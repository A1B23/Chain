from project.utils import *
from project.nspec.blockchain.modelBC import *
from project.pclass import c_peer
from project.nspec.blockchain.balance import *


firstTime = [True]
def verifyBasicTX(trans, isCoinBase, ref):
    m, l, f = checkRequiredFields(trans, ref, [], False)
    colErr = ""
    for x in m:
        if colErr == "":
            colErr = "Missing field(s): '" + x + "'"
        else:
            colErr = colErr + "and '" + x + "'"
    if l != 0:
        # TODO test only still unclear about data structure so for test accept both
        if (l != 1) or ("transactionDataHash" not in trans):
            colErr = colErr + " Invalid number of fields in transaction"
    if colErr == "":  # final checks
        if (len(trans['senderSignature']) != 2):
            colErr = colErr + " Invalid number of elements in 'senderSignature' field"
        #TODO check senderSigLengths
    if not isinstance(trans['fee'], int):
        colErr = colErr + "Fees must be integer, you sent: " + str(trans['fee'])
    else:
        if isCoinBase is True:
            if trans['fee'] != 0:
                colErr = colErr + "Coinbase fee should be zero, you sent: " + str(trans['fee'])
        else:
            if trans['fee'] < m_stats['m_minFee']:
                colErr = colErr + "Minimun fee 10 micro-coins, you sent: " + str(trans['fee'])
    if not isinstance(trans['value'], int):
        colErr = colErr + "Value must be integer, you sent: " + str(trans['value'])
    else:
        #TODO confirm that 0 value transactions are allowed per slides
        if (trans['value'] < 0):
            colErr = colErr + "Minimun value 0 micro-coins, you sent: " + str(trans['value'])
    if (len(trans['from']) != len(trans['to'])) or (len(trans['from']) != defAdr):
        colErr = colErr + "Invalid from/to address length"
    return colErr



def verifyBlockAndAllTX(block):
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

    #TODO check the hash of the blockhash!
    #blockHash = sha256ToHex(m_Miner_order, block) or use the update as we need to inlccude each TX below!!!

    #TODO check the blocks time is greater than the last one
    # check the index of the block is correct, skip else and abort
    if (block['index'] == len(m_Blocks)):
        isCoinBase = True
        for trans in block['transactions']:
            ret = verifyBasicTX(trans, isCoinBase, m_staticTransactionRef)
            #TODO add TX to block has!
            if (len(ret)>0):
                return ret
            isCoinBase = False
    return ""

def receivedNewTransaction(trans, fromPeer, share):
    # Checks for missing / invalid fields / invalid field values
    colErr = verifyBasicTX(trans, False, m_transaction) #such can never be coinbase, so False!

    if colErr == "":
        trx = deepcopy(trans)
        passOn = deepcopy(trans)
        del trx["senderSignature"]  # this must be excluded from the hash
        hash = sha256ToHex(m_transaction_order, trx)

        #TODO Validates the transaction public key, validates the signature
        # valid = verify(generator_secp256k1, pub_key, tran_hash, tran_signature)
        # print("Is signature valid? " + str(valid))

        # Calculates the transaction data hash (unique transaction ID)
        trans["transactionDataHash"]= hash

        # Checks for collisions -> duplicated transactions are skipped
        if hash in m_pendingTX:
            return errMsg("Duplicate TX received",400)

        #TODO Checks the sender account balance to be >= value + fee
        #TODO Checks whether value >= 0 and fee > 10 (min fee)

        #Puts the transaction in the "pending transactions" pool
        m_pendingTX.update({trans['transactionDataHash']:deepcopy(trans)})
        trans["transferSuccessful"]= True
        trans["minedInBlockIndex"] = len(m_Blocks)
        m_candidateBlock['transactions'].append(deepcopy(trans))
        m_info['pendingTransactions'] = len(m_pendingTX)
        response = {"transactionDataHash": hash}

        m_BufferMinerCandidates.clear()
        if (share):
            # Sends the transaction to all peer nodes through the REST API
            # It goes from peer to peer until it reaches the entire network
            #TODO do we still need this 'fromPeer'?
            c_peer.sendAsynchPOSTToPeers("/transactions/send", passOn, fromPeer)
            return jsonify(response), 201 #201 as per slide 38
        return #nothing returmed, nothing sent
    return errMsg(colErr, 400)


def initPendingTX():
    if (firstTime[0] == True):
        firstTime[0] = False
        for peer in m_cfg['peers']:
            if (m_cfg['peers'][peer]['active'] == True):
                txList, ret = c_peer.sendGETToPeer(peer+"/transactions/pending")
                for tx in txList:
                    receivedNewTransaction(tx, "", False)
                break
