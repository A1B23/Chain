from project.utils import checkRequiredFields, isABCNode, setOK, errMsg, isBCNode, d, getValidURL
from threading import Thread
from project.models import m_cfg, m_peerSkip, m_Delay, m_visualCFG, m_info, m_peerInfo
from project.nspec.blockchain.modelBC import m_Blocks
from copy import deepcopy
from time import sleep
import random
import requests
import json
import project.classes


class peers:
    skipDoubleCheck = []

    def makeDelay(self, url, json, isAsyncPost):
        try:
            if m_cfg['canTrack'] is True:
                if m_visualCFG['active'] is True:
                    urlc= url
                    if url.startswith("http"):
                        urlc = url[url.index("//")+3:]
                    if m_visualCFG['pattern'].search(urlc):
                        id = random.randint(100, 10000000)
                        m_Delay.append({"delayID": id, "url": url, "json": json, "asynchPOST": isAsyncPost})
                        return id
        except Exception:
            i=0
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

    def doPOST(self, url, data):
        self.visualDelay(self.makeDelay(url, data, False))
        return requests.post(url=url, json=data, headers={'accept': 'application/json'})

    def doGET(self, url, fastTrack=False):
        #normal is used to skip visual to get maxPeers, but show for minPeers!
        # at this point we have to assume the url is corrcet syntax
        #parsed_uri = urlparse(url)
        domain = getValidURL(url, False)
        if fastTrack is False:
            self.visualDelay(self.makeDelay(domain, {}, False))
        return requests.get(url=domain, headers={'accept': 'application/json'})


    def asAsynchPost(self, ptype, url, data, cnt):
        for peer in self.randomOrderFor(m_cfg[ptype]):
            if m_cfg[ptype][peer]['active'] is True:
                try:
                    d("asynch: " + peer + url + str(data))
                    self.doPOST(peer + url, data)
                    cnt = cnt + 1
                    if cnt > m_cfg['minPeers']:
                        break
                except Exception:
                    m_cfg[ptype][peer]['numberFail'] = m_cfg[ptype][peer]['numberFail'] + 1

        return cnt

    def asynchPOST(self, url, data):
        if url[0] != "/":
            url = "/"+url
        sent = self.asAsynchPost('activePeers', url, data, 0)
        if sent < m_cfg['minPeers']:
            self.asAsynchPost('shareToPeers', url, data, sent)

    def sendAsynchPOSTToPeers(self, url, data):
        thread = Thread(target=self.asynchPOST, args=(url, data))
        #TODO after some time, clear this buffer, maybe as part of checking peers availability?
        #TODO or alternatively by the size/len of it???
        #TODO cut the buffer short if POST is too long???
        m_peerSkip.append({"url": url, "json": data})
        thread.start()

    def postPeers(self, useList, url, data, cnt):
        response = []
        for peer in self.randomOrderFor(m_cfg[useList]):
            if m_cfg[useList][peer]['active'] is True:
                try:
                    ret = self.doPOST(peer + url, data)
                    response.append(ret)
                    cnt = cnt + 1
                    m_cfg[useList][peer]['active'] = True
                    if cnt > m_cfg['minPeers']:  # TODO do more?
                        break
                except Exception:
                    m_cfg[useList][peer]['numberFail'] = m_cfg[useList][peer]['numberFail'] + 1
        return response

    def sendPOSTToPeers(self, url, data):
        m_peerSkip.append({"url": url, "json": data})
        response = []
        if url[0] != "/":
            url = "/"+url
        response.append(self.postPeers('activePeers', url, data, 0))
        if (len(response) < m_cfg['minPeers']) or (len(response[0]) == 0):
            response.append(self.postPeers('shareToPeers', url, data, len(response)))
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
        x = rep.status_code
        if x == 500:
            dat = {"ErrMessagePeer": "Failed peer attempt using"+url}
        else:
            dat = json.loads(rep.text)
        return dat, x

    def getPeers(self, peerType, url, cnt):
        response = []
        for peer in self.randomOrderFor(m_cfg[peerType]):
            if m_cfg[peerType][peer]['active'] is True:
                try:
                    response.append(self.sendGETToPeer(url=peer+url))
                    cnt = cnt + 1
                    if cnt >= m_cfg['minPeers']:
                        break
                except Exception:
                    m_cfg[peerType][peer]['numberFail'] = m_cfg[peerType][peer]['numberFail'] + 1
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
                for tx in self.getPeers('shareToPeers', url, len(resp)):
                    response.append(tx)
        return response

    def ensureBCNode(self, peerType):
        # peers can actually only be BCNode, all else make no sense
        return isABCNode(peerType)

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

    def registerPotentialPeer(self, nodes, port, source="startup"):
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

                print("Supposed to connect to "+newNode)
                err = self.addPeerOption(newNode, source, 'peerOption')
                if len(err) > 0:
                    print("Failed to register peer: " + err)
                    return ""
        ks = next(iter(m_cfg['peerOption'].keys()))
        return ks

    def addPeerOption(self, newInURL, source, dest="peerOption"):
        newURL = getValidURL(newInURL, True)
        if newURL == "":
            return "Invalid URL: "+newInURL

        if (newURL != m_info['nodeId']) and (newURL not in m_cfg['peerOption']):
            if (newURL in m_cfg['activePeers']) or (newURL in m_cfg['shareToPeers']):
                return "Already connected to peer: " + newURL
            m_cfg[dest][newURL] = deepcopy(m_peerInfo)
            m_cfg[dest][newURL]['source'] = source
            return ""
        return "Already connecting to peer: " + newURL

    def removePeerOption(self, newInURL):
        newURL = getValidURL(newInURL, True)
        if newURL == "":
            return "Invalid URL: "+newInURL

        if newURL != m_info['nodeId']:
            ret = "Not connected/registered anyway"
            if newURL in m_cfg['peerOption']:
                del m_cfg['peerOption'][newURL]
                ret = ""
            if newURL in m_cfg['activePeers']:
                del m_cfg['activePeers'][newURL]
                ret = ""
            if newURL in m_cfg['shareToPeers']:
                del m_cfg['shareToPeers'][newURL]
                ret = ""
            return ret
        return "No self connection anyway: " + newURL

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

    def available(self, peer, peerType, fastTrack=False):
        remOption = []
        retry = []
        try:
            reply = self.suitablePeer(peer, fastTrack)
        except Exception:
            reply = {'fail': True}
        if ("wrongType" in reply) or ("wrongID" in reply) or ("fail" in reply) or ("wrongChain" in reply):  # not suitable or no reply
            # give five chances, as it was supposed to be correct as per recommendation and some small error
            m_cfg[peerType][peer]['wrongType'] = m_cfg[peerType][peer]['wrongType'] + 1
            if "fail" not in reply:
                if m_cfg[peerType][peer]['wrongType'] > m_cfg['maxWrong']:
                    remOption.append(peer)
                    m_cfg['peerAvoid'].append(peer)
                    if peer in m_cfg['activePeers']:
                        del m_cfg['activePeers'][peer]
                    if peer in m_cfg['shareToPeers']:
                        del m_cfg['shareToPeers'][peer]
                if (peerType != 'activePeers') and (peer in m_cfg['activePeers']):
                    m_cfg['activePeers'][peer]['active'] = False
                if (peerType != 'shareToPeers') and (peer in m_cfg['shareToPeers']):
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

    def tryToAchieveMaxPeerActiveUsing(self, peerType, minOrMax):
        remOption = []
        retry = []
        for peer in self.randomOrderFor(m_cfg[peerType]):
            if peer in m_cfg['peerAvoid']:
                remOption.append(peer)
                continue
            cnt = self.cntPeers('activePeers')
            if cnt > m_cfg[minOrMax]:
                return

            #double check prevents asking the same node twice for nin and then max
            if peer not in self.skipDoubleCheck:
                retr, remO = self.available(peer, peerType, minOrMax == 'maxPeers')
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
                            if peer in m_cfg[peerType]:
                                del m_cfg[peerType][peer]
                        return
                    retr, remO = self.available(peer, peerType, minOrMax == 'maxPeers')
                    remOption.extend(remO)
        for peer in remOption:
            if peer in m_cfg[peerType]:
                del m_cfg[peerType][peer]
        return

    def cntPeers(self, peerType):
        cnt = 0
        for peer in m_cfg[peerType]:
            if m_cfg[peerType][peer]['active'] is True:
                cnt = cnt + 1
        return cnt


    def manageType(self, peerType, minOrMax):
        cnt = self.cntPeers('activePeers')
        isMin = minOrMax.startswith("min")
        if cnt >= m_cfg['maxPeers']:
            return True

        if (isMin is True) and (cnt >= m_cfg['minPeers']):
            return True

        self.tryToAchieveMaxPeerActiveUsing(peerType, minOrMax)

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

            #time to sleep untilk next peer check depends on current situation
            slp = m_cfg['peersCheckDelay']+random.randint(0, 10)-5
            cnt = self.cntPeers('activePeers') + self.cntPeers("shareToPeers")
            if cnt == 0:
                slp = 5
            elif cnt < m_cfg['maxPeers']:
                slp =int(slp/2)

            sleep(slp)

    def peersConnect(self, source, values, isConnect):
        m, l, f = checkRequiredFields(['peerUrl'], values, [], False)
        if len(m) > 0:
            return errMsg("Missing field 'peerUrl' ")
        url = values['peerUrl']
        newURL = getValidURL(url, True)
        if newURL == "":
            return errMsg("Invalid URL: "+url)

        if isConnect:
            err = self.addPeerOption(url, source)
            if len(err) == 0:
                return setOK("Connection to peer registered")
            if err.startswith("Already connected"):
                return errMsg("Already connected to peer: " + url, 409)
        else:
            err = self.removePeerOption(url)
            if len(err) == 0:
                return setOK("Connection to peer removed")

        return errMsg(err)

    def listPeers(self):
        response = {}
        for peer in m_cfg['activePeers']:
            response.update({m_cfg['activePeers'][peer]['nodeId']: peer})
        for peer in m_cfg['shareToPeers']:
            response.update({m_cfg['shareToPeers'][peer]['nodeId']: peer})
        return setOK(response)
