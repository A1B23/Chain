from project.utils import checkRequiredFields, isABCNode, setOK, errMsg, isBCNode, d
from threading import Thread
from project.models import m_cfg, m_peerSkip, m_Delay, m_visualCFG, m_info, m_peerInfo
from project.nspec.blockchain.modelBC import m_Blocks
from copy import deepcopy
from time import sleep
import random
import requests
import json
from urllib.parse import urlparse
import project.classes


class peers:
    skipDoubleCheck = []
    #TODO when we receive info etc. from an unknonw node and outr count is below needd
    # then why does the peer list not take it as new node???
    def makeDelay(self, url, json, isAsyncPost):
        if m_cfg['canTrack'] is True:
            if (m_visualCFG['active'] is True) and (m_visualCFG['pattern'].search(url)):
                id = random.randint(1, 1000000)
                m_Delay.append({"delayID": id, "url": url, "json": json, "asynchPOST": isAsyncPost})
                return id
        return -1

    def visualDelay(self, myDelay):
        if (myDelay > 0) and (m_visualCFG['active'] is True):
            try:
                maxCount = 12  # delay at most x seconds in total then move on, but keep the buffer anyway
                while (maxCount > 0) and (len(m_Delay) > 0):
                    for item in m_Delay:
                        if 'delayID' in item:
                            if item['delayID'] == myDelay:
                                sleep(1)
                                maxCount = maxCount - 1
                                break
                        if 'releaseID' in item:
                            if item['releaseID'] == myDelay:
                                sleep(1)
                                maxCount = maxCount - 1
                                break

            except Exception:  # means no ,m_Delay
                myDelay = -1

    def doPOST(self, url, json):
        self.visualDelay(self.makeDelay(url, json, False))
        return requests.post(url=url, json=json, headers={'accept': 'application/json'})

    def doGET(self, url,fastTrack=False):
        #normal is used to skip visual to get maxPeers, but show for minPeers!
        parsed_uri = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}{uri.path}'.format(uri=parsed_uri)
        if fastTrack is False:
            self.visualDelay(self.makeDelay(domain, {}, False))
        return requests.get(url=domain, headers={'accept': 'application/json'})

    def asPost(self, type, url, jsonx, cnt):
        for peer in self.randomOrderFor(m_cfg[type]):
            if m_cfg[type][peer]['active'] is True:
                try:
                    d("asynch: " + peer + url + str(jsonx))
                    self.doPOST(peer + url, jsonx)
                    cnt = cnt + 1
                    if cnt > m_cfg['minPeers']: # TODO do  more?
                        break
                except Exception:
                    m_cfg[type][peer]['numberFail'] = m_cfg[type][peer]['numberFail'] + 1

        return cnt

    def asynchPOST(self, url, jsonx):
        if url[0] != "/":
            url = "/"+url
        cnt = self.asPost('activePeers', url, jsonx, 0)
        if cnt < m_cfg['minPeers']:
            self.asPost('shareToPeers', url, jsonx, cnt)

    def sendAsynchPOSTToPeers(self, url, jsonx):
        thread = Thread(target=self.asynchPOST, args=(url, jsonx))
        #TODO after some time, clear this buffer, maybe as part of checking peers availability?
        #TODO or alternatively by the size/len of it???
        #TODO cut the buffer short if POST is too long???
        m_peerSkip.append({"url": url, "json": jsonx})
        thread.start()

    def postPeers(self, list, url, jsonx, cnt):
        response = []
        for peer in self.randomOrderFor(m_cfg[list]):
            if m_cfg[list][peer]['active'] is True:
                try:
                    ret = self.doPOST(url=peer + url, json=jsonx)
                    response.append(ret)
                    cnt = cnt + 1
                    m_cfg[list][peer]['active'] = True
                    if cnt > m_cfg['minPeers']:  # TODO do more?
                        break
                except Exception:
                    m_cfg[list][peer]['numberFail'] = m_cfg[list][peer]['numberFail'] + 1
        return response

    def sendPOSTToPeers(self, url, jsonx):
        m_peerSkip.append({"url": url, "json": jsonx})
        response = []
        if url[0] != "/":
            url = "/"+url
        response.append(self.postPeers('activePeers', url, jsonx, 0))
        if (len(response) < m_cfg['minPeers']) or (len(response[0]) == 0):
            response.append(self.postPeers('shareToPeers', url, jsonx, len(response)))
        return response

    def randomOrderFor(self, dictx):
        dest = [*dictx]
        random.shuffle(dest)
        return dest

    def sendGETToPeerToAnyone(self, peer, url):
        # note peer comes with slash at the end, peer does not have, url does not have
        # this routine mostly handle incoming request from unknown nodes
        # so we try to get information first from known nodes, but we may
        # see later if we want to connect to the newbie
        print("trying to request "+url+ " from peer "+peer)
        if peer in m_cfg['activePeers']:
            try:
                print("try peer directly")
                resp = self.sendGETToPeer(peer+url)
                txt, code = resp
                if code == 200:
                    print("got peer directly")
                    return resp
            except Exception:
                i=0

        for peerx in self.randomOrderFor(m_cfg['activePeers']):
            try:
                print("try random peer from active "+peerx)
                resp = self.sendGETToPeer(peerx+"/"+url)
                txt, code = resp
                if code == 200:
                    print("got peer directly")
                    return resp
            except Exception:
                i=0

        for peerx in self.randomOrderFor(m_cfg['shareToPeers']):
            try:
                print("try random peer from share "+peerx)
                resp = self.sendGETToPeer(peerx+"/"+url)
                txt, code = resp
                if code == 200:
                    print("got peer directly")
                    return resp
            except Exception:
                i=0

        try:
            print("last try unconfirmed source itself " + peer)
            resp = self.sendGETToPeer(peer + url)
            txt, code = resp
            if code == 200:
                print("got directly from unconfirmed source")
                peer = peer[0:-1]
                # have not seen this peer before, so we may connect later
                if peer not in m_cfg['peerOption']:
                    m_cfg['peerOption'][peer] = deepcopy(m_peerInfo)
                    m_cfg['peerOption'][peer]['source'] = peer
            print("Done")
            return resp
        except Exception:
            return ("{'noDelivery':True}", 400)

    def sendGETToPeer(self, url):
        # This routine must not have try/except as except is signal to caller
        rep = self.doGET(url=url)
        dat = json.loads(rep.text)
        x = rep.status_code
        return dat, x

    def getPeers(self, type, url, cnt):
        response = []
        for peer in self.randomOrderFor(m_cfg[type]):
            if m_cfg[type][peer]['active'] is True:
                try:
                    response.append(self.sendGETToPeer(url=peer+url))
                    cnt = cnt + 1
                    if cnt >= m_cfg['minPeers']:
                        break
                except Exception:
                    m_cfg[type][peer]['numberFail'] = m_cfg[type][peer]['numberFail'] + 1
        return response

    def sendGETToPeers(self, url):
        #TODO check if we still need and if it works
        #TODO taken ranofm if more than minPeers
        if (url[0] != "/"):
            url = "/" + url

        resp = self.getPeers('activePeers', url, 0)
        if len(resp) == 0:
            response = self.getPeers('shareToPeers', url, 0)
        else:
            response = resp
            if len(resp) < m_cfg['minPeers']:
                for tx in (self.getPeers('shareToPeers', url, len(resp))):
                    response.append[tx]
        return response

    def ensureBCNode(self, type):
        # peers can actually only be BCNode, all else make no sense
        return isABCNode(type)

    def isPeerAliveAndValid(self, peer, reply):
        try:
            if peer in m_cfg['peers']:
                if m_cfg['peers'][peer]['nodeId'] != "Pending...":
                    if m_cfg['peers'][peer]['nodeId'] != reply['nodeId']:
                        m_cfg['peers'][peer]['active'] = False
                        return False
                    m_cfg['peers'][peer]['active'] = True
                    return True
            m_cfg['peers'][peer]['nodeId'] = reply['nodeId']
            m_cfg['peers'][peer]['active'] = True
            return True
        except Exception:
            return False

    def checkPeerAliveAndValid(self, peer):
        reply = self.suitableReply(peer)
        if len(reply) == 0:
            return False
        return self.isPeerAliveAndValid(peer, reply)

    # def addPeer(self, url, addCheck):
    #     #TODO when node receives packet form peer and is lacking peers, why is the sender not taken in?
    #     pos = url.index("//")
    #     try:
    #         pos = url.index("/", pos+2)
    #         url = url[0:pos]
    #     except Exception:
    #         pos=-1
    #
    #     for x in m_cfg['peers']:
    #         if url.startswith(x):
    #             return False
    #     if url not in m_cfg['peers']:
    #         # TODO this may need to be made more sophisticated, same url without http is still a loop
    #         if url != m_info['nodeUrl']:
    #             m_cfg['peers'][url] = deepcopy(m_peerInfo)
    #             m_info['peers'] = len(m_cfg['peers'])
    #             #TODO doe snot exist anymore, is this routine called at all
    #             reply = self.suitableReply(url)
    #             if len(reply) == 0:
    #                 return False
    #             valid = ((not addCheck) or self.isPeerAliveAndValid(url, reply))
    #             return valid
    #     return False

    def registerPotentialPeer(self, nodes, port,source="startup"):
        for x in nodes.split(','):
            if len(x) > 0:
                newNode=""
                #type = 'shareToPeers'
                if len(x) < 4:
                    try:
                        xint = int(x.strip())
                        if (xint > 0) and (xint < 256):
                            newNode = "http://127.0.0."+str(xint)+":"+str(port)
                        else:
                            print("WAR: IP extension not recognised: '" + x + "'")
                    except Exception:
                        print("ERR: Invalid connection parameter: '" + x + "'")
                else:
                    newNode = x


                #TODO add type parameter later as startup has more prio??
                print("Supposed to connect to "+newNode)
                err = self.addPeerOption(newNode, source, 'peerOption')
                if len(err) > 0:
                    print("Failed to register peer: " + err)
                    return ""
        ks = next(iter(m_cfg['peerOption'].keys()))
        return ks

    def addPeerOption(self, newURL, source, dest="peerOption"):
        try:
            result = urlparse(newURL)
            newURL = result.scheme+"://"+result.netloc
        except Exception:
            return "Invalid url structure"

        if (newURL != m_info['nodeId']) and (newURL not in m_cfg['peerOption']):
            if (newURL in m_cfg['activePeers']) or (newURL in m_cfg['shareToPeers']):
                return "Already connected to peer: " + newURL
            m_cfg[dest][newURL] = deepcopy(m_peerInfo)
            m_cfg[dest][newURL]['source'] = source
            return ""
        return "Already connecting to peer: " + newURL

    def suitablePeer(self, peer, fastTrack=False):
        try:
            s1 = self.doGET(peer + "/info", fastTrack)
            reply = json.loads(s1.text)
            m, l, f = checkRequiredFields(reply, m_info, ["chainId", "about"], False)
            if (len(f) > 0) or (len(m) > 0):  # we skip to check any additional fields, is that OK
                print("Peer " + peer + " reply not accepted, considered not alive")
                # as it is invalid peer, don't try again
                m_cfg['peers'][peer]['wrongType'] = m_cfg['peers'][peer]['wrongType'] + 1
                del m_cfg['peers'][peer]
                m_info['peers'] = len(m_cfg['peers'])
                return {'wrongChain': True}

            if peer != reply['nodeUrl']:
                return {'Inconsistency in nodeURL': True}

            if not self.ensureBCNode(reply['type']):
                return {'wrongType': True}

            if isBCNode():
                if m_cfg['chainLoaded'] is True:
                    if (reply['blocksCount'] > len(m_Blocks)) or (reply['blockHash'] != m_Blocks[-1]['blockHash']):
                        # ignore the return data from the situational check as here is primarily peer
                        # and informing the blockmanager about potential peers is secondary here
                        d("info showed longer block or different hash:" +str(reply['blocksCount']) +" "+ str(len(m_Blocks)) +" "+ reply['blockHash'] +" "+m_Blocks[-1]['blockHash'])
                        project.classes.c_blockchainNode.c_blockchainHandler.checkChainSituation('info', reply)
                    if reply['blocksCount'] < len(m_Blocks):
                        # we found a laggard, let him know we are further
                        project.classes.c_blockchainNode.c_blockchainHandler.asynchNotifyPeers()
            return reply
        except Exception:
            return {'fail': True}

    def available(self, peer, type, fastTrack=False):
        remOption = []
        retry = []
        try:
            reply = self.suitablePeer(peer, fastTrack)
        except Exception:
            reply = {'fail': True}
        if ("wrongType" in reply) or ("wrongID" in reply) or ("fail" in reply) or ("wrongChain" in reply):  # not suitable or no reply
            # give five chances, as it was supposed to be correct as per recommendation and some small error
            m_cfg[type][peer]['wrongType'] = m_cfg[type][peer]['wrongType'] + 1
            if "fail" not in reply:
                if m_cfg[type][peer]['wrongType'] > m_cfg['maxWrong']:
                    remOption.append(peer)
                    m_cfg['peerAvoid'].append(peer)
                    if peer in m_cfg['activePeers']:
                        del m_cfg['activePeers'][peer]
                    if peer in m_cfg['shareToPeers']:
                        del m_cfg['shareToPeers'][peer]
                if (type != 'activePeers') and (peer in m_cfg['activePeers']):
                    m_cfg['activePeers'][peer]['active'] = False
                if (type != 'shareToPeers') and (peer in m_cfg['shareToPeers']):
                    m_cfg['shareToPeers'][peer]['active'] = False
            else:
                retry.append(peer)
            return retry, remOption

        if peer not in m_cfg['shareToPeers']:
            if peer not in m_cfg['activePeers']:
                m_cfg['shareToPeers'][peer] = deepcopy(m_peerInfo)
                m_cfg['shareToPeers'][peer]['active'] = True
                m_cfg['shareToPeers'][peer]['nodeId'] = reply['nodeId']
                remOption.append(peer)
            else:
                m_cfg['activePeers'][peer]['active'] = True
        else:
            m_cfg['shareToPeers'][peer]['active'] = True

        # double check prevents asking the same node twice for nin and then max
        # but only in case we got reply, fo none reply we try again
        if peer not in retry:
            self.skipDoubleCheck.append(peer)
        return retry, remOption

    def tryToAchieveMaxPeerActiveUsing(self, type, minOrMax):
        remOption = []
        retry = []
        for peer in self.randomOrderFor(m_cfg[type]):
            if peer in m_cfg['peerAvoid']:
                remOption.append(peer)
                continue
            cnt = self.cntPeers('activePeers')
            if cnt > m_cfg[minOrMax]:
                return

            #double check prevents asking the same node twice for nin and then max
            if peer not in self.skipDoubleCheck:
                retr, remO = self.available(peer, type, minOrMax == 'maxPeers')
                retry.extend(retr)
                remOption.extend(remO)

        if len(retry) > 0:
            for rets in range(1, 3):
                sleep(1)
                for peer in retry:
                    if peer in m_cfg['peerAvoid']:
                        remOption.append(peer)
                        continue
                    cnt = self.cntPeers('activePeers')
                    if cnt > m_cfg[minOrMax]:
                        for peer in remOption:
                            if peer in m_cfg[type]:
                                del m_cfg[type][peer]
                        return
                    retr, remO = self.available(peer, type, minOrMax == 'maxPeers')
                    remOption.extend(remO)
        for peer in remOption:
            if peer in m_cfg[type]:
                del m_cfg[type][peer]
        return

    def cntPeers(self,type):
        cnt = 0
        for peer in m_cfg[type]:
            if m_cfg[type][peer]['active'] is True:
                cnt = cnt + 1
        return cnt


    def manageType(self, type, minOrMax):
        cnt = self.cntPeers('activePeers')
        isMin = minOrMax.startswith("min")
        if cnt >= m_cfg['maxPeers']:
            return True

        if (isMin is True) and (cnt >= m_cfg['minPeers']):
            return True

        self.tryToAchieveMaxPeerActiveUsing(type, minOrMax)

        cnt = self.cntPeers('activePeers')

        if cnt >= m_cfg['maxPeers']:
            return True

        if (isMin is True) and (cnt >= m_cfg['minPeers']):
            return True

        return False

    def upgradeShareToActive(self):
        #TODO ask for the per list and if we are peer of the other, upgrade to activePeers
        return

    def ensurePeerNumber(self, minOrMax):
        if minOrMax.startswith("min"):
            if self.manageType("activePeers", minOrMax) is True:
                return
            if self.manageType("shareToPeers", minOrMax) is True:
                return
            self.upgradeShareToActive()
        self.manageType("peerOption", minOrMax)


    #this is a thread running every x seconds to check peers are still there
    def checkEveryXSecs(self):
        m_cfg['checkingPeers'] = False
        while m_cfg['shutdown'] is False:
            try:
                self.skipDoubleCheck.clear()
                while m_cfg['chainInit'] is True or m_cfg['checkingChain'] is True:
                    sleep(1)
                if m_cfg['checkingPeers'] is False:
                    m_cfg['checkingPeers'] = True
                    self.ensurePeerNumber("minPeers")
                    self.ensurePeerNumber("maxPeers")
                    m_cfg['checkingPeers'] = False
            except Exception:
                i=0

            slp = m_cfg['peersCheckDelay']+random.randint(0, 10)-5
            cnt = self.cntPeers('activePeers') + self.cntPeers("shareToPeers")
            if cnt == 0:
                slp = 5
            elif cnt < m_cfg['maxPeers']:
                slp =int(slp/2)

            sleep(slp) #TODO adjust to 60 after testing, controlled by 'peersCheck' in config

    def peersConnect(self, source, values):
        m, l, f = checkRequiredFields(['peerUrl'], values, [], False)
        if len(m) > 0:
            return errMsg("Missing field 'peerUrl' ")
        err = self.addPeerOption(values['peerUrl'], source)
        if len(err) == 0:
            return setOK("Connection to peer registered")
        if err.startswith("Already connected"):
            return errMsg("Already connected to peer: " + values['peerUrl'], 409)
        return errMsg(err)

    def listPeers(self):
        response = {}
        for peer in m_cfg['activePeers']:
            response.update({m_cfg['activePeers'][peer]['nodeId']: peer})
        for peer in m_cfg['shareToPeers']:
            response.update({m_cfg['shareToPeers'][peer]['nodeId']: peer})
        return setOK(response)
