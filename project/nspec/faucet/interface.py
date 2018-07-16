from project.utils import errMsg, setOK
from project.classes import c_faucetInterface
from project.models import m_info
from project.nspec.wallet.modelW import m_db


class faucetInterface:
    def nodeSpecificGETNow(self, url, linkInfo):
        urlID = url[1:5]
        #if (urlID == 'send'):
        #    return send()
        if (urlID == 'info'):
            infow = {
                'about': m_info['about'],
                'database': m_db['DATABASE'],
                'chainID': m_info['chainId'],
                'nodeUrl': m_info['nodeUrl'],
                'nodeId': m_info['nodeId']
            }
            return setOK(infow)

        if urlID == 'wall':
            if (url.startswith("/wallet/list/wallet")):
                return c_faucetInterface.getAllWallets(linkInfo['user'])
            elif (url.startswith("/wallet/list/keys/s")):
                return c_faucetInterface.getAllKeys(linkInfo)
            elif (url.startswith("/wallet/list/balance")):
                return c_faucetInterface.getKeyBalance(linkInfo)
            elif (url.startswith("/wallet/list/allbalances")):
                return c_faucetInterface.getAllBalance(linkInfo)
            elif (url.startswith("/wallet/list/allbalance")):
                return c_faucetInterface.getWalletBalance(linkInfo)
            elif (url.startswith("/wallet/list/allkeybalance")):
                return c_faucetInterface.getWalletKeyBalance(linkInfo)
            elif (url.startswith("/wallet/list/allTXs/")):
                return c_faucetInterface.getAllTX(linkInfo)
            elif (url.startswith("/wallet/list/allTX/")):
                return c_faucetInterface.getWalletTX(linkInfo)

        if (urlID == 'addr'):
            return setOK(linkInfo)

            #return send()
        # identify your url and then proceed
        #linkInfo is a json object containing the information from the URL
        response = {
            'NodeType': m_info['type'],
            'info': "This API is not yet implemented....",
            'requestedUrl': url,
            'linkInfo': linkInfo
        }
        ## put your logic here and create the reply as next line
        return errMsg(response)


    def nodeSpecificPOSTNow(self, url, linkInfo, json, request):
        # linkInfo is a json object containing the information from the URL
        urlID = url[1:7]
        #if (url == "/"):
        #    return form_post(request)

        if (urlID == 'wallet'):
            if (url.startswith("/wallet/transfer")):
                return c_faucetInterface.payment(json)
            elif (url.startswith("/wallet/createKey")):
                return c_faucetInterface.createKeys(json)
            elif (url.startswith("/wallet/create")):
                return c_faucetInterface.createWallet(json)

        #json contains the json object submitted during the POST
        response = {
            'NodeType': m_info['type'],
            'info': "This API is not (yet) implemented...."
        }
        ## put your logic here and create the reply as next line
        return errMsg(response)