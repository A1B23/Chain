from project.utils import isBCNode, isMiner, isWallet, checkRequiredFields
from project.nspec.blockchain.interface import chainInterface
from project.nspec.wallet.interface import walletInterface
from project.models import *
from time import sleep
import re
from flask import jsonify

class mainInterface:
    c_blockInterface = chainInterface()
    c_walletInterface = walletInterface()

    def delay(self,url,type):
        #sleep a seconds or a loop etc
        print("Delay needed for: "+url + " type: "+str(type)+ " stackGET: "+str(len(m_simpleLock))+ " stackPOST: "+str(len(m_isPOST)))
        sleep(1)
        return True

    def permittedURLPOST(self, url):
        for test in m_permittedPOST:
            if re.match(test, url):
                return True
        return False


    def permittedURLGET(self,url):
        for test in m_permittedGET:
            if re.match(test, url):
                return True
        return False

    #POST is critical to all info, so we give it priority (we need to assume we have to implement
    # something to protect DOS-attack on POSTs to stop any GET later on)
    # A POST pauses all subsequent POST and GET til it is completed to avoid data inconsistency
    # A delay in response for the pending queries is acceptable, packets always get lost in internet :-)
    def nodeSpecificGET(self, url, linkInfo):
        ret = {
            'NodeType': m_cfg['type'],
            'info': "This URL/API is not available/broken"
        }
        try:
            if (not self.permittedURLGET(url)):
                response = {
                    'errMsg': "This URL/API is invalid or not available. " + url
                }
                return jsonify(response), 400
            if (not "statusChain" in m_cfg):
                m_cfg['statusChain'] = False    #backward compatible
            while ((len(m_isPOST)>0) or (m_cfg['statusChain']==True)):
                if (self.delay(url,1) == False):
                    break   #for some reason we decide to ignore the lock

            m_simpleLock.append(url)
            #TODO remove test sleep
            #sleep(3)
            if (isBCNode()):
                ret = self.c_blockInterface.nodeSpecificGETNow(url, linkInfo)
            elif (isWallet()):
                ret = self.c_walletInterface.nodeSpecificGETNow(url, linkInfo)
        except Exception:
            print("Oops, GET exception happened ....")

        if (url in m_simpleLock):
            m_simpleLock.remove(url) #maybe need to check for being there, then need to add random to URL
        return ret


    def nodeSpecificPOST(self,url, linkInfo, json,request):
        ret = {
            'NodeType': m_cfg['type'],
            'info': "This URL/API is not available/broken"
        }

        try:
            # This is only applicable to POST, and is a shortcut to stop endless broadcast
            # of the same message
            for urlJson in m_peerSkip:
                if (urlJson['url'] == url):
                    m, l, f = checkRequiredFields(json, urlJson['json'], urlJson['json'],True)
                    if ((len(m)==0) and (len(f)==0)):
                        response = {
                            'message': "Acknowledge... "
                        }
                        return jsonify(response), 200
            # TODO for bigger network, make this bigger as well?
            if (len(m_peerSkip) > 10):
                del m_peerSkip[0]

            if (not self.permittedURLPOST(url)):
                response = {
                    'errMsg': "This URL/API is invalid or not available. " + url
                }
                return jsonify(response), 400
            m_isPOST.append(url)

            while ((len(m_isPOST)>1) or (m_cfg['statusChain']==True)):
                if (self.delay(url,2) == False):
                    break   #for some reason we decide to ignore the loop
            while (len(m_simpleLock)>0):
                if (self.delay(url,3) == False):
                    break   #for some reason we decide to ignore the loop

            if (isBCNode()):
                ret = self.c_blockInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
            elif (isWallet()):
                ret = self.c_walletInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
            #sleep is for test only to see POST locking works!!!
            #sleep(10)
        except Exception:
            print("POST exception caught")

        if (url in m_isPOST):
            m_isPOST.remove(url) #maybe need to check for being there, then need to add random to URL
        return ret