from project import app, render_template
from flask import Flask, jsonify, request
import datetime, requests
from project.models import *
from project.nspec.blockchain.modelBC import *
from project.utils import *
import json
from project.InterfaceLocking import mainInterface
from project.classes import c_blockchainNode, c_walletInterface
from project.pclass import c_peer
from copy import deepcopy

c_MainIntf = mainInterface()

@app.route('/visual')
def visual():
    dat = []
    if (len(m_Delay)>0):
        dat = m_Delay.pop(0)
    return jsonify(dat), 200


@app.route('/cfg')
def get_cfg():
    return jsonify(m_cfg), 200

### TODO remove after debugging
@app.route('/load/<file>')
def loadSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/save/<file>')
def saveSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /info
@app.route('/info')
def get_info():
    return info()

#GET /debug
@app.route('/debug')
def debug():
    response = []
    response.extend(m_cfg)
    response.extend(m_info)
    response.extend(m_pendingTX)
    response.extend(m_BufferMinerCandidates)

    return jsonify(response), 200

#GET /debug/reset-chain
@app.route('/debug/reset-chain')
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
@app.route('/blocks')
def blocks():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /blocks/{number}
@app.route('/blocks/<number>')
def blocks_getByNumber(number):
    linkInfo = {"blockNumber": number}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/pending
@app.route('/transactions/pending')
def transactions_pending():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/confirmed
@app.route('/transactions/confirmed')
def transactions_confirmed():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /transactions/{TXHash}
@app.route('/transactions/<TXHash>')
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
@app.route('/balances')
def balances():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /address/{address}/transactions
@app.route('/address/<address>/transactions')
def address_transaction(address):
    linkInfo = {"address": address}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

#GET /address/{address}/balance
@app.route('/address/<address>/balance')
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
@app.route('/peers')
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
@app.route('/mining/get-mining-job/<minerAddress>')
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
@app.route('/debug/mine/<minerAddress>/<difficulty>')
def debug_mining(minerAddress, difficulty):
    linkInfo = {"address": minerAddress, "difficulty": difficulty}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


#This table shows Flask’s built-in URL converters.
#string 	Accepts any text without a slash (the default).
#int 	Accepts integers.
#float 	Like int but for floating point values.
#path 	Like string but accepts slashes.



@app.route("/",methods=['POST', 'GET'])
def index():
    if (isBCNode()):
        return render_template("indexBC.html")
    if (isWallet()):
        if request.method == 'POST':
            return c_walletInterface.form_post(request)
        return render_template("TabWallet.html")

    response = {
        'NodeType': m_cfg['type'],
        'info': "This URL/API is not available"
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

@app.route('/wallet/list/wallet')
def getWallets():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/wallet/list/keys/<param>/<wallet>', methods=['GET'])
def getKeyInfo(param,wallet):
    linkInfo = {"sel": param, "wallet": wallet}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


################## the following two are only for testing while developing peer module
@app.route("/listNodes")
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

    oldNodes = setNode(python_obj['node'], m_info['nodeURL'])
    for oldNode in oldNodes:
        if oldNode in m_cfg['nodes']:
            m_cfg['nodes'].remove(oldNode)

    return jsonify(m_cfg), 200