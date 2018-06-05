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
        afrom, ato, value, total, txhash = tx['from'], tx['to'], tx['value'], tx['value']+tx['fee'], tx['transactionDataHash']
        # this can be called either during block setting up
        # or after receiving confirmed block
        if (not afrom in tempBalance):
            if (not afrom in m_AllBalances):
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
                return {}

        tempBalance[afrom] = tempBalance[afrom] - total

        # pend = 0
        # if (txhash in m_pendingTX):
        #     # If this is from a block, we reduce pending amount
        #     pend = value
        #
        # if (isNewTx == True):
        #     # As this is new TX outside block, it adds pending amount to recipients instead of reducing
        #     pend = -pend

        if (not ato in m_AllBalances):
            # if (isNewTx):
            #     addNewRealBalance(ato, -1)
            # else:
            addNewRealBalance(ato, tx['minedInBlockIndex'])
            #TODO can remove next line, as it is only for testing which has a free balance of 1000 in data struct
            m_AllBalances[ato]['curBalance'] = 0

        if (not ato in tempBalance):
            tempBalance.update({ato: m_AllBalances[ato]['curBalance']})

        tempBalance[ato] = tempBalance[ato] + value
        # m_candidateBlockBalance[ato][1] = m_candidateBlockBalance[ato][1] - pend
    return tempBalance

# def verifySenderBalance(trx):
#     if (not 'from' in trx):
#         return "Invalid transaction, no 'from' field"
#     isCoinBase = (trx['from'] == defAdr)
#
#     if (isCoinBase):
#         # TODO set the corrctt checking parameter instead
#         #return verifyBasicTX(trx, isCoinBase, m_staticTransactionRef)
#         err=""
#     else:
#         err = verifyBasicTX(trx, isCoinBase, m_staticTransactionRef)
#
#     if (len(err)>0):
#         return err
#
#     addrFrom = trx['from']
#     #TODO remove this convencience default faucet after testing!!!!
#     if (not trx['from'] in m_AllBalances):
#         # TODO remove this after initial tests, which gives anyone 50 from scratch
#         newInfo = deepcopy(m_staticBalanceInfo)
#         m_AllBalances.update({addrFrom: newInfo})
#     #end of TODO remove temporaray
#
#
#     if (not addrFrom in m_AllBalances):
#         return "Invalid TX, no account registered with any balance for: " + str(addrFrom)
#
#     value = trx['value']
#     fee = trx['fee']
#     total = value + fee
#     # TODO is this comparison corrcet with confirmedBalance???
#     if (total > m_AllBalances[addrFrom]['balance']['confirmedBalance']):
#         # TODO is this unsuccesfull? Or still go to block chain??
#         return "Insufficient funds"
#     return ""

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
    if (len(updBalance) == 0):
        return "Block rejected, invalid TX detected in: "+tx['transactionDataHash']

    # all tx in this block are valid, so update actual balances based on the results from checking
    for addr in updBalance:
        #TODO set history value for block and address
        #if (not addrTo in m_AllBalances):
        #    addNewRealBalance(addr, blockIndex)
        m_AllBalances[addr]['curBalance'] = updBalance[addr]

    for tx in txList:
        if (tx['transactionDataHash'] in m_pendingTX):
            del m_pendingTX[tx['transactionDataHash']]

    return ""


def getBalance(address):
    if (len(address) == len(defAdr)):
        ret = deepcopy(m_TemplateSingleBalance)
        found = False
        if (address in m_AllBalances):
            found = True
            ret['confirmedBalance'] = m_AllBalances[address]['curBalance']
            #ret['confirmedBalance'] = ???m_AllBalances[address]['curBalance']

        for tx in m_pendingTX:
            # TODO temp remove later
            if (len(m_AllBalances)<2):
                if (m_pendingTX[tx]['from'] == address):
                    found = True
                    ret['confirmedBalance'] = 1000
            # TODO end of free money for start up trial ony
            if (m_pendingTX[tx]['to'] == address):
                found = True
                ret['pendingBalance'] = ret['pendingBalance'] + m_pendingTX[tx]['value']

        if (found):
            return setOK(ret)
    return errMsg("Invalid address", 404)


def getAllBalances():
    ret = {}
    for balAddr in m_AllBalances:
        bal = m_AllBalances[balAddr]['curBalance']
        #TODO sort by address or so?
        if (bal != 0):
            ret.update({balAddr: bal})
    return setOK(ret)
