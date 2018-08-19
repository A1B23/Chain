from project.utils import isBCNode, isWallet, isGenesis, isFaucet, checkRequiredFields, errMsg, setOK, d
from project.nspec.blockchain.interface import chainInterface
from project.nspec.wallet.interface import walletInterface
from project.nspec.faucet.interface import faucetInterface
from project.nspec.genesis.interface import genesisInterface
from project.models import m_permittedPOST, m_permittedGET, m_cfg, m_simpleLock, m_isPOST, m_peerSkip, m_info
from time import sleep
import re


class mainInterface:
    c_blockInterface = chainInterface()
    c_walletInterface = walletInterface()
    c_faucetInterface = faucetInterface()
    c_genesisInterface = genesisInterface()

    def delay(self, url, type):
        # sleep a second or a loop etc
        print("....................Delay needed for: "+url + " type: "+str(type) + " stackGET: " + str(len(m_simpleLock)) + " stackPOST: " + str(len(m_isPOST)))
        sleep(1)
        return True

    def permittedURLPOST(self, url):
        for test in m_permittedPOST:
            if re.match(test, url):
                return True
        return False

    def permittedURLGET(self, url):
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
            'NodeType': m_info['type'],
            'info': "This URL/API is not available/broken"
        }
        try:
            if self.permittedURLGET(url) is False:
                return errMsg("This URL/API is invalid or not available. " + url)
            if "chainInit" not in m_cfg:
                m_cfg['chainInit'] = False    # backward compatible
            maxWait = 15
            while (len(m_isPOST) > 0) or (m_cfg['chainInit'] is True):
                if url == "/info":  # this is needed for peers to cross reference each other
                    break
                if self.delay(url, 1) is False:
                    break   # for some reason we decide to ignore the lock
                maxWait = maxWait - 1
                if maxWait < 0:
                    print("Console maxwait for chain update reached, just go ahead now ....")
                    break

            m_simpleLock.append(url)
            if isBCNode():
                ret = self.c_blockInterface.nodeSpecificGETNow(url, linkInfo)
            elif isWallet():
                ret = self.c_walletInterface.nodeSpecificGETNow(url, linkInfo)
            elif isFaucet():
                ret = self.c_faucetInterface.nodeSpecificGETNow(url, linkInfo)
            elif isGenesis():
                ret = self.c_genesisInterface.nodeSpecificGETNow(url, linkInfo)
        except Exception:
            print("Oops, GET exception happened ....")

        if url in m_simpleLock:
            m_simpleLock.remove(url)  # maybe need to check for being there, then need to add random to URL
        return ret

    def nodeSpecificPOST(self,url, linkInfo, json,request):
        ret = {
            'NodeType': m_info['type'],
            'info': "This URL/API is not available/broken"
        }

        try:
            for x in json:
                if not re.match("[0-9a-zA-Z]+", x):
                    return errMsg("Invalid JSON key: " + str(x))
                if isinstance(json[x], str):
                    if not re.match("[0-9a-zA-Z \.%!@#$\-_+=;:,/?<>]*", json[x]):
                        return errMsg("Invalid character in JSON data: "+str(x))
                elif isinstance(json[x], list):
                    for xx in json[x]:
                        if isinstance(xx, str):
                            if not re.match("[0-9a-zA-Z \.%!@#$\-_+=;:,/?<>]*", xx):
                                return errMsg("Invalid character in JSON data: " + str(xx))
                elif not isinstance(json[x], int):
                    return errMsg("Invalid character in JSON data: " + str(json[x]))

            # This is only applicable to POST, and is a shortcut to stop endless broadcast
            # of the same message
            for urlJson in m_peerSkip:
                if urlJson['url'] == url:
                    m, l, f = checkRequiredFields(json, urlJson['json'], urlJson['json'], True)
                    if len(m) + len(f) == 0:
                        #TODO what text here?
                        return setOK("Acknowledge... ")
            # TODO for bigger network, make this bigger as well?
            if len(m_peerSkip) > 10:
                del m_peerSkip[0]

            if self.permittedURLPOST(url) is False:
                return errMsg("This URL/API is invalid or not available. " + url)

            d("Add delay url: '"+url +"' before we had "+str(len(m_isPOST)))
            m_isPOST.append(url)

            while (len(m_isPOST) > 1) or (m_cfg['chainInit'] is True):
                if self.delay(url, 2) is False:
                    break   # for some reason we decide to ignore the loop
            while len(m_simpleLock) > 0:
                if self.delay(url, 3) is False:
                    break   # for some reason we decide to ignore the loop

            if isBCNode():
                ret = self.c_blockInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
            elif isWallet():
                ret = self.c_walletInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
            elif isFaucet():
                ret = self.c_faucetInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
            elif isGenesis():
                ret = self.c_genesisInterface.nodeSpecificPOSTNow(url, linkInfo, json, request)
        except Exception:
            d("*********************************************")
            d("*********************************************")
            print("POST exception caught, isPoststack "+str(len(m_isPOST)))
            m_isPOST.clear()
            d("*********************************************")
            d("*********************************************")

        if url in m_isPOST:
            m_isPOST.remove(url)
            d("Removed delay url: '" + url + "' back to " + str(len(m_isPOST)))
        return ret
