from project.models import *
from flask import jsonify
import time
import random
from project.utils import *
import hashlib
from copy import deepcopy
from project.nspec.blockchain.transact import transactions
from project.nspec.blockchain.blocks import blockchain
from project.nspec.blockchain.modelBC import *
from project.pclass import c_peer
from project.models import m_Miner_order

class blockChainNode:
    c_tx = transactions()
    c_blockchainHandler = blockchain()


    def bufferSys(self):
        sysout = {}
        sysout['m_info'] = m_info
        sysout['m_cfg'] = m_cfg
        sysout['m_peerInfo'] = m_peerInfo
        sysout['m_pendingTX'] = m_pending
        sysout['m_Blocks'] = m_Blocks
        sysout['m_BufferMinerCandidates'] = m_BufferMinerCandidates
        sysout['m_stats'] = m_stats
        sysout['balances'] = m_AllBalances #I save buffer for info, but it is not loaded
        return sysout


    def loadSys(self,sysIn):
        myUrl = m_info['nodeUrl']
        myNodeID = m_info['nodeId']
        m_info.clear()
        m_info.update(sysIn['m_info'])
        m_info["nodeUrl"]=myUrl
        m_info["nodeId"] = myNodeID
        m_cfg.clear()
        m_cfg.update(sysIn['m_cfg'])
        m_peerInfo.clear()
        m_peerInfo.update(sysIn['m_peerInfo'])
        m_Blocks.clear()
        m_AllBalances.clear()   # I don't load BalanceInfo form file as it is calculated on the fly
        for block in sysIn['m_Blocks']:
            if (len(m_Blocks) == 0):
                # TODO verify all fields are the same not only there!!!
                m, l, f = checkRequiredFields(block, m_genesisSet[0], [], False)
                if (len(m) == 0):
                    # TODO revert if loading failed!?!?!
                    m_Blocks.append(block)
                    continue
            else:
                ret = self.c_blockchainHandler.verifyThenAddBlock(block)
                if (len(ret) > 0):
                    # TODO revert if loading failed!?!?!
                    return jsonify(ret), 400

        m_pendingTX.clear()
        m_pendingTX.update(sysIn['m_pendingTX'])
        m_BufferMinerCandidates.clear()
        m_BufferMinerCandidates.update(sysIn['m_BufferMinerCandidates'])
        m_stats.update(sysIn['m_stats'])

    def getMinerCandidate(self, minerAddress):
        if minerAddress in m_BufferMinerCandidates:
            cand = m_BufferMinerCandidates[minerAddress]
            if cand['index'] == m_candidateBlock['index']:
                cand['countRepeat'] = cand['countRepeat'] + 1
                ### If there is no solution and no miner can find a solution, then unless a new tx
                ### comes in the network hangs, so need to limit the number of reuse here and change the timestamp
                if (cand['countRepeat']<5):
                    cand2 = deepcopy(cand)
                    del cand2['countRepeat']
                    return jsonify(cand2), 200 #if nothing has changed, return same block

        candidateMiner = deepcopy(m_candidateMiner)
        candidateMiner['rewardAddress'] = minerAddress
        m_candidateBlock['minedBy'] = minerAddress
        fees = 0
        for tx in m_candidateBlock['transactions']:
            if (len(tx) >0):    #otherwise it is empty coinbase
                fees = fees + tx['fee']
            else:
                if (fees>0):
                    errMsg("Invalid empty TX in block", 404)
        candidateMiner['index'] = len(m_Blocks) #m_candidateBlock['index']
        candidateMiner['expectedReward'] = candidateMiner['expectedReward'] +fees
        coinBase = deepcopy(m_coinBase)
        coinBase['to'] = minerAddress
        coinBase['dateCreated'] = getTime()
        coinBase['value'] = candidateMiner['expectedReward']
        coinBase['minedInBlockIndex'] = len(m_Blocks)
        coinBase['transactionDataHash'] = sha256ToHex(m_transaction_order, coinBase)
        m_candidateBlock['transactions'][0] = coinBase #just overwrite first TX, miner gets money for empty as well
        candidateMiner['transactionsIncluded'] = len(m_candidateBlock['transactions']) #inlcudes coinbase
        # now the block is done, hash it for miner
        # need to calculate now the hash for this specific miner based candidateBlock
        # the hash for the miner has to be in specific order of data
        forHash = "{"
        for txs in m_candidateMiner_order:
            if (txs == 'transactions'):
                forHash = forHash + '"' + txs + '":['
                for tx in m_candidateBlock['transactions']:
                    forHash = forHash + putDataInOrder(m_txorderForBlockHash, tx)
                forHash = forHash + "],"
            else:
                forHash = forHash + addItems(txs, m_candidateBlock[txs])
        candidateMiner['blockDataHash'] = sha256StrToHex(forHash[:-1] + "}")
        print("Generate new candidate for miner: " + minerAddress + " with " + candidateMiner['blockDataHash'])
        m_BufferMinerCandidates[minerAddress] = deepcopy(candidateMiner)
        m_BufferMinerCandidates[minerAddress]['countRepeat'] = 0
        return jsonify(candidateMiner), 200

    def minerFoundSolution(self,minerSolution):
        # TODO we must check it all
        #{"blockDataHash": "15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
        # "dateCreated": "2018-05-20T04:36:36Z", "nonce": "735530",
        # "blockHash": "0000020135f1c30b68733e9805f52fdc758fff4b07149929edbd995d30167ae1"}
        colErr = checkSameFields(minerSolution,m_minerFoundNonce,True)
        if (colErr != ""):
            return errMsg(colErr, 400)
        for minerAddress in m_BufferMinerCandidates:
            known = m_BufferMinerCandidates[minerAddress]
            if known['blockDataHash'] == minerSolution['blockDataHash']:
                sol = minerSolution['blockHash']
                dif = known['difficulty']
                fail = (len(sol) < dif) or (sol[:dif] != ("0" * dif))
                if (fail):
                    return errMsg("Submitted block hash does not fulfill difficulty ", 400)

                # calculate hash based on nonce and then compare
                blockHash = makeMinerHash(minerSolution)
                if (blockHash != minerSolution['blockHash']):
                    return errMsg("Incorrect block hash", 400)

                # TODO timestamp must be bigger than when the candidate was sent, nut
                # TODO timestap cannot be too far into the future, maybe allow 1 minute?

                # TODO is this double updtae with minerdareCreated to TX and block creation correct???
                m_candidateBlock['transactions'][0]['dateCreated'] = minerSolution['dateCreated']
                m_candidateBlock['transactions'][0]['to'] = minerAddress
                m_candidateBlock['minedBy'] = minerAddress
                m_candidateBlock['blockHash'] = minerSolution['blockHash']
                m_candidateBlock['nonce'] = minerSolution['nonce']
                m_candidateBlock['dateCreated'] = minerSolution['dateCreated']
                err = self.c_blockchainHandler.verifyThenAddBlock(m_candidateBlock)
                if (len(err) > 0):
                    return errMsg("Internal error on setting up block",400)
                toPeer = dict(m_informsPeerNewBlock)
                toPeer["blocksCount"] = len(m_Blocks)
                toPeer["cumulativeDifficulty"] = 55 # TODO this still need to be counted
                toPeer["nodeUrl"] = m_info['nodeUrl']
                c_peer.sendAsynchPOSTToPeers("peers/notify-new-block", toPeer, "")
                return setOK("Block accepted, reward paid: "+str(known['expectedReward'])+" microcoins")

        #TODO call errMsg
        #TODO confirm
        #After a new block is mined in the network (by someone)
        #All pending mining jobs are deleted (because are no longer valid)
        #When a miner submits a mined block later  404 "Not Found"

        return errMsg("Block not found or already mined", 404)


