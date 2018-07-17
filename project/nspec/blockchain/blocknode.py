from project.utils import checkRequiredFields, errMsg, setOK, sha256ToHex, checkSameFields
from project.utils import makeMinerHash, getTime, makeBlockDataHash
from project.nspec.blockchain.transact import transactions
from project.nspec.blockchain.blocks import blockchain
from project.nspec.blockchain.modelBC import m_genesisSet, m_candidateBlock, m_candidateMiner
from project.nspec.blockchain.modelBC import m_informsPeerNewBlock, m_coinBase, m_minerFoundNonce
from project.nspec.blockchain.modelBC import minBlockReward, maxSameBlockPerMiner
from project.nspec.blockchain.modelBC import m_pendingTX, m_AllBalances, m_BufferMinerCandidates, m_stats, m_Blocks
from project.models import m_info, m_peerInfo, m_transaction_order
from project.models import m_cfg
from project.pclass import c_peer
from copy import deepcopy

class blockChainNode:
    c_tx = transactions()
    c_blockchainHandler = blockchain()

    def bufferSys(self):
        sysout = {}
        sysout['m_info'] = m_info
        sysout['m_cfg'] = m_cfg
        sysout['m_peerInfo'] = m_peerInfo
        sysout['m_pendingTX'] = m_pendingTX
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
        m_info["nodeUrl"] = myUrl
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
                    return errMsg(ret)

        m_pendingTX.clear()
        m_pendingTX.update(sysIn['m_pendingTX'])
        m_BufferMinerCandidates.clear()
        m_BufferMinerCandidates.update(sysIn['m_BufferMinerCandidates'])
        m_stats.update(sysIn['m_stats'])

    def getMinerCandidate(self, minerAddress):
        #TODO share same block for different miner later on to save memory
        if minerAddress in m_BufferMinerCandidates:
            cand = m_BufferMinerCandidates[minerAddress]['mineCandidate']
            if cand['index'] == m_candidateBlock['index']:
                if m_BufferMinerCandidates[minerAddress]['minerBlock']['blockDataHash'] == m_candidateBlock['blockDataHash']:
                    ##m_BufferMinerCandidates[minerAddress]['countRepeat'] = m_BufferMinerCandidates[minerAddress]['countRepeat'] + 1
                    ### If there is no solution and no miner can find a solution, then unless a new tx
                    ### comes in the network hangs, so need to limit the number of reuse here and change the timestamp
                    ##if m_BufferMinerCandidates[minerAddress]['countRepeat'] < maxSameBlockPerMiner:
                    ##    return setOK(cand) #if nothing has changed, return same block

                    return setOK(cand)  # if nothing has changed, return same block
        # as candidate blocks change with every new TX and different miners might deal
        # with different blocks, we must keep the miner specific block in case the
        # miner succeeds
        minerSpecificBlock = deepcopy(m_candidateBlock)
        # TODO need house-keeping if miners disappear and don't come back,
        # else we get a queue overflow attack by fake miners
        candidateMiner = deepcopy(m_candidateMiner)
        candidateMiner['rewardAddress'] = minerAddress
        minerSpecificBlock['minedBy'] = minerAddress
        fees = minBlockReward
        for tx in m_candidateBlock['transactions']:
            if len(tx) > 0:    #otherwise it is empty coinbase
                fees = fees + tx['fee']
            else:
                if fees != minBlockReward:
                    return errMsg("Invalid minimum CoinBase fee TX in block", 404)
        coinBase = deepcopy(m_coinBase)
        candidateMiner['index'] = len(m_Blocks)
        coinBase['minedInBlockIndex'] = len(m_Blocks)
        candidateMiner['expectedReward'] = fees
        coinBase['value'] = fees
        coinBase['to'] = minerAddress
        coinBase['dateCreated'] = getTime()
        coinBase['transactionDataHash'] = sha256ToHex(m_transaction_order, coinBase)
        minerSpecificBlock['transactions'][0] = coinBase #just overwrite first TX, miner gets money for empty as well
        candidateMiner['transactionsIncluded'] = len(minerSpecificBlock['transactions']) #inlcudes coinbase
        # now the block is done, hash it for miner
        # need to calculate now the hash for this specific miner based candidateBlock
        # the hash for the miner has to be in specific order of data

        candidateMiner['blockDataHash'] = makeBlockDataHash(m_candidateBlock, False)
        print("Generate new candidate for miner: " + minerAddress + " with Hash: " + candidateMiner['blockDataHash'] + " reward: " + str(fees))
        m_BufferMinerCandidates[minerAddress] = {}
        m_BufferMinerCandidates[minerAddress]['mineCandidate'] = deepcopy(candidateMiner)
        m_BufferMinerCandidates[minerAddress]['minerBlock'] = minerSpecificBlock
        return setOK(candidateMiner)


    def minerFoundSolution(self, minerSolution):
        colErr = checkSameFields(minerSolution, m_minerFoundNonce, True)
        if colErr != "":
            return errMsg(colErr)

        #miner does not say who he is, so need to find the match in blockDataHash
        #which includes the correct address
        minerAddress = ""
        for miner in m_BufferMinerCandidates:
            if m_BufferMinerCandidates[miner]['mineCandidate']['blockDataHash'] == minerSolution['blockDataHash']:
                    minerAddress = miner
                    #make copy to avoid parallel changes through bad/new miner request
                    known = deepcopy(m_BufferMinerCandidates[minerAddress]['mineCandidate'])
                    minerSpecificBlock = deepcopy(m_BufferMinerCandidates[minerAddress]['minerBlock'])
                    break

        if len(minerAddress) == 0:
            return errMsg("Block not found or already mined", 404)

        try:
            sol = minerSolution['blockHash']
            dif = known['difficulty']
            if (len(sol) < dif) or (sol[:dif] != ("0" * dif)):
                return errMsg("Submitted block hash does not fulfill difficulty ")

            # calculate hash based on nonce and then compare
            blockHash = makeMinerHash(minerSolution)
            if (blockHash != minerSolution['blockHash']):
                return errMsg("Incorrect block hash")


            # TODO timestamp must be bigger than when the candidate was sent, nut
            # TODO timestap cannot be too far into the future, maybe allow 1 minute?

            # this was the right, and no matter what comes now or was registered since we
            # found it, every miner must now start newly, because the block is gone
            m_BufferMinerCandidates.clear()

            minerSpecificBlock['transactions'][0]['dateCreated'] = minerSolution['dateCreated']
            minerSpecificBlock['transactions'][0]['to'] = minerAddress
            minerSpecificBlock['blockHash'] = minerSolution['blockHash']
            minerSpecificBlock['nonce'] = minerSolution['nonce']
            minerSpecificBlock['dateCreated'] = minerSolution['dateCreated']
            minerSpecificBlock['blockDataHash'] = minerSolution['blockDataHash']
            err = self.c_blockchainHandler.verifyThenAddBlock(minerSpecificBlock)
            if len(err) > 0:
                colErr = "Internal error on setting up block"
                minerAddress=""
            else:
                toPeer = deepcopy(m_informsPeerNewBlock)
                toPeer["blocksCount"] = len(m_Blocks)
                toPeer["cumulativeDifficulty"] = 55 # TODO this still need to be counted
                toPeer["nodeUrl"] = m_info['nodeUrl']
                c_peer.sendAsynchPOSTToPeers("peers/notify-new-block", toPeer, "")
        except Exception:
            colErr = colErr + " and grave error encountered"

        # this was the right, and no matter what else happened or comes now or was registered since we
        # found it, every miner must now start newly, because the block is gone, so
        # if since previous clear another one registered, clear all again and start anew
        m_BufferMinerCandidates.clear()

        if len(minerAddress) > 0:
            return setOK("Block accepted, reward paid: "+str(known['expectedReward'])+" microcoins")

        return errMsg(colErr)



