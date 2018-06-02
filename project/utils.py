import time
import random
import requests
import json

import datetime
import hashlib
from flask import jsonify
from project.models import *
from project.nspec.blockchain.modelBC import m_BalanceInfo, m_staticBalanceInfo
from copy import deepcopy

#Call this for debuggin print to screen which needs to be removed at the end
def d(mes):
    print(mes)


def info():
    return jsonify(m_info), 200


def jsonToStr(jsonDict):
    json_encoder = json.JSONEncoder(separators=(',', ':'))
    tran_json = json_encoder.encode(jsonDict)
    return tran_json


def sha256ToHex(data):
    hash_bytes = hashlib.sha256(jsonToStr(data).encode("utf8")).digest()
    return hex(int.from_bytes(hash_bytes, byteorder="big"))[2:]


def getFutureTimeStamp(addedTime):
    timestamp = (datetime.datetime.now()+addedTime).isoformat()
    timestamp = timestamp + "Z"
    return timestamp


def getTime():
    timestamp = datetime.datetime.now().isoformat()
    timestamp = timestamp + "Z"
    return timestamp


def genNodeID():
    timestamp = (time.time() * 10000)
    hex_string = ""
    for xx in range(1,int(len(defNodeID)/2)):
        hex_string = hex_string+ '0x{:02x}'.format(int(random.randint(1000000, 9999999)))[2:]
    hex_string=hex_string +'0x{:02x}'.format(int(timestamp))
    # still need to sha over it and return
    return hex_string[0:len(defNodeID)]


def isMiner():
    return m_cfg['type'] == "Miner"


def isWallet():
    return m_cfg['type'] == "Wallet"


def isBCNode():
    return m_cfg['type'] == "BCNode"


def isFaucet():
    return m_cfg['type'] == "Faucet"


def isExplorer():
    return m_cfg['type'] == "Explorer"


def checkRequiredFields(check, myReference, mandatoryList, shortenManadatory):
    missing = []
    fails = []
    for chk in myReference:
        if not chk in check:
            missing.append(str(chk))
            if chk in mandatoryList:
                fails.append(chk)
                if (shortenManadatory):
                    break  # one false is enough in this case.... stop
        else:
            if chk in mandatoryList:
                if (check[chk] != myReference[chk]):
                    fails.append(chk)
                    if (shortenManadatory):
                        break       #one false is enough in this case.... stop

    return missing, (len(check) - len(myReference)), fails


def checkSameFields(check,myReference,sameLen):
    colErr=""
    for chk in myReference:
        if not chk in check:
            if (colErr != ""):
                colErr = colErr + " and "
            colErr = colErr + "'"+chk+"'"
    if (colErr != ""):
        colErr = "Invalid structure: field " + colErr + " is missing"
    if sameLen:
        if (len(check) != len(myReference)):
            colErr = colErr + " Invalid number of fields in transaction"
    return colErr


def errMsg(msg,code):
    return jsonify({"errorMsg":msg}),code


def setOK(data):
    return jsonify(data),200

def isSameChain(detail):
    return True
    #TODO adjust this return (detail['about'] == m_info['about']) and (detail['chainId'] == m_info['chainId'])

def createNewBalance(addr):
    newInfo = deepcopy(m_staticBalanceInfo)
    m_BalanceInfo.update({addr: newInfo})

def updatePendingBalance(addr, trx, blockIndex, value):
    if (not addr in m_BalanceInfo):
        createNewBalance(addr)
    m_BalanceInfo[addr]['balance']['pendingBalance'] = m_BalanceInfo[addr]['balance']['pendingBalance'] + value
    nxt = {"blockIndex": blockIndex, "TX": deepcopy(trx)}
    m_BalanceInfo[addr]['info'].append(nxt)


