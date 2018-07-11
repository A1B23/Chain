import time
import random
import json
import datetime
import hashlib
from flask import jsonify
from project.models import m_cfg, defNodeID
from project.models import m_info

#Call this for debuggin print to screen which needs to be removed at the end
def d(mes):
    print(mes)


def jsonToStr(jsonDict):
    json_encoder = json.JSONEncoder(separators=(',', ':'))
    tran_json = json_encoder.encode(jsonDict)
    return tran_json


def sha256ToHex(ref, data):
    return sha256StrToHex(putDataInOrder(ref, data))

def sha256StrToHex(toStr):
    return hashlib.sha256(toStr.encode("utf8")).hexdigest()


def getFutureTimeStamp(addedTime):
    #TODO add a few sseconds addedTime, which depends on difficulty to the time stamp
    timestamp = (datetime.datetime.now()).isoformat()
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

def checkType(asSet, type):
    return (asSet == type) or (asSet == "*"+type)

def isMiner():
    return checkType(m_info['type'], "Miner")


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


def checkSameFields(check, myReference, sameLen):
    colErr=""
    for chk in myReference:
        if not chk in check:
            if (colErr != ""):
                colErr = colErr + " and "
            colErr = colErr + "'" + chk + "'"
    if (colErr != ""):
        colErr = "Invalid structure: field " + colErr + " is missing"
    if sameLen:
        if (len(check) != len(myReference)):
            colErr = colErr + " Invalid number of fields in transaction"
    return colErr


def errMsg(msg, code):
    return jsonify({"errorMsg": msg}), code


def setOK(data):
    if (isinstance(data, str)):
        return jsonify({"message": data}), 200
    return jsonify(data), 200


def isSameChain(detail):
    return True
    #TODO adjust this return (detail['about'] == m_info['about']) and (detail['chainId'] == m_info['chainId'])


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
    #We deliberately ignore additional data in the data structure, if any present
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




