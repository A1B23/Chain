from project.nspec.blockchain.modelBC import m_AllBalances, m_candidateBlockBalance, m_staticBalanceInfo, \
    m_pendingTX, m_TemplateSingleBalance
from project.models import defAdr
from project.utils import setOK, errMsg
from copy import deepcopy


def addNewRealBalance(addr, blockNo):
    m_AllBalances.update({addr: createNewBalance(blockNo)})

def createNewBalance(blockNo):
    newInfo = deepcopy(m_staticBalanceInfo)
    #newInfo['curBalance'] = 0
    newInfo['createdInBlock'] = blockNo
    #newInfo['confirm'] = {}
    return newInfo


def updateConfirmedBalance(txList, isNewTx):
    tempBalance = {}
    for tx in txList:
        afrom, ato, value, total, txhash = tx['from'], tx['to'], tx['value'], (tx['value']+tx['fee']), tx['transactionDataHash']
        # this can be called either during block setting up
        # or after receiving confirmed block
        if not afrom in tempBalance:
            if not afrom in m_AllBalances:
                #TODO remove later, now only for testing we allow any address
                addNewRealBalance(afrom,0)
                m_AllBalances[afrom]['curBalance'] = 1000
                #TODO after test finished, bring in the return again1!!!
                #if (isNewTx == True):
                #   tx["transferSuccessful"] = False
                #return False

            tempBalance.update({afrom: m_AllBalances[afrom]['curBalance']})

        #special case for coinbase needed
        if (afrom != defAdr) and (tempBalance[afrom] < total):
            # if (isNewTx == True):
            #     tx["transferSuccessful"] = False
            # elif (tx["transferSuccessful"] == True):
            return {} #inidcate invalid block, as all TX are supposed to be ok at this stage

        tempBalance[afrom] = tempBalance[afrom] - total #reduce by value + fee

        # pend = 0
        # if (txhash in m_pendingTX):
        #     # If this is from a block, we reduce pending amount
        #     pend = value
        #
        # if (isNewTx == True):
        #     # As this is new TX outside block, it adds pending amount to recipients instead of reducing
        #     pend = -pend

        if not ato in m_AllBalances:
            # if (isNewTx):
            #     addNewRealBalance(ato, -1)
            # else:
            addNewRealBalance(ato, tx['minedInBlockIndex'])
            #whatever the default, make sure to set 0
            m_AllBalances[ato]['curBalance'] = 0

        if not ato in tempBalance:
            tempBalance.update({ato: m_AllBalances[ato]['curBalance']})

        tempBalance[ato] = tempBalance[ato] + value #add only value, fee went to  miner
        # m_candidateBlockBalance[ato][1] = m_candidateBlockBalance[ato][1] - pend
    return tempBalance

def confirmUpdateBalances(txList, blockIndex):
    # m_candidateBlockBalance.clear()
    err = confirmUpdateBalancesNow(txList, blockIndex)
    # m_candidateBlockBalance.clear()
    return err


def confirmUpdateBalancesNow(txList, blockIndex):
    # entering here we know the structure of the TX are all ok, so settle only balances
    # first we update the buffer info, and only if all pass
    # then update the actual balances involved
    # theoretically if it is our own block, all should be correct, but we check anyway
    updBalance = updateConfirmedBalance(txList, False)
    if len(updBalance) == 0:
        return "Block rejected, invalid TX detected in: " + tx['transactionDataHash']

    # all tx in this block are valid, so update actual balances based on the results from checking
    for addr in updBalance:
        #if (not addrTo in m_AllBalances):
        #    addNewRealBalance(addr, blockIndex)
        m_AllBalances[addr]['curBalance'] = updBalance[addr]

    #balances updated, remove TX from pending list
    for tx in txList:
        if tx['transactionDataHash'] in m_pendingTX:
            del m_pendingTX[tx['transactionDataHash']]

    return ""


def getBalance(address):
    if len(address) == len(defAdr):
        ret = deepcopy(m_TemplateSingleBalance)
        found = False
        if address in m_AllBalances:
            found = True
            ret['confirmedBalance'] = m_AllBalances[address]['curBalance']

        for tx in m_pendingTX:
            if m_pendingTX[tx]['to'] == address:
                #TODO must check if it is a valid TX, not a below balance one as not signed!!!??
                found = True
                ret['pendingBalance'] = ret['pendingBalance'] + m_pendingTX[tx]['value']
            # The next might be outside spec, but makes sense to me, negative pending balance for spending
            if m_pendingTX[tx]['from'] == address:
                #TODO must check if it is a valid TX, not a below balance one as not signed!!!??
                found = True
                ret['pendingBalance'] = ret['pendingBalance'] - (m_pendingTX[tx]['value']+m_pendingTX[tx]['fee'])()

        if found is True:
            return setOK(ret)
        return setOK("No entry found")
    return errMsg("Invalid address", 404)


def getAllBalances():
    ret = {}
    for balAddr in m_AllBalances:
        bal = m_AllBalances[balAddr]['curBalance']
        if bal != 0:
            ret.update({balAddr: bal})
    # no need to sort by address or so
    return setOK(ret)
