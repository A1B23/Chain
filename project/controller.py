from project import app, render_template
from flask import request
from project.nspec.blockchain.modelBC import *
from project.utils import *
import json
from project.InterfaceLocking import mainInterface
from project.classes import c_blockchainNode
from project.pclass import c_peer
from copy import deepcopy
from project.models import m_cfg, m_visualCFG
import re

c_MainIntf = mainInterface()


@app.route('/visualGet', methods=["GET"])
def visualGet():
    dat = {}
    for item in m_Delay:
        if 'delayID' in item:
            dat = deepcopy(item)
            item['releaseID'] = dat['delayID']
            del item['delayID']
            break
    return jsonify(dat), 200

@app.route('/visualRelease/<int:id>', methods=["GET"])
def visualRelease(id):
    for item in m_Delay:
        if ('releaseID' in item) and (item['releaseID'] == id):
            rel = item
            break
    m_Delay.remove(rel)
    return jsonify(rel), 200


@app.route('/visualCfg', methods=["POST"])
def visualCfg():
    try:
        values = request.get_json()
        if (values['active'] is True):
            pattern = re.compile(values['pattern'])
            m_visualCFG['active'] = True
            m_visualCFG['pattern'] = pattern
            return setOK(values)
        m_visualCFG['active'] = False
        m_Delay.clear()
        return setOK("Tracking switched off")
    except Exception:
        return errMsg("JSON not decodeable or missing item", 400)


@app.route('/cfg', methods=["GET"])
def get_cfg():
    return jsonify(m_cfg), 200

### TODO remove after debugging
@app.route('/load/<file>', methods=["GET"])
def loadSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/save/<file>', methods=["GET"])
def saveSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /info
@app.route('/info', methods=["GET"])
def get_info():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /debug
@app.route('/debug', methods=["GET"])
def debug():
    response = []
    response.append(m_cfg)
    response.append(m_info)
    response.append(m_pendingTX)
    response.append(m_BufferMinerCandidates)

    return jsonify(response), 200

#GET /debug/reset-chain
@app.route('/debug/reset-chain', methods=["GET"])
def debug_resetChain():
    ## this is a very special case, as it is not GET but actually a POST issue
    m_isPOST.append("Reset Chain")
    while (len(m_isPOST)>1):
        if (c_MainIntf.delay("reset-chain",999) == False):
            break   #for some reason we decide to ignore the lock
    ret = c_blockchainNode.c_blockchainHandler.resetChainReply()
    m_isPOST.clear()
    return ret

#GET /blocks
@app.route('/blocks', methods=["GET"])
def blocks():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /blocks/{number}
@app.route('/blocks/<int:number>', methods=["GET"])
def blocks_getByNumber(number):
    linkInfo = {"blockNumber": number}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/pending
@app.route('/transactions/pending', methods=["GET"])
def transactions_pending():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/confirmed
@app.route('/transactions/confirmed', methods=["GET"])
def transactions_confirmed():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/{TXHash}
@app.route('/transactions/<TXHash>', methods=["GET"])
def transactions_hash(TXHash):
    linkInfo = {"TXHash": TXHash}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#POST /transactions/send
@app.route('/transactions/send', methods=['POST'])
def transactions_send():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

#GET /balances
@app.route('/balances', methods=["GET"])
def balances():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /address/{address}/transactions
@app.route('/address/<address>/transactions', methods=["GET"])
def address_transaction(address):
    linkInfo = {"address": address}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /address/{address}/balance
@app.route('/address/<address>/balance, methods=["GET"]')
def address_balance(address):
    linkInfo = {"address": address}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#POST /peers/notify-new-block
@app.route('/peers/notify-new-block', methods=['POST'])
def peers_notifyNewBlock():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

#GET /peers
@app.route('/peers', methods=["GET"])
def peers():
    return c_peer.listPeers()

#POST /peers/connect
@app.route('/peers/connect', methods=['POST'])
# this is invoked by user to tell me that the other node exists at IP
def peers_connect():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_peer.peersConnect(request.path, linkInfo, values, request)

#GET /mining/get-mining-job/{miner-address}
@app.route('/mining/get-mining-job/<minerAddress>', methods=["GET"])
def mining_getMiningJob(minerAddress):
    linkInfo = {"minerAddress": minerAddress}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#POST /mining/submit-mined-block
@app.route('/mining/submit-mined-block', methods=['POST'])
def mining_submitBlock():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

#GET /debug/mine/{minerAddress}/{difficulty}
@app.route('/debug/mine/<minerAddress>/<int:difficulty>', methods=["GET"])
def debug_mining(minerAddress, difficulty):
    linkInfo = {"address": minerAddress, "difficulty": difficulty}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


#This table shows Flask’s built-in URL converters.
#string 	Accepts any text without a slash (the default).
#int 	Accepts integers.
#float 	Like int but for floating point values.
#path 	Like string but accepts slashes.


@app.route("/", methods=['GET'])
def index():
    addOn = ""
    if m_cfg['debug'] == True:
        addOn = "_debug"

    if (isBCNode()):
        return render_template("indexBC" + addOn + ".html")
    if (isWallet()):
        return render_template("TabWallet" + addOn + ".html")

    response = {
        'NodeType': m_cfg['type'],
        'info': "Requested URL/API is not available"
     }
    return jsonify(response), 400

################## Wallet specific routes
@app.route('/wallet/create', methods=['POST'])
def wallet_create():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

@app.route('/wallet/createKey', methods=['POST'])
def wallet_createKey():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

@app.route('/wallet/transfer', methods=['POST'])
def wallet_transfer():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable", 400)
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

@app.route('/wallet/list/wallet/<user>', methods=["GET"])
def getWallets(user):
    linkInfo = {'user': user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/wallet/list/keys/<param>/<wallet>/<user>', methods=['GET'])
def getKeyInfo(param, wallet, user):
    linkInfo = {"sel": param, "wallet": wallet,
                'user': user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/wallet/list/balance/<param>/<wallet>/<key>/<user>', methods=['GET'])
def getKeyBalance(param, wallet, key, user):
    linkInfo = {"sel": param, "wallet": wallet, "key": key, "user": user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/wallet/list/allbalances/<user>', methods=['GET'])
def getAllBalances(user):
    linkInfo = {"user": user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/wallet/list/allbalance/<wallet>/<user>', methods=['GET'])
def getWalletBalance(wallet, user):
    linkInfo = {"wallet": wallet, "user": user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/wallet/list/allkeybalance/<wallet>/<user>', methods=['GET'])
def getWalletKeyBalance(wallet, user):
    linkInfo = {"wallet": wallet, "user": user}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/wallet/list/allTXs/<type>/<user>', methods=['GET'])
def getAllTX(type, user):
    linkInfo = {"user": user, "type": type}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/wallet/list/allTX/<type>/<wallet>/<user>', methods=['GET'])
def getWalletTx(type, wallet, user):
    linkInfo = {"wallet": wallet, "user": user, "type": type}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


################## the following two are only for testing while developing peer module
@app.route("/listNodes", methods=["GET"])
def listNodes():
    return jsonify(m_cfg['peers']), 200

@app.route("/clrNode", methods=['POST'])
def clrNode():
    values = request.get_json()

    #Check that the required fields are in the POST'ed data.
    required = ['node']
    python_obj = json.loads(values)
    for k in required:
        if not (k in python_obj):
            return 'Invalid param', 400

    #TODO what was clrNode and setNode() doing?
    oldNodes = setNode(python_obj['node'], m_info['nodeURL'])
    for oldNode in oldNodes:
        if oldNode in m_cfg['nodes']:
            m_cfg['nodes'].remove(oldNode)

    return jsonify(m_cfg), 200