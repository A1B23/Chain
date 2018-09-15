import time
import random
import json
import datetime
import hashlib
import re
from urllib.parse import urlparse
from flask import jsonify
from project.models import defNodeID, m_info, m_candidateMiner_order, m_txorderForBlockHash, m_cfg
from project.nspec.blockchain.modelBC import m_Blocks, m_pendingTX
from project.nspec.miner.modelM import cfg
from project.nspec.wallet.modelW import w_cfg


#Call this for debug print to screen which needs to be removed at the end
def d(mes):
    print(mes)
    return mes


def jsonToStr(jsonDict):
    json_encoder = json.JSONEncoder(separators=(',', ':'))
    tran_json = json_encoder.encode(jsonDict)
    return tran_json


def sha256ToHex(ref, data):
    return sha256StrToHex(putDataInOrder(ref, data))


def sha256StrToHex(toHashStr):
    return hashlib.sha256(toHashStr.encode("utf8")).hexdigest()


def getTime():
    timestamp = datetime.datetime.now().isoformat()
    timestamp = timestamp[:timestamp.index(".")+4] + "Z"
    return timestamp


def getFutureTime(deltaInSecs):
    timestamp = (datetime.datetime.now() + datetime.timedelta(seconds=deltaInSecs)).isoformat()
    timestamp = timestamp[:timestamp.index(".")+4] + "Z"
    return timestamp


def genNodeID():
    timestamp = (time.time() * 10000)
    hex_string = ""
    for xx in range(1, int(len(defNodeID)/2)):
        hex_string = hex_string + '0x{:02x}'.format(int(random.randint(1000000, 9999999)))[2:]
    hex_string=hex_string + '0x{:02x}'.format(int(timestamp))
    # still need to sha over it and return
    return hex_string[0:len(defNodeID)]


def checkType(asSet, type):
    return (asSet == type) or (asSet == "*"+type)


def isMiner():
    return checkType(m_info['type'], "Miner")


def isGenesis():
    return checkType(m_info['type'], "Genesis")


def isWallet():
    return checkType(m_info['type'], "Wallet")


def isBCNode():
    return checkType(m_info['type'], "BCNode")


def isABCNode(ref):
    return checkType(ref, "BCNode")


def isFaucet():
    return checkType(m_info['type'],"Faucet")


def isExplorer():
    return checkType(m_info['type'], "Explorer")


def addCfg(m_ret):
    # this part is only needed for the visualisation data during simulation
    if isBCNode():
        if m_cfg['chainInit'] is False:
            m_ret['chainHeight'] = len(m_Blocks)
            tot = 0
            tot2 = 0
            for tx in m_pendingTX:
                tot2 = (tot2+int(tx,16)) % 65535
                tot = tot + m_pendingTX[tx]['value']
            m_ret['pendTX'] = str(len(m_pendingTX))+"@"+str(tot)+"("+str(tot2)+")"

            m_ret['blockHash'] = m_Blocks[-1]['blockHash']
    elif isMiner():
        m_ret['nonceCnt'] = str(cfg['nonceCnt']) + "/(..."+cfg['blockHash'][0:6]+")/" + \
                            cfg['dateCreated'][cfg['dateCreated'].index("T")+1:-1]
    elif isWallet():
        m_ret['lastBal'] = w_cfg['lastBal']



def checkRequiredFields(check, myReference, mandatoryList, shortenManadatory):
    missing = []
    fails = []
    for chk in myReference:
        if chk not in check:
            missing.append(str(chk))
            if chk in mandatoryList:
                fails.append(chk)
                if shortenManadatory is True:
                    break  # one false is enough in this case.... stop
        else:
            if chk in mandatoryList:
                if check[chk] != myReference[chk]:
                    fails.append(chk)
                    if shortenManadatory is True:
                        break       # one false is enough in this case.... stop

    return missing, (len(check) - len(myReference)), fails


def checkSameFields(check, myReference, sameLen):
    colErr = ""
    for chk in myReference:
        if not chk in check:
            if colErr != "":
                colErr = colErr + " and "
            colErr = colErr + "'" + chk + "'"
    if colErr != "":
        colErr = "Invalid structure: field " + colErr + " is missing"
    if sameLen:
        if len(check) != len(myReference):
            colErr = colErr + " Invalid number of fields in transaction"
    return colErr


def makeResp(data, code=200):
    respx = jsonify(data)
    respx.status_code = code
    return respx


def errMsg(msg, code=400):
    return makeResp({"errorMsg": msg}, code)


def setOK(data, code=200):
    if isinstance(data, str):
        return makeResp({"message": data}, code)
    return makeResp(data, code)


def isSameChain(detail):
    return True
    #TODO adjust this return (detail['about'] == m_info['about']) and (detail['chainId'] == m_info['chainId'])
    #carefule of difference between chainref and chainID


def addItem(element):
    if (isinstance(element, int)):
        return str(element) + ','
    elif (isinstance(element, list)):
        lst = "["
        for sx in element:
            lst = lst + addItem(sx)
        if (len(lst) > 1):
            return lst[:-1] + "],"
        return "[],"
    else:
        return '"' + str(element) + '",'


def addItems(item, element):
    return '"' + item + '":' + addItem(element)


def putDataInOrder(order, data):
    # We deliberately ignore additional data in the data structure, if any present
    ret = "{"
    for item in order:
        if (item in data):
            ret = ret + addItems(item, data[item])
    if (len(ret) > 1):
        return ret[:-1] + "}"
    return "{}"


def makeMinerHash(candidate):
    data = candidate['blockDataHash'] + "|" + candidate['dateCreated'] + "|" + str(candidate['nonce'])
    return hashlib.sha256(data.encode("utf8")).hexdigest()


def makeBlockDataHash(TXBlock, isGenesis):
    # now the block is done, hash it for miner
    # need to calculate now the hash for this specific miner based candidateBlock
    # the hash for the miner has to be in specific order of data
    forHash = "{"
    try:
        for txs in m_candidateMiner_order:
            if txs == 'transactions':
                forHash = forHash + '"' + txs + '":['
                for tx in TXBlock['transactions']:
                    forHash = forHash + putDataInOrder(m_txorderForBlockHash, tx)
                forHash = forHash + "],"
            else:
                # genesis block skips a few fields, others must have
                if (isGenesis is False):
                    if (txs in TXBlock):
                        forHash = forHash + addItems(txs, TXBlock[txs])

        ret = sha256StrToHex(forHash[:-1] + "}")
        return ret
    except Exception:
        return "fail to create block data hash"


def getValidURL(url, upToNetLoc):
    try:
        parsed_uri = urlparse(url)
        if upToNetLoc is True:
            domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        else:
            domain = '{uri.scheme}://{uri.netloc}{uri.path}'.format(uri=parsed_uri)
        if (not url.startswith(domain)) or (parsed_uri.query != "") or (parsed_uri.netloc == "") or ((upToNetLoc is False) and (parsed_uri.path == "")):
            return ""


        regex = re.compile(
            r'^(?:http)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        res = re.match(regex, domain)
        if res is None:
            return ""
        regex = re.compile(
            r'^(?:http)s?://'  # http:// or https://
            r'(?P<IP>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE)
        res = re.match(regex, domain)
        if res is not None:
            for tst in res.group("IP").split("."):
                tst = int(tst)
                if (tst < 0) or (tst > 255):
                    return ""
        return domain
    except Exception:
        return ""




