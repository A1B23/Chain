from project.models import *
from project.utils import *
from threading import Thread
from project.models import m_cfg, m_peerSkip, m_Delay
from project.utils import checkRequiredFields
from flask import jsonify
from copy import deepcopy
from time import sleep

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

cntDelay = [0]
class peers:
    def doPOST(self, url, json):
        if (m_cfg['useDelay'] == True):
            myDelay = cntDelay[0]
            m_Delay.append({"delay": myDelay, "url": url, "json": json})
            cntDelay[0] = cntDelay[0] + 1
            try:
                while (m_Delay[0]['delay'] == myDelay):
                    sleep(1)
            except Exception: #means no ,m_Delay
                myDelay=-1
        return requests.post(url=url, json=json)

    def doGET(self, url):
        if (m_cfg['useDelay'] == True):
            myDelay = cntDelay[0]
            m_Delay.append({"delay": myDelay, "url": url})
            cntDelay[0] = cntDelay[0] + 1
            try:
                while (m_Delay[0]['delay'] == myDelay):
                    sleep(1)
            except Exception: #means no ,m_Delay
                myDelay=-1
        #return requests.get(url=url)
        return requests.get(url=url, headers={'accept': 'application/json'})

    def asynchPOST(self, url, json, skipPeer):
        cnt=0
        if (url[0] != "/"):
            url = "/"+url
        print("Current asynch list: "+str(m_cfg['peers']))
        for peer in m_cfg['peers']:
            #if (peer == skipPeer):
            #    continue
            if (m_cfg['peers'][peer]['active']):
                try:
                    print("sending asynch " + peer + url + str(json))
                    self.doPOST(url=peer + url, json=json)
                    cnt = cnt + 1
                    m_cfg['peers'][peer]['active'] = True
                    if (cnt> m_cfg['minPeers']): #TODO stop sending when min reached, do more?
                        break
                except Exception:
                    m_cfg['peers'][peer]['numberFail'] = m_cfg['peers'][peer]['numberFail'] + 1


    def sendAsynchPOSTToPeers(self,url,json,skipPeer):
        thread = Thread(target=self.asynchPOST, args=(url, json, skipPeer))
        #TODO after some time, clear this buffer, maybe as part of checking peers availability?
        #TODO or alternatively by the size/len of it???
        #TODO cut the buffer short if POST is too long???
        m_peerSkip.append({"url":url,"json":json})
        thread.start()

    def hasActivePeers(self):
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active']):
                return True
        return False

    def sendPOSTToPeers(self, url, json):
        m_peerSkip.append({"url": url, "json": json})
        response = []
        cnt = 0
        if (url[0] != "/"):
            url = "/"+url
        forceSend = not self.hasActivePeers()
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active']) or forceSend:
                try:
                    print("Peer: Share new info with "+url + ", force: "+str(forceSend))
                    ret = self.doPOST(url=peer+url, json=json)
                    response.append(ret)
                    cnt = cnt+1
                    m_cfg['peers'][peer]['active'] = True
                    if (cnt> m_cfg['minPeers']): #TODO stop sending when min reached, do more?
                        break
                except Exception:
                    if (not forceSend):
                        m_cfg['peers'][peer]['numberFail'] = m_cfg['peers'][peer]['numberFail'] + 1
        return response

    def sendGETToPeer(self, url):
        #This routine must not have try/except as except is signal to caller
        rep = self.doGET(url=url)
        dat = json.loads(rep.text)
        x = rep.status_code
        self.addPeer(url, False)
        return dat, x

    def sendGETToPeers(self, url):
        #TODO check if we still need and if it works
        response = []
        cnt = 0
        if (url[0] != "/"):
            url = "/" + url
        forceSend = not self.hasActivePeers()
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active'] or forceSend):
                try:
                    response.append(self.sendGETToPeer(url=peer+url))
                    cnt = cnt + 1
                    if (cnt >= m_cfg['minPeers']):
                        break
                except Exception:
                    if (not forceSend):
                        m_cfg['peers'][peer]['numberFail'] = m_cfg['peers'][peer]['numberFail'] + 1
        return response

    def deActivate(self, peer):
        if (m_cfg['peers'][peer]['numberFail'] > m_cfg['peerDrop']):
            print("Peer " + peer + " not responding " + str(m_cfg['peers'][peer]['numberFail']) + " times, de-activated...")
            m_cfg['peers'][peer]['active'] = False
            return True
        return False

    def discoverPeers(self, needed):
        findPeer = []
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active'] == True):
                try:
                    s1 = self.doGET(peer + "/peers")
                except Exception:
                    m_cfg['peers'][peer]['active'] = False
                    continue
                reply = json.loads(s1.text)
                for nodeId in reply:
                    found = False
                    for peer2 in m_cfg['peers']:
                        if nodeId == m_cfg['peers'][peer2]['nodeId']:
                            found = True
                            break
                    if (not found):
                        findPeer.append(reply[nodeId])
                        needed = needed - 1
                        break

                if (needed <= 0):
                    break   # do not just take all peers from one peer
                    # to avoid peer aggregation, rather try another peer
                    # to see if that one connects to another, even if it
                    # means the lower boundary is off for a few more rounds
        for peer in findPeer:
            self.addPeer(peer, True)


    def checkPeerAliveAndValid(self, peer):
        try:
            s1 = self.doGET(peer+"/info")
            reply = json.loads(s1.text)
            m, l, f = checkRequiredFields(reply, m_info, ["chainId", "about"],False)
            if (len(f) > 0) or (len(m) > 0): #we skip to check any additoinal fields, is that OK
                print("Peer " + peer + " reply not accepted, considered not alive")
                m_cfg['peers'][peer]['numberFail'] = m_cfg['peerDrop'] + 1
                return False
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

    def addPeer(self, url, addCheck):
        for x in m_cfg['peers']:
            if (url.startswith(x)):
                return False
        if url not in m_cfg['peers']:
            # TODO this may need to be made more sophisticated, same url without http is still a loop
            if url != m_info['nodeUrl']:
                m_cfg['peers'][url] = deepcopy(m_peerInfo)
                m_info['peers'] = len(m_cfg['peers'])
                return ((not addCheck) or self.checkPeerAliveAndValid(url))
        return False


    def setPeersAs(self, nodes, port):
        for x in nodes.split(','):
            if len(x) > 0:
                if (len(x) < 4):
                    try:
                        xint = int(x.strip())
                        if (xint > 0) and (xint < 256):
                            newNode = "http://127.0.0."+str(xint)+":"+str(port)
                            self.addPeer(newNode, True)
                        else:
                            print("WAR: IP extension not recognised: '" + x + "'")
                    except Exception:
                        print("ERR: Invalid connection parameter: '" + x + "'")
                else:
                    self.addPeer(x, True)


    #this is a thread running every x seconds to check peers are still there
    def checkEveryXSecs(self, sleepSecs):
        while True:
            if(not "statusChain" in m_cfg):
                m_cfg['statusChain'] = False       # backward compatibility
            while(m_cfg['statusChain'] == True):
                sleep(1)
            m_cfg['statusPeer'] = True
            cntActive= 0
            for peer in m_cfg['peers']:
                if (cntActive > m_cfg['minPeers']):
                    break
                if (self.checkPeerAliveAndValid(peer) == False):
                    m_cfg['peers'][peer]['numberFail'] = m_cfg['peers'][peer]['numberFail'] + 1
                    self.deActivate(peer)
                else:
                    cntActive = cntActive+1
                    m_cfg['peers'][peer]['numberFail'] = 0
            # add here any other regular checks, so that we have only 1 thread
            if (cntActive < m_cfg['minPeers']):
                self.discoverPeers(m_cfg['minPeers']-cntActive)
            #to avoid DOS attack or memory overflow on peerlist, clear when to many are dead and kept
            rem = []
            clr = len(m_cfg['peers']) - 10*m_cfg['maxPeers']
            while (clr>0):
                found = False
                for peer in m_cfg['peers']:
                    if (peer['active'] == False):
                        rem.append(peer)
                        clr = clr - 1
                        found = True
                if (found == False):
                    break
            for peer in rem:
                del m_cfg['peers'][peer]
            m_cfg['statusPeer'] = False
            sleep(sleepSecs) #TODO adjust to 60 after testing

    # TODO newNode set too late and several vars not used??
    def peersConnect(self, path, linkInfo, values, request):
        try:
            values = request.get_json()
        except Exception:
            return errMsg("JSON not decodeable", 400)
        #check = json.loads(values)
        m, l, f = checkRequiredFields(['peerUrl'], values, [], False)
        if (len(m) > 0):
            return errMsg("Missing field 'peerUrl': " + newNode, 400)
        newNode = values['peerUrl']
        peers = m_cfg['peers']
        for k in peers:
            if newNode == k:
                return errMsg("Already connected to peer: " + newNode, 409)
        if self.addPeer(newNode, False):
            if self.checkPeerAliveAndValid(newNode) == False:
                del m_cfg['peers'][newNode]
                return errMsg("Invalid or not connected peer/chain: " + newNode, 400)
            return setOK({'message': 'Connected to peer: '+newNode})
        return errMsg("Invalid peer/chain/recursion: " + newNode, 400)

    def listPeers(self):
        response = {}
        for peer in m_cfg['peers']:
            response.update({m_cfg['peers'][peer]['nodeId']: peer})
        return setOK(response)
