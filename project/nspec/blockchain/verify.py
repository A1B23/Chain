from project.utils import checkRequiredFields, errMsg, sha256ToHex
from project.nspec.blockchain.modelBC import m_stats, m_completeBlock, m_Blocks, m_staticTransactionRef
from project.nspec.blockchain.modelBC import m_transaction, m_candidateBlock, m_pendingTX, m_BufferMinerCandidates
from project.pclass import c_peer
from project.nspec.wallet.transactions import get_public_address_from_publicKey
from project.models import re_addr, re_pubKey, defAdr, defPub, defSig,m_transaction_order, m_cfg, m_info
from copy import deepcopy
from flask import jsonify


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
        else:
            if (len(trans['senderSignature'][0]) != len(trans['senderSignature'][0])) or\
                    (len(trans['senderSignature'][0]) != len(defSig)):
                    colErr = colErr + " Invalid 'senderSignature' length"
            else:
                if isCoinBase is True:
                    if (trans['senderSignature'][0] != defSig) or (trans['senderSignature'][1] != defSig):
                        colErr = colErr + "Invalid senderSignature"
                else:
                    if (trans['senderSignature'][0] == defSig) or (trans['senderSignature'][1] == defSig):
                        colErr = colErr + "Invalid senderSignature"
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
        # slide 39 confirm that 0 value transactions are allowed
        if (trans['value'] < 0):
            colErr = colErr + "Minimum value 0 micro-coins, you sent: " + str(trans['value'])
    if isCoinBase is True:
        # TODO complete other coinbase checks
        colErr = colErr + verifyPubKey(trans['senderPubKey'], True)
        if trans['from'] != defAdr:
            colErr = colErr + "Invalid from in Coinbase"
    else:
        colErr = colErr + verifyAddr(trans['from'], trans['senderPubKey'])
    colErr = colErr + verifyAddr(trans['to'])

    return colErr

def isUniqueTXInBlocks(hash):
    #As there is no reliable element to prevent replay attacks, we must scan entire chain
    # to check a TX has never been used before
    for b in m_Blocks:
        for tx in b['transactions']:
            if (tx['transactionDataHash'] == hash):
                return False
    return True


def verifyAddr(addr, pubKey=""):
    #First is actually a duplicate of second pattern, but refines the reply
    if len(addr) != len(defAdr):
        return "Invalid address length"
    if addr == defAdr:
        return "Invalid address, all zero reserved for Genesis"
    if not re_addr.match(addr):
        return "Invalid address format"
    if len(pubKey) > 0:
        colErr = verifyPubKey(pubKey, False)
        if len(colErr) != 0:
            return colErr
        if (get_public_address_from_publicKey(pubKey) != addr):
            return "Invalid address-public key instance"
    return ""

def verifyPubKey(pubKey, isCoinBase):
    if len(pubKey) != len(defPub):
        return "Invalid public Key length"
    if pubKey == defPub:
        if isCoinBase is False:
            return "Invalid pubKey, all zero reserved for Genesis"
    else:
        if isCoinBase is True:
            return "Invalid pubKey, all zero reserved for Genesis"

    if not re_pubKey.match(pubKey):
        return "Invalid public key format"
    return ""


def verifyBlockAndAllTX(block, isGenesis):
    #make sure block has all fields an dthe corrcet chanId
    m, l, f = checkRequiredFields(block, m_completeBlock, ['chainId'], False)
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
        isCoinBase = True   #Setting otrue here ensures that there is at least a conbase there and not skipped
        for trans in block['transactions']:
            ret = verifyBasicTX(trans, isCoinBase, m_staticTransactionRef)
            #TODO add TX to block has!
            if (len(ret)>0):
                return ret #error case
            # we only ned to check block hashes as here we have no pending TXs
            if isUniqueTXInBlocks(trans['transactionDataHash']) == False:
                return "Duplicate TX detected"
            isCoinBase = isGenesis  #geneis block verification only has coinbase like entries

    return ""


def receivedNewTransaction(trans, share):
    # Checks for missing / invalid fields / invalid field values
    colErr = verifyBasicTX(trans, False, m_transaction) #such can never be coinbase, so False!

    if colErr == "":
        trx = deepcopy(trans)
        passOn = deepcopy(trans)
        del trx["senderSignature"]  # this must be excluded from the hash
        hash = sha256ToHex(m_transaction_order, trx)

        #TODO Validates the transaction public key, validates the signature
        trans["transactionDataHash"] = hash

        # Checks for collisions -> duplicated transactions are skipped
        if hash in m_pendingTX:
            return errMsg("TX is duplicate of in pending TX")

        if isUniqueTXInBlocks(hash) == False:
            return errMsg("TX is duplicate of TX in existing block")


        #Puts the transaction in the "pending transactions" pool
        m_pendingTX.update({trans['transactionDataHash']: deepcopy(trans)})
        trans["transferSuccessful"] = True
        trans["minedInBlockIndex"] = len(m_Blocks)
        m_candidateBlock['transactions'].append(deepcopy(trans))
        m_info['pendingTransactions'] = len(m_pendingTX)
        response = {"transactionDataHash": hash}

        m_BufferMinerCandidates.clear()
        if (share):
            # Sends the transaction to all peer nodes through the REST API
            # It goes from peer to peer until it reaches the entire network
            #TODO do we still need this 'fromPeer'?
            c_peer.sendAsynchPOSTToPeers("/transactions/send", passOn)
            return jsonify(response), 201 #201 as per slide 38
        return  # nothing returned, nothing sent
    return errMsg(colErr)


def initPendingTX():
    if (firstTime[0] == True):
        firstTime[0] = False
        #TODO do the same with sendingPeers
        for peer in m_cfg['activePeers']:
            if (m_cfg['activePeers'][peer]['active'] == True):
                txList, ret = c_peer.sendGETToPeer(peer+"/transactions/pending")
                for tx in txList:
                    receivedNewTransaction(tx,  False)
                break
