from project.nspec.blockchain.modelBC import m_AllBalances, m_staticBalanceInfo, m_pendingTX
from project.models import defAdr, m_TemplateSingleBalance, m_info
from project.utils import setOK, errMsg
from copy import deepcopy


def addNewRealBalance(addr, blockNo):
    m_AllBalances.update({addr: createNewBalance(blockNo)})


def createNewBalance(blockNo):
    newInfo = deepcopy(m_staticBalanceInfo)
    newInfo['createdInBlock'] = blockNo
    return newInfo


def setBalanceTo(newBal,blockNo):
    delThem = []
    for b in m_AllBalances:
        if (b not in newBal) or (m_AllBalances[b]['createdInBlock'] > blockNo):
            delThem.append(b)
        else:
            m_AllBalances[b]['curBalance'] = newBal[b]

    for b in delThem:
        m_AllBalances.pop(b)


def updateTempBalance(txList, tempBalance, chkOnly=""):
    for tx in txList:
        afrom, ato, value, total, txhash = tx['from'], tx['to'], tx['value'], (tx['value']+tx['fee']), tx['transactionDataHash']
        # this can be called either during block setting up
        # or after receiving confirmed block
        if chkOnly != "":
            if (chkOnly != afrom) and (chkOnly != ato):
                continue
        if afrom not in tempBalance:
            tempBalance.update({afrom: 0})

        tempBalance[afrom] = tempBalance[afrom] - total #reduce by value + fee

        if ato not in tempBalance:
            tempBalance.update({ato: value})
        else:
            tempBalance[ato] = tempBalance[ato] + value #add only value, fee went to  miner
    return True


def updateConfirmedBalance(txList, isGenesis):
    tempBalance = {}
    for tx in txList:
        afrom, ato, value, total, txhash = tx['from'], tx['to'], tx['value'], (tx['value']+tx['fee']), tx['transactionDataHash']
        # this can be called either during block setting up
        # or after receiving confirmed block
        if afrom not in tempBalance:
            if afrom not in m_AllBalances:
                if isGenesis is False:
                   tx["transferSuccessful"] = False
                   # below, nakov chain definition inconsistency, but we try to handle it
                   # this is a weakness in the nakov chain definition that ther miner can cheat as
                   # the miner already got the money no one has
                   # but I cannot redefine the entire system, so I go along with it
                   # the problem is that if balance is checked upon submit, then there is no transferSuccessful == false
                   # because it will have to be outright rejected, but instruction was to include unsuccessful
                   # in the change, so balance check is not possible/suitable
                   continue
                if afrom != defAdr:
                    return {}
                addNewRealBalance(afrom, 0)
            tempBalance.update({afrom: m_AllBalances[afrom]['curBalance']})

        # special case for coinbase needed
        if (afrom != defAdr) and (tempBalance[afrom] < total):
            return {}  # indicate invalid block, as all TX are supposed to be ok at this stage

        tempBalance[afrom] = tempBalance[afrom] - total  # reduce by value + fee

        if ato not in m_AllBalances:
            addNewRealBalance(ato, tx['minedInBlockIndex'])
            # whatever the default, make sure to set 0
            m_AllBalances[ato]['curBalance'] = 0

        if ato not in tempBalance:
            tempBalance.update({ato: m_AllBalances[ato]['curBalance']})

        tempBalance[ato] = tempBalance[ato] + value  # add only value, fee went to  miner
    return tempBalance


def confirmUpdateBalances(txList, isGenesis):
    # entering here we know the structure of the TX are all ok, so settle only balances
    # first we update the buffer info, and only if all pass
    # then update the actual balances involved
    # theoretically if it is our own block, all should be correct, but we check anyway
    updBalance = updateConfirmedBalance(txList, isGenesis)
    if len(updBalance) == 0:
        return "Block rejected, invalid TX detected in: " + txList['transactionDataHash']

    # all tx in this block are valid, so update actual balances based on the results from checking
    for addr in updBalance:
        m_AllBalances[addr]['curBalance'] = updBalance[addr]

    # balances updated, remove TX from pending list
    for tx in txList:
        if tx['transactionDataHash'] in m_pendingTX:
            del m_pendingTX[tx['transactionDataHash']]
    # TODO test that now invalid Tx are correctly removed, as another block and new balances applied
    remTx = []
    for tx in m_pendingTX:
        remTx.append(tx)
        tmpBal = getBalance(tx['from'], remTx)
        if tmpBal['confirmedBalance'] + tmpBal['pendingBalance'] < tx['value'] + tx['fee']:
            # Not enough balance anymore to keep the TX alive
            del remTx[-1]

    if len(remTx) != len(m_pendingTX):
        m_pendingTX.clear()
        m_pendingTX.extend(remTx)

    return ""


def confirmRevertBalances(txList):
    # entering here we know the structure of the TX are all ok, so settle only balances
    # first we update the buffer info, and only if all pass
    # then update the actual balances involved
    # theoretically if it is our own block, all should be correct, but we check anyway
    updBalance = updateConfirmedBalance(txList, False)
    if len(updBalance) == 0:
        #This should never happen!!!
        return "Block rejected, invalid TX detected in: " + txList['transactionDataHash']

    # all tx in this block are valid, so update actual balances based on the results from checking
    for addr in updBalance:
        m_AllBalances[addr]['curBalance'] = m_AllBalances[addr]['curBalance'] - (updBalance[addr] - m_AllBalances[addr]['curBalance'])

    # balances updated, re-install actual TX into pending list
    for tx in txList:
        # special case for coinbase, because the miner fee is not an actual transaction to restore!
        if tx['from'] != defAdr:
            if tx['transactionDataHash'] not in m_pendingTX:
                m_pendingTX[tx['transactionDataHash']] = tx
    m_info['confirmedTransactions'] = m_info['confirmedTransactions'] - len(txList)
    return ""


def getBalanceRet(address):
    if len(address) == len(defAdr):
        return setOK(getBalance(address))  # slides say if valid address but no TX, return 0 balance, not error!
    return errMsg("Invalid address", 404)


def getBalance(address, refTX=m_pendingTX):
    ret = deepcopy(m_TemplateSingleBalance)
    if address in m_AllBalances:
        ret['confirmedBalance'] = m_AllBalances[address]['curBalance']

    for tx in refTX:
        if refTX[tx]['to'] == address:
            #TODO must check if it is a valid TX, not a below balance one as not signed!!!??
            found = True
            ret['pendingBalance'] = ret['pendingBalance'] + refTX[tx]['value']
        # The next might be outside spec, but makes sense to me, negative pending balance for spending
        if refTX[tx]['from'] == address:
            #TODO must check if it is a valid TX, not a below balance one as not signed!!!??
            found = True
            ret['pendingBalance'] = ret['pendingBalance'] - (refTX[tx]['value']+refTX[tx]['fee'])

    return ret



def getAllBalances():
    ret = {}
    for balAddr in m_AllBalances:
        bal = m_AllBalances[balAddr]['curBalance']
        if bal != 0:
            ret.update({balAddr: bal})
    # no need to sort by address or so
    return setOK(ret)
