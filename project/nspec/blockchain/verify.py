from project.utils import checkRequiredFields, errMsg, sha256ToHex, d
from project.nspec.blockchain.modelBC import m_stats, m_completeBlock, m_Blocks, m_staticTransactionRef
from project.nspec.blockchain.modelBC import m_transaction, m_candidateBlock, m_pendingTX, m_BufferMinerCandidates
from project.nspec.blockchain.balance import updateTempBalance, getBalance
from project.pclass import c_peer
from project.nspec.wallet.transactions import get_public_address_from_publicKey
from project.models import re_addr, re_pubKey, defAdr, defPub, defSig, m_transaction_order, m_cfg, m_info
from project.utils import setOK
from copy import deepcopy

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
        # only for cases of rejected TX we need to additionally check the two separate fields
        if (l != 2):
            colErr = colErr + " Invalid number of fields in transaction: " + str(l) + str(trans)
        else:
            if ("transferSuccessful" not in trans) or ("transactionDataHash" not in trans):
                colErr = colErr + " Problem with TX successfulField " + str(trans)
            else:
                l = 0  # not used so far, but prepare for any changes later
    if colErr == "":  # final checks
        if len(trans['senderSignature']) != 2:
            colErr = colErr + " Invalid number of elements in 'senderSignature' field"
        else:
            # len0 = len(trans['senderSignature'][0])
            # len1 = len(trans['senderSignature'][1])
            # len2 = len(defSig)
            if (len(trans['senderSignature'][0]) != len(trans['senderSignature'][1])) or\
                    (len(trans['senderSignature'][0]) != len(defSig)):
                    colErr = colErr + " Invalid/Unpadded 'senderSignature' length"
            else:
                if isCoinBase:
                    if (trans['senderSignature'][0] != defSig) or (trans['senderSignature'][1] != defSig):
                        colErr = colErr + "Invalid senderSignature"
                else:
                    if (trans['senderSignature'][0] == defSig) or (trans['senderSignature'][1] == defSig):
                        colErr = colErr + "Invalid senderSignature"
    if not isinstance(trans['fee'], int):
        colErr = colErr + "Fees must be integer, you sent: " + str(trans['fee'])
    else:
        if isCoinBase:
            if trans['fee'] != 0:
                colErr = colErr + "Coinbase fee should be zero, you sent: " + str(trans['fee'])
        else:
            if trans['fee'] < m_stats['m_minFee']:
                colErr = colErr + "Minimun fee 10 micro-coins, you sent: " + str(trans['fee'])
    if not isinstance(trans['value'], int):
        colErr = colErr + "Value must be integer, you sent: " + str(trans['value'])
    else:
        # slide 39 confirm that 0 value transactions are allowed
        if trans['value'] < 0:
            colErr = colErr + "Minimum value 0 micro-coins, you sent: " + str(trans['value'])
    if isCoinBase:
        # TODO any other coinbase checks
        colErr = colErr + verifyPubKey(trans['senderPubKey'], True)
        if trans['from'] != defAdr:
            colErr = colErr + "Invalid from in Coinbase"
    else:
        colErr = colErr + verifyAddr(trans['from'], trans['senderPubKey'])
    colErr = colErr + verifyAddr(trans['to'])

    if len(colErr) > 0:
        d("Verification problem: "+colErr)
    return colErr


def isUniqueTXInBlocks(hash):
    # As there is no reliable element to prevent replay attacks, we must scan entire chain
    # to check a TX has never been used before
    for b in m_Blocks:
        for tx in b['transactions']:
            if (tx['transactionDataHash'] == hash):
                return False
    return True


def verifyAddr(addr, pubKey = ""):
    # First is actually a duplicate of second pattern, but refines the reply
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
        if get_public_address_from_publicKey(pubKey) != addr:
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


def verifyBlockAndAllTX(block):
    if block['index'] != len(m_Blocks):
        return "New block cannot be added to chain, wrong index: "
    return verifyBlockAndAllTXOn(block, True)


def verifyBlockAndAllTXOn(block, checkUnique):
    # make sure block has all fields and the correct chanId
    m, l, f = checkRequiredFields(block, m_completeBlock, ['chainId'], False)
    isGenesis = (block['index'] == 0)
    if isGenesis:
        # special case for genesis bloc
        if (len(m) != 1) or (m[0] != "prevBlockHash") or (l != -1) or (len(f) > 0):
            return "Invalid Genesis block, should only not have 'prevBlockHash' but says "+str(m)
    else:
        if len(m) == 0:
            if block['prevBlockHash'] != m_Blocks[block["index"]-1]['blockHash']:
                return "Block hash does not match previous block hash "
        else:
            return "Missing field(s): "+str(m)

        if (l != 0) or (len(f) > 0):
            return "Invalid block fields"

    #TODO check the hash of the blockhash!
    #blockHash = sha256ToHex(m_Miner_order, block) or use the update as we need to inlccude each TX below!!!


    isCoinBase = True   # Setting true here ensures that there is at least a coinbase there and not skipped
    for trans in block['transactions']:
        ret = verifyBasicTX(trans, isCoinBase, m_staticTransactionRef)
        #TODO add TX to block has!
        if (len(ret)>0):
            return ret
        # we only ned to check block hashes as here we have no pending TXs
        if (checkUnique is True) and (isUniqueTXInBlocks(trans['transactionDataHash']) is False):
            return "Duplicate TX detected"
        isCoinBase = isGenesis  # genesis block verification only has coinbase like entries

    return ""


def receivedNewTransaction(trans, share):
    # Checks for missing / invalid fields / invalid field values
    colErr = verifyBasicTX(trans, False, m_transaction)  # such can never be coinbase, so False!

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

        if isUniqueTXInBlocks(hash) is False:
            return errMsg("TX is duplicate of TX in existing block")
        if ('transferSuccessful' not in trans) or (trans['transferSuccessful'] is True):
            tmpBal = getBalance(trans['from'])
            if tmpBal['confirmedBalance'] + tmpBal['pendingBalance'] < trans['value']+trans['fee']:
                return errMsg("Not enough balance")

        # Puts the transaction in the "pending transactions" pool
        m_pendingTX.update({trans['transactionDataHash']: deepcopy(trans)})
        if "transferSuccessful" not in trans:
            trans["transferSuccessful"] = True
        trans["minedInBlockIndex"] = len(m_Blocks)
        m_candidateBlock['transactions'].append(deepcopy(trans))
        m_info['pendingTransactions'] = len(m_pendingTX)
        response = {"transactionDataHash": hash}

        m_BufferMinerCandidates.clear()
        if share is True:
            # Sends the transaction to all peer nodes through the REST API
            # It goes from peer to peer until it reaches the entire network
            #TODO do we still need this 'fromPeer'?
            c_peer.sendAsynchPOSTToPeers("/transactions/send", passOn)
            return setOK(response, 201) #201 as per slide 38
        return  # nothing returned, nothing sent
    return errMsg(colErr)


def initPendingTX():
    if firstTime[0] is True:
        firstTime[0] = False
        #TODO do the same with sendingPeers
        for peer in m_cfg['activePeers']:
            if m_cfg['activePeers'][peer]['active'] is True:
                txList, ret = c_peer.sendGETToPeer(peer+"/transactions/pending")
                for tx in txList:
                    receivedNewTransaction(tx,  False)
                break
