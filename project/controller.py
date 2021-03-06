from project import app, render_template
from flask import request
from project.utils import setOK, errMsg, isBCNode, isWallet, isGenesis, isFaucet, isMiner, addCfg
import json
import requests
from project.InterfaceLocking import mainInterface
import project.classes
from project.pclass import c_peer
from copy import deepcopy
from project.models import m_cfg, m_visualCFG, m_Delay, m_info, m_isPOST
from project.nspec.blockchain.modelBC import m_pendingTX, m_BufferMinerCandidates, m_Blocks
from project.nspec.blockchain.modelBC import m_AllBalances
import re
import sys

c_MainIntf = mainInterface()


def shutdown_server():
    m_cfg['shutdown'] = True
    print("Down")
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutDown', methods=["POST"])
def shutDown():
    try:
        shutdown_server()
    except Exception:
        print("Smooth Shutdown failed")
    # return 'Server shutting down...'
    sys.exit(0)


@app.route('/visualGet', methods=["GET"])
def visualGet():
    try:
        dat = {}
        for item in m_Delay:
            if 'delayID' in item:
                dat = deepcopy(item)
                item['releaseID'] = dat['delayID']
                del item['delayID']
                break
        dat['activePeers'] = m_cfg['activePeers']
        dat['shareToPeers'] = m_cfg['shareToPeers']
        dat['peerOption'] = m_cfg['peerOption']
        addCfg(dat)
        return setOK(dat)
    except Exception:
        print("visualGet Failed")
    return errMsg("Request failed")

@app.route('/visualRelease/<int:idx>', methods=["GET"])
def visualRelease(idx):
    try:
        found = False
        rel = {}
        for item in m_Delay:
            if ('releaseID' in item) and (item['releaseID'] == idx):
                rel = item
                found = True
                break
        if found is True:
            m_Delay.remove(rel)
            if rel['asynchPOST'] is True:
                requests.post(url=rel['url'], json=rel['json'], headers={'accept': 'application/json'})
            return setOK(rel)
        return errMsg("Unexpected Release for "+str(id))
    except Exception:
        print("visualRelease Failed")
    return errMsg("Request failed")

@app.route('/visualCfg', methods=["POST"])
def visualCfg():
    try:
        values = request.get_json()
        if values['active'] is True:
            pattern = re.compile(values['pattern'])
            m_visualCFG['active'] = True
            m_visualCFG['pattern'] = pattern
            return setOK(values)
        m_visualCFG['active'] = False
        m_Delay.clear()
        return setOK("Tracking switched off")
    except Exception:
        return errMsg("JSON not decodeable or missing item")


@app.route('/cfg', methods=["GET"])
def get_cfg():
    m_ret = deepcopy(m_cfg)
    addCfg(m_ret)
    return setOK(m_ret)

### TODO remove after debugging
@app.route('/load/<file>', methods=["GET"])
def loadSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/save/<file>', methods=["GET"])
def saveSys(file):
    linkInfo = {"file": file}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/info', methods=["GET"])
def get_info():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/debug', methods=["GET"])
def debug():
    m_ret = {"cfg": deepcopy(m_cfg)}
    addCfg(m_ret)
    if isBCNode():
        m_ret.update({"TX": deepcopy(m_pendingTX)})
        m_ret.update({"minerCandidates": deepcopy(m_BufferMinerCandidates)})
        m_ret.update({"balances": deepcopy(m_AllBalances)})
        m_ret.update({"blocks": deepcopy(m_Blocks)})
    return setOK(m_ret)

@app.route('/debug/reset-chain', methods=["GET"])
def debug_resetChain():
    # this is a very special case, as it is not GET but actually a POST issue
    m_isPOST.append("Reset Chain")
    while len(m_isPOST) > 1:
        if c_MainIntf.delay("reset-chain",999) is False:
            break   # for some reason we decide to ignore the lock
    ret = project.classes.c_blockchainNode.c_blockchainHandler.resetChainReply()
    m_isPOST.clear()
    return ret


@app.route('/blocks', methods=["GET"])
@app.route('/transactions/pending', methods=["GET"])
@app.route('/transactions/confirmed', methods=["GET"])
@app.route('/balances', methods=["GET"])
def transactions_GET():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/blocks/<int:number>', methods=["GET"])
def blocks_getByNumber(number):
    linkInfo = {"blockNumber": number}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/blocks/hash/<int:hfrom>/<int:hto>/<int:hcnt>', methods=['GET'])
def getBlockHash(hfrom, hto, hcnt):
    linkInfo = {"from": hfrom, "to": hto, 'cnt': hcnt}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/blockBalances/<int:hto>', methods=['GET'])
def getBlockBalances(hto):
    linkInfo = {"to": hto}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

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
        return errMsg("JSON not decodeable")
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)


@app.route('/address/<address>/transactions', methods=["GET"])
@app.route('/address/<address>/balance', methods=["GET"])
def address_bal_TX(address):
    linkInfo = {"address": address}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/peers/notify-new-block', methods=['POST'])
def peers_notifyNewBlock():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable")
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

@app.route('/peers', methods=["GET"])
def peers():
    return c_peer.listPeers()


@app.route('/peers/connect', methods=['POST'])
@app.route('/peers/disconnect', methods=['POST'])
# this is invoked by user to tell me that the other node exists at IP
def peers_connect():
    try:
        values = request.get_json()
        pt = request.path
        return c_peer.peersConnect(request.host, values, "dis" not in pt)
    except Exception:
        return errMsg("JSON not decodeable")


@app.route('/mining/get-mining-job/<minerAddress>', methods=["GET"])
def mining_getMiningJob(minerAddress):
    linkInfo = {"minerAddress": minerAddress}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)

@app.route('/mining/submit-mined-block', methods=['POST'])
def mining_submitBlock():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodable")
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)

#the next routre was removed, as it is not clear how a node can force a mining with arbitrary address
#unless the node does its own mining, which doe snot make sense
# @app.route('/debug/mine/<minerAddress>/<int:difficulty>', methods=["GET"])
# def debug_mining(minerAddress, difficulty):
#     linkInfo = {"address": minerAddress, "difficulty": difficulty}
#     return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


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

    if isBCNode():
        return render_template("indexBC" + addOn + ".html")
    if isWallet():
        return render_template("TabWallet" + addOn + ".html")
    if isFaucet():
        return render_template("TabFaucet" + addOn + ".html")
    if isMiner():
        return render_template("TabMiner" + addOn + ".html")
    if isGenesis():
        project.classes.c_genesisInterface.initGenesis()
        return render_template("TabGenesis" + addOn + ".html")

    response = {
        'NodeType': m_info['type'],
        'info': "Requested URL/API is not available"
     }
    return errMsg(response)

################## Wallet specific routes
@app.route('/wallet/create', methods=['POST'])
@app.route('/wallet/createKey', methods=['POST'])
@app.route('/wallet/transfer', methods=['POST'])
def wallet_POST():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable")
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


################## Geneis specific routes

@app.route('/viewGX', methods=['GET'])
def gen_viewGX():
    linkInfo = {}
    return c_MainIntf.nodeSpecificGET(request.path, linkInfo)


@app.route('/genFaucet', methods=['POST'])
@app.route('/useTX', methods=['POST'])
@app.route('/genGX', methods=['POST'])
@app.route('/updGX', methods=['POST'])
@app.route('/genTX', methods=['POST'])
@app.route('/setID', methods=['POST'])
def genesis_POST():
    linkInfo = {}
    try:
        values = request.get_json()
    except Exception:
        return errMsg("JSON not decodeable")
    return c_MainIntf.nodeSpecificPOST(request.path, linkInfo, values, request)


################## the following two are only for testing while developing peer module
@app.route("/listNodes", methods=["GET"])
def listNodes():
    return setOK(m_cfg['activePeers'])

@app.route("/clrNode", methods=['POST'])
def clrNode():
    values = request.get_json()

    #Check that the required fields are in the POST'ed data.
    required = ['node']
    python_obj = json.loads(values)
    for k in required:
        if k not in python_obj:
            return 'Invalid param', 400

    #TODO what was clrNode and setNode() doing?
    oldNodes = setNode(python_obj['node'], m_info['nodeURL'])
    for oldNode in oldNodes:
        if oldNode in m_cfg['nodes']:
            m_cfg['nodes'].remove(oldNode)

    return setOK(m_cfg)
