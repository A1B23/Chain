from project.utils import checkRequiredFields, isABCNode, setOK, errMsg, isBCNode
from threading import Thread
from project.models import m_cfg, m_peerSkip, m_Delay, m_visualCFG, m_info, m_peerInfo
from project.nspec.blockchain.modelBC import m_Blocks #, m_peerToBlock
from copy import deepcopy
from time import sleep
import random
import requests, json
from urllib.parse import urlparse
import project.classes


#TODO
#To avoid double-connecting to the same peer
#First get /info and check the nodeId
#Never connect twice to the same nodeId
#connecting to peer synchronise with block and pending transactions slide60
#After successful connection to a peer, try to synchronize the chain (if the peer has better chain) + synchronize the pending transactions
#Extra: implement functionality to delete lost peers
#If a peer is contacted and it does not respond, delete it from the connected peers
#If /info does not return the correct peerId
#It is invalid or does not respond -> delete it
#You may run this check once per minute or when you send a notification about a new block

class peers:

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


    def doGET(self, url):
        parsed_uri = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        # if domain + "cfg" == url:
        #     peerOffer = {
        #         "peerUrl": m_info['nodeUrl']
        #     }
        #     self.asynchPOST("peers/connect", peerOffer, " ")
        self.visualDelay(self.makeDelay(url, {}, False))
        return requests.get(url=url, headers={'accept': 'application/json'})

    def asPost(self, type, url, json, cnt):
        for peer in self.randomOrderFor(m_cfg[type]):
            #if (peer == skipPeer):
            #    continue
            if m_cfg[type][peer]['active'] is True:
                try:
                    print("asynch: " + peer + url + str(json))
                    if self.makeDelay(peer + url, json, True) <= 0:
                        self.doPOST(peer + url, json)
                    cnt = cnt + 1
                    if cnt > m_cfg['minPeers']: #TODO stop sending when min reached, do more?
                        break
                except Exception:
                    m_cfg[type][peer]['numberFail'] = m_cfg[type][peer]['numberFail'] + 1

        return cnt


    def asynchPOST(self, url, json, skipPeer):
        if url[0] != "/":
            url = "/"+url
        cnt = self.asPost('activePeers', url, json, 0)
        if cnt < m_cfg['minPeers']:
            self.asPost('shareToPeers', url, json, cnt)
        #print("Succeed to send asynch to: "+str(cnt))


    def sendAsynchPOSTToPeers(self,url,json,skipPeer):
        thread = Thread(target=self.asynchPOST, args=(url, json, skipPeer))
        #TODO after some time, clear this buffer, maybe as part of checking peers availability?
        #TODO or alternatively by the size/len of it???
        #TODO cut the buffer short if POST is too long???
        m_peerSkip.append({"url": url, "json": json})
        thread.start()

    def hasActivePeers(self):
        for peer in m_cfg['activePeers']:
            if m_cfg['activePeers'][peer]['active'] is True:
                return True
        return False


    def postPeers(self, list, url, json, cnt):
        response = []
        # TODO taken ranofm if more than minPeers
        for peer in self.randomOrderFor(m_cfg[list]):
            if m_cfg[list][peer]['active'] is True:
                try:
                    #print("Peer: Share new info with " + url)
                    ret = self.doPOST(url=peer + url, json=json)
                    response.append(ret)
                    cnt = cnt + 1
                    m_cfg[list][peer]['active'] = True
                    if cnt > m_cfg['minPeers']:  # TODO stop sending when min reached, do more?
                        break
                except Exception:
                    m_cfg[list][peer]['numberFail'] = m_cfg[list][peer]['numberFail'] + 1
        return response

    def sendPOSTToPeers(self, url, json):
        m_peerSkip.append({"url": url, "json": json})
        response = []
        if url[0] != "/":
            url = "/"+url
        response.append(self.postPeers('activePeers', url, json, 0))
        if (len(response) < m_cfg['minPeers']) or (len(response[0]) == 0):
            response.append(self.postPeers('shareToPeers', url, json, len(response)))
        return response

    def randomOrderFor(self, dict):
        dest = [*dict]
        random.shuffle(dest)
        return dest

    def sendGETToPeerToAnyone(self, peer, url):
        #note peer comes with slash at the end, peerx does not have, url does not have
        #this rountine mostly handls incoming requst from unknown nodes
        #so we try to get informatin first from known nodes, but we may
        #see later if we want to connect to the newbie
        if peer in m_cfg['activePeers']:
            try:
                resp = self.sendGETToPeer(peer+url)
                txt, code = resp
                if code == 200:
                    return resp
            except Exception:
                i=0

        for peerx in self.randomOrderFor(m_cfg['activePeers']):
            try:
                resp = self.sendGETToPeer(peerx+"/"+url)
                txt, code = resp
                if code == 200:
                    return resp
            except Exception:
                i=0

        for peerx in self.randomOrderFor(m_cfg['shareToPeers']):
            try:
                resp = self.sendGETToPeer(peerx+"/"+url)
                txt, code = resp
                if code == 200:
                    return resp
            except Exception:
                i=0

        try:
            resp = self.sendGETToPeer(peer + url)
            txt, code = resp
            if code == 200:
                peer = peer[0:-1]
                #have not seen this peer before, so we may connect later
                if peer not in m_cfg['peerOption']:
                    m_cfg['peerOption'][peer] = deepcopy(m_peerInfo)
                    m_cfg['peerOption'][peer]['source'] = peer
            return resp
        except Exception:
            return ("{'noDelivery':True}", 400)


    def sendGETToPeer(self, url):
        #This routine must not have try/except as except is signal to caller
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
        response = []
        cnt = 0
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

    # def deActivate(self, peer):
    #     if m_cfg['peers'][peer]['numberFail'] > m_cfg['peerDrop']:
    #         print("Peer " + peer + " not responding " + str(m_cfg['peers'][peer]['numberFail']) + " times, de-activated...")
    #         m_cfg['peers'][peer]['active'] = False
    #         return True
    #     return False

    # def discoverPeers(self, needed):
    #     findPeer = []
    #     for peer in m_cfg['peers']:
    #         if m_cfg['peers'][peer]['active'] is True:
    #             try:
    #                 s1 = self.doGET(peer + "/peers")
    #             except Exception:
    #                 m_cfg['peers'][peer]['active'] = False
    #                 continue
    #             reply = json.loads(s1.text)
    #             for nodeId in reply:
    #                 found = False
    #                 for peer2 in m_cfg['peers']:
    #                     if nodeId == m_cfg['peers'][peer2]['nodeId']:
    #                         found = True
    #                         break
    #                 if found is False:
    #                     findPeer.append(reply[nodeId])
    #                     needed = needed - 1
    #                     break
    #
    #             if needed <= 0:
    #                 break   # do not just take all peers from one peer
    #                 # to avoid peer aggregation, rather try another peer
    #                 # to see if that one connects to another, even if it
    #                 # means the lower boundary is off for a few more rounds
    #     for peer in findPeer:
    #         self.addPeer(peer, True)

    def ensureBCNode(self, type):
        # peers can actually only be BCNode, all else make no sense
        if isABCNode(type):
            return True
        return False


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
        except Exception:
            return False
        return True

    def checkPeerAliveAndValid(self, peer):
        reply = self.suitableReply(peer)
        if len(reply) == 0:
            return False
        # if self.isPeerAliveAndValid(peer, reply) is True:
        #     if ('blocksCount' in reply) and (reply['blocksCount'] > len(m_Blocks)):
        #         base = peer
        #         if base[-1] != "/":
        #             base = base + "/"
        #         base = base + "blocks/"
        #         m_cfg['missingBlock'] = {base, peer}
        #     return True
        # return False
        return self.isPeerAliveAndValid(peer, reply)

    def addPeer(self, url, addCheck):
        #TODO when node receives packet form peer and is lacking peers, why is the sender not taken in?
        pos = url.index("//")
        try:
            pos = url.index("/", pos+2)
            url = url[0:pos]
        except Exception:
            pos=-1

        for x in m_cfg['peers']:
            if url.startswith(x):
                return False
        if url not in m_cfg['peers']:
            # TODO this may need to be made more sophisticated, same url without http is still a loop
            if url != m_info['nodeUrl']:
                m_cfg['peers'][url] = deepcopy(m_peerInfo)
                m_info['peers'] = len(m_cfg['peers'])
                reply = self.suitableReply(url)
                if len(reply) == 0:
                    return False
                valid = ((not addCheck) or self.isPeerAliveAndValid(url, reply))
                return valid
        return False


    def registerPotentialPeer(self, nodes, port,source="startup"):
        for x in nodes.split(','):
            if len(x) > 0:
                newNode=""
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

                if (len(newNode) > 0) and (newNode != m_info['nodeId']) and (not newNode in m_cfg['peerOption']):
                    m_cfg['peerOption'][newNode] = deepcopy(m_peerInfo)
                    m_cfg['peerOption'][newNode]['source'] = source


    def suitablePeer(self, peer, nodeId):
        try:
            #TODO if we got peer recommended, check that is it the same nodeId
            s1 = self.doGET(peer + "/info")
            reply = json.loads(s1.text)
            m, l, f = checkRequiredFields(reply, m_info, ["chainId", "about"], False)
            if (len(f) > 0) or (len(m) > 0):  # we skip to check any additional fields, is that OK
                print("Peer " + peer + " reply not accepted, considered not alive")
                # as it is invalid peer, don't try again
                m_cfg['peers'][peer]['wrongType'] = m_cfg['peers'][peer]['wrongType'] + 1
                del m_cfg['peers'][peer]
                m_info['peers'] = len(m_cfg['peers'])
                return {'wrongChain': True}

            # if nodeId != "startup":
            #     if nodeId != reply['nodeId']:
            #         #TODO do we want to keep this srtict link?? wallet restart???
            #         return {'wrongID': True}
            if not self.ensureBCNode(reply['type']):
                return {'wrongType': True}
            if isBCNode():
                if reply['blocksCount'] > len(m_Blocks):
                    #m_peerToBlock['addBlock'] = peer
                    threadp = Thread(target=project.classes.c_blockchainNode.c_blockchainHandler.getMissingBlocksFromPeer(), args=(peer,))
                    threadp.start()
            return reply
        except Exception:
            return {'fail': True}

    def checkAvailability(self, type, ref):
        remOption = []
        for peer in self.randomOrderFor(m_cfg[type]):
            if peer in m_cfg['peerAvoid']:
                remOption.append(peer)
                continue
            cnt = 0
            for peerx in m_cfg['activePeers']:
                if peerx['active'] is True:
                    cnt = cnt + 1
            if cnt > m_cfg[ref]:
                break
            try:
                reply = self.suitablePeer(peer, m_cfg[type][peer]['source'])
            except Exception:
                reply = {'fail': True}
            if ("wrongType" in reply) or ("wrongID" in reply) or ("fail" in reply) or ("wrongChain" in reply): #not suitable or no reply
                #give five chances, as it was supposed to be correct as per recommendation and some small error
                m_cfg[type][peer]['wrongType'] = m_cfg[type][peer]['wrongType'] + 1
                if ("fail" not in reply) and m_cfg[type][peer]['wrongType'] > m_cfg['maxWrong']:
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
                continue

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

        return remOption


    def manageType(self, type, ref, isActive):
        cnt = 0
        for peer in m_cfg['activePeers']:
            if peer['active'] is True:
                cnt = cnt + 1
        if cnt >= m_cfg['maxPeers']:
            return True

        if (isActive is True) and (cnt >= m_cfg['minPeers']):
            return True

        remOption = self.checkAvailability(type, ref)
        for peer in remOption:
            if peer in m_cfg[type]:
                del m_cfg[type][peer]

        cnt = 0
        for peer in m_cfg['activePeers']:
            if peer['active'] is True:
                cnt = cnt + 1

        if cnt >= m_cfg['maxPeers']:
            return True

        if (isActive is True) and (cnt >= m_cfg['minPeers']):
            return True

        return False

    def upgradeShareToActive(self):
        #TODO ask for the per list and if we are peer of the other, upgrade to activePeers
        return

    def ensurePeerNumber(self, isActive, ref):
        if isActive is True:
            if self.manageType("activePeers", ref, isActive) is True:
                return
            if self.manageType("shareToPeers", ref, isActive) is True:
                return
            self.upgradeShareToActive()
        self.manageType("peerOption", ref, isActive)

        if isActive is True:
            if (len(m_cfg['peerOption']) > 0) and (ref != 'maxPeers'):
                threadp = Thread(target=self.ensurePeerNumber, args=(False, 'maxPeers'))
                threadp.start()
                return

        m_cfg['statusPeer'] = False

    #this is a thread running every x seconds to check peers are still there
    def checkEveryXSecs(self):
        m_cfg['statusPeer'] = False
        while m_cfg['shutdown'] is False:
            if "statusChain" not in m_cfg:
                m_cfg['statusChain'] = False       # backward compatibility
            while m_cfg['statusChain']:
                sleep(1)
            while m_cfg['statusPeer']:
                sleep(1)
            m_cfg['statusPeer'] = True
            self.ensurePeerNumber(True, "minPeers")
            sleep(m_cfg['peersCheckDelay']) #TODO adjust to 60 after testing, controlled by 'peersCheck' in config


    # TODO newNode set too late and several vars not used??
    def peersConnect(self, path, linkInfo, values, request):
        try:
            values = request.get_json()
        except Exception:
            return errMsg("JSON not decodeable")
        #check = json.loads(values)
        m, l, f = checkRequiredFields(['peerUrl'], values, [], False)
        if len(m) > 0:
            return errMsg("Missing field 'peerUrl': " + str(values))
        newNode = values['peerUrl']
        peers = m_cfg['peers']
        for k in peers:
            if newNode == k:
                return errMsg("Already connected to peer: " + newNode, 409)
        if self.addPeer(newNode, False):
            if self.checkPeerAliveAndValid(newNode) is False:
                del m_cfg['peers'][newNode]
                return errMsg("Invalid or not connected peer/chain: " + newNode)
            return setOK('Connected to peer: '+newNode)
        return errMsg("Invalid peer/chain/recursion: " + newNode)

    def listPeers(self):
        response = {}
        for peer in m_cfg['activePeers']:
            response.update({m_cfg['activePeers'][peer]['nodeId']: peer})
        for peer in m_cfg['shareToPeers']:
            response.update({m_cfg['shareToPeers'][peer]['nodeId']: peer})
        return setOK(response)
