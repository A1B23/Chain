from project.utils import *
from project.nspec.blockchain.modelBC import *
from copy import deepcopy
from project.pclass import c_peer


firstTime = [True]
def verifyBasicTX(trans,isCoinBase,ref):
    m, l, f = checkRequiredFields(trans, ref , [],False)
    colErr = ""
    for x in m:
        if (colErr == ""):
            colErr = "Missing field(s): '" + x + "'"
        else:
            colErr = colErr + "and '" + x + "'"
    if (l != 0):
        # TODO test only still unclear about data structure so for test accept both
        if (l != 1) or ("transactionDataHash" not in trans):
            colErr = colErr + " Invalid number of fields in transaction"
    if (colErr == ""):  # final checks
        if (len(trans['senderSignature']) != 2):
            colErr = colErr + " Invalid number of elements in 'senderSignature' field"
    if (not isinstance(trans['fee'], int)):
        colErr = colErr + "Fees must be integer, you sent: " + str(trans['fee'])
    else:
        if (isCoinBase):
            if (trans['fee'] != 0):
                colErr = colErr + "Coinbase fee should be zero, you sent: " + str(trans['fee'])
        else:
            if (trans['fee'] < m_stats['m_minFee']):
                colErr = colErr + "Minimun fee 10 micro-coins, you sent: " + str(trans['fee'])
    if (not isinstance(trans['value'], int)):
        colErr = colErr + "Value must be integer, you sent: " + str(trans['value'])
    else:
        if (trans['value'] < 0):
            colErr = colErr + "Minimun value 0 micro-coins, you sent: " + str(trans['value'])
    return colErr


def verifySenderBalance(trx):
    if (not 'from' in trx):
        return "Invalid transaction, no 'from' field"
    isCoinBase = (trx['from'] == defAdr)

    if (isCoinBase):
        # TODO set the corrctt checking parameter instead
        #return verifyBasicTX(trx, isCoinBase, m_staticTransactionRef)
        err=""
    else:
        err = verifyBasicTX(trx, isCoinBase, m_staticTransactionRef)

    if (len(err)>0):
        return err

    addrFrom = trx['from']
    #TODO remove this convencience default faucet after testing!!!!
    if (not trx['from'] in m_BalanceInfo):
        # TODO remove this after initial tests, which gives anyone 50 from scratch
        newInfo = deepcopy(m_staticBalanceInfo)
        m_BalanceInfo.update({addrFrom: newInfo})
    #end of TODO remove temporaray


    if (not addrFrom in m_BalanceInfo):
        return "Invalid TX, no account registered with any balance for: " + str(addrFrom)

    value = trx['value']
    fee = trx['fee']
    total = value + fee
    # TODO is this comparison corrcet with confirmedBalance???
    if (total > m_BalanceInfo[addrFrom]['balance']['confirmedBalance']):
        # TODO is this unsuccesfull? Or still go to block chain??
        return "Insufficient funds"
    return ""

def verifyBlock(block):
    m, l, f = checkRequiredFields(block, m_completeBlock, [],False)
    if (block['index']==0):
        #special case for genesis bloc
        if (len(m) != 1) or (m[0] != "prevBlockHash"):
            return "Invalid Genesis block, should only not have 'prevBlockHash' but says "+str(m)
        m.clear()
    else:
        if (len(m) == 0):
            if (block['prevBlockHash'] != m_Blocks[-1]['blockHash']):
                return "Block hash does not match previous block hash "
        else:
            return "Missing field(s): "+str(m)

    #TODO check the blocks time is greater than the last one
    # check the index of the block is correct, skip else and abort
    if (block['index'] == len(m_Blocks)):
        isCoinBase = True
        for trans in block['transactions']:
            ret = verifyBasicTX(trans,isCoinBase,m_staticTransactionRef)
            if (len(ret)>0):
                return ret
            isCoinBase = False
    return ""

def receivedNewTransaction(trans,fromPeer,share):
    # only basic checks so far, more needed
    # we must check that each field exists
    colErr = verifyBasicTX(trans,False,m_transaction) #such can never be coinbase, so False!

    if (colErr == ""):
        trx = deepcopy(trans)
        passOn = deepcopy(trans)
        del trx["senderSignature"]
        hasHash = False
        if ("transactionDataHash" in trans):
            compare = trans["transactionDataHash"]
            del trx["transactionDataHash"]
            hasHash = True

        hash = sha256ToHex(trx)
        if (hasHash and str(hash) != str(compare)):
            #TODO Wallet sends wrong format of transactionHash
            test = 0
            #return errMsg("Wrong transactionDataHash",400)
        trans["transactionDataHash"]=hash
        if hash in m_pendingTX:
            return errMsg("Duplicate TX received",400)
        ## need to check the date and the signature etc....
        #TODO For each received transaction the Node does the following:
        #TODO Checks for missing / invalid fields / invalid field values
        #Calculates the transaction data hash (unique transaction ID)
        #Checks for collisions  duplicated transactions are skipped
        #Validates the transaction public key, validates the signature
        #Checks the sender account balance to be >= value + fee
        #Checks whether value >= 0 and fee > 10 (min fee)
        #Puts the transaction in the "pending transactions" pool
        #Sends the transaction to all peer nodes through the REST API
        #It goes from peer to peer until it reaches the entire network

        m_pendingTX.update({trans['transactionDataHash']:deepcopy(trans)})
        trans["transferSuccessful"]= True
        trans["minedInBlockIndex"] = len(m_Blocks)
        m_candidateBlock['transactions'].append(deepcopy(trans))
        m_info['pendingTransactions'] = len(m_pendingTX)
        response = {
            "transactionDataHash": trans["transactionDataHash"],
            "Wallet": "sends TXHash in int instead of hex, so it is ignored...and should be removed!"
        }

        m_BufferMinerCandidates.clear()
        addrTo = trans['to']
        value = trans['value']
        total = value + trans['fee']
        #TODO update the checking balance maybe???
        #updatePendingBalance(addrTo,trans,len(m_Blocks),value)
        if (share):
            c_peer.sendAsynchPOSTToPeers("/transactions/send",passOn,fromPeer)
            return jsonify(response), 201 #201 as per slide 38
        return ""
    return errMsg(colErr,400)

def initPendingTX():
    if (firstTime[0] == True):
        firstTime[0] = False
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active'] == True):
                txList, ret = c_peer.sendGETToPeer(peer+"/transactions/pending")
                for tx in txList:
                    receivedNewTransaction(tx,"",False)
                break


