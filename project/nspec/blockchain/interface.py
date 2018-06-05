from flask import Flask, jsonify, request
from project.utils import *
import json
from project.nspec.blockchain.modelBC import m_Blocks
from project.classes import c_blockchainNode
# this is the dummy function only, your function comes from the import!
from project.pclass import c_peer
from project.nspec.blockchain.verify import *
from project.nspec.blockchain.balance import *


firstCall = True
class chainInterface:

    def nodeSpecificGETNow(self,url,linkInfo):
        urlID = url[1:6]
        #TODO ensure for all who have no parameter in URL hat linkoinfo is empty!
        if (urlID == 'block'):
            if (linkInfo == {}):
                return jsonify(m_Blocks),200
            else:
                return c_blockchainNode.c_blockchainHandler.getJSONBlockByNumber((int) (linkInfo['blockNumber']))

        elif (urlID == "minin"):
            if (len(linkInfo) ==1):
                return c_blockchainNode.getMinerCandidate(linkInfo['minerAddress'])

        elif (urlID == "trans"):
            if (len(linkInfo) == 1):
                return c_blockchainNode.c_tx.getTXForHash(linkInfo['TXHash'])
            else:
                if (url == "/transactions/confirmed"):
                    return setOK(c_blockchainNode.c_tx.getConfirmedTXByHash(""))
                if (url == "/transactions/pending"):
                    return c_blockchainNode.c_tx.getPendingTX("")
        elif (urlID == "addre"):
            if ("transactions" in url):
                return c_blockchainNode.c_tx.getTXForAddress(linkInfo['address'])
            else:
                if ("balance" in url):
                    return getBalance(linkInfo['address'])
        elif (urlID == "balan"):
            return getAllBalances()
        elif (urlID == "load/"):
            c_blockchainNode.c_blockchainHandler.initChain()
            with open(linkInfo["file"], "r") as myFile:
                sysIn = json.load(myFile)
            c_blockchainNode.loadSys(sysIn)

            response = {
                'message': 'system loaded from: ' + str(linkInfo["file"]),
                'date': datetime.datetime.now().isoformat(),
            }
            return jsonify(response), 200
        elif (urlID == "save/"):
            sysout = c_blockchainNode.bufferSys()
            text_file = open(linkInfo["file"], "w")
            text_file.write(json.dumps(sysout, indent=2, sort_keys=True))
            text_file.close()

            response = {
                'message': 'system saved to: ' + str(linkInfo["file"]),
                'date': datetime.datetime.now().isoformat(),
            }
            return jsonify(response), 200

        # identify your url and then proceed
        #linkInfo is a json object containing the information from the URL
        response = {
            'NodeType': m_cfg['type'],
            'info': "This API is not yet implemented....",
            'requestedUrl': url,
            'linkInfo': linkInfo
        }
        ## put your logic here and create the reply as next line
        return errMsg(response), 400

    # this is the dummy function only, your functoin comes from the import!
    def nodeSpecificPOSTNow(self,url,linkInfo,json,request):
        # linkInfo is a json object containing the information from the URL
        urlID = url[1:6]
        if (urlID == "trans"):
            return receivedNewTransaction(json, request.url_root, True)

        if (urlID == "peers") and (url == "/peers/notify-new-block"):
            return c_blockchainNode.c_blockchainHandler.receivedBlockNotificationFromPeer(json)

        if (urlID == "minin"):
            return c_blockchainNode.minerFoundSolution(json)

        #json contains the json object submitted during the POST
        response = {
            'NodeType': m_cfg['type'],
            'info': "This API is not yet implemented...."
        }
        ## put your logic here and create the reply as next line
        return jsonify(response), 400