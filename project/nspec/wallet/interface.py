from project.utils import *
from project.classes import c_walletInterface
from project.models import m_info
from project.nspec.wallet.modelW import m_db

# put your distribution according to url
class walletInterface:
    def nodeSpecificGETNow(self, url, linkInfo):
        urlID = url[1:5]
        if (urlID == 'send'):
            return send()
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
                return c_walletInterface.getAllWallets(linkInfo['user'])
            elif (url.startswith("/wallet/list/keys/s")):
                return c_walletInterface.getAllKeys(linkInfo)
            elif (url.startswith("/wallet/list/balance")):
                return c_walletInterface.getKeyBalance(linkInfo)
            elif (url.startswith("/wallet/list/allbalances")):
                return c_walletInterface.getAllBalance(linkInfo)
            elif (url.startswith("/wallet/list/allbalance")):
                return c_walletInterface.getWalletBalance(linkInfo)
            elif (url.startswith("/wallet/list/allkeybalance")):
                return c_walletInterface.getWalletKeyBalance(linkInfo)
            elif (url.startswith("/wallet/list/allTXs/")):
                return c_walletInterface.getAllTX(linkInfo)
            elif (url.startswith("/wallet/list/allTX/")):
                return c_walletInterface.getWalletTX(linkInfo)

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
        return jsonify(response), 400

    # this is the dummy function only, your functoin comes from the import!
    def nodeSpecificPOSTNow(self, url, linkInfo, json, request):
        # linkInfo is a json object containing the information from the URL
        urlID = url[1:7]
        if (url == "/"):
            return form_post(request)

        if (urlID == 'wallet'):
            if (url.startswith("/wallet/transfer")):
                return c_walletInterface.payment(json)
            elif (url.startswith("/wallet/createKey")):
                return c_walletInterface.createKeys(json)
            elif (url.startswith("/wallet/create")):
                return c_walletInterface.createWallet(json)

        #json contains the json object submitted during the POST
        response = {
            'NodeType': m_info['type'],
            'info': "This API is not (yet) implemented...."
        }
        ## put your logic here and create the reply as next line
        return jsonify(response), 400