from flask import Flask, jsonify, request
from project.models import *
from project.nspec.blockchain.modelBC import *
from copy import deepcopy
from project.utils import d, checkRequiredFields, isSameChain
from project.nspec.blockchain.balance import addNewRealBalance
from project.pclass import c_peer
from project.nspec.blockchain.verify import *
from project.nspec.blockchain.balance import *
from threading import Thread


class blockchain:

    def setNetBasedOnChainID(self,id):
        # the id is the blochhash, so find the index and the
        useID = 1 #just default value
        self.resetChain()
        return

    def resetChainReply(self):
        self.resetChain()
        response = {
          "message": "The chain was reset to its genesis block"
        }
        return jsonify(response), 200

    def initChain(self):
        # TODO the genesis block TX is still missing in balances, which shows how many coins went to faucet!!!!
        m_Blocks.clear()
        if useNet == 0:
            m_info['about'] = "SoftUniChain/0.9-csharp"
        if useNet == 1:
            m_info['about'] = "NAPCoin"

        m_info['chainId'] = m_genesisSet[useNet]['blockHash']
        m_info['currentDifficulty'] = m_genesisSet[useNet]['difficulty']
        m_info['blocksCount'] = 1 # TODO I assume genesis block applies
        m_info['cumulativeDifficulty'] = m_info['currentDifficulty']
        m_info['confirmedTransactions'] = len(m_genesisSet[useNet]['transactions'])
        m_info['pendingTransactions'] = 0
        m_balHistory.clear()

        m_pendingTX.clear()
        m_AllBalances.clear()
        m_BufferMinerCandidates.clear()
        addNewRealBalance(defAdr,0)
        #m_Blocks.append(m_genesisSet[useNet])
        err = self.verifyThenAddBlock(m_genesisSet[useNet])
        if (len(err)>0):
            #TODO make sure this does not happen
            print("Ooops, it appears that the genesis Block is not correct, please fix... for test we continue despite "+err)
            m_Blocks.append(m_genesisSet[useNet])


    def resetChain(self):
        m_cfg['statusChain'] = True
        try:
            self.resetChainNow()
        except Exception:
            print("Seems no peers ready yet....")
        m_cfg['statusChain'] = False

    def resetChainNow(self):
        #TODO keep my blocks in buffer, because if hte other chains cannot
        #be verified or not longer, then revert to existing status

        self.initChain()
        allPeersInfo = c_peer.sendGETToPeers("info")
        ret = -1
        bestPeer=""
        while (ret != 200) and (len(allPeersInfo)>0):
            #some peers exists and may have blocks, so we follow them
            maxIdx = -1
            maxDiff =-1
            cnt = -1
            for detail, detail200 in allPeersInfo:
                cnt = cnt + 1
                if (detail200 != 200):
                    #TODO actually should remove!!!!
                    continue
                m, l, f = checkRequiredFields(detail, m_info, [],False)
                if (isSameChain(detail) and (len(m) ==0)):
                    if (maxDiff < detail['cumulativeDifficulty']):
                        maxDiff = detail['cumulativeDifficulty']
                        maxIdx = cnt
            if (maxIdx >= 0):
                bestPeer = allPeersInfo[maxIdx][0]['nodeUrl']
                #bestPeer = bestPeer[0]
                #bestPeer = bestPeer['nodeUrl']
                #navkov has wrong nodeUrl info, so change this to fix url is used in initargs!!!
                #bestPeer = 'https://stormy-everglades-34766.herokuapp.com'
                blockList, ret = c_peer.sendGETToPeer(bestPeer+"/blocks")
                if (ret == 200):
                    isFirst = True
                    for block in blockList:
                        if (isFirst):
                            #TODO compare block with my genesis
                            # if any verification fails, set ret to -1
                            isFirst = False
                            #cumDiff = cumDiff + block['difficulty']
                            m_info['cumulativeDifficulty']=block['difficulty']
                            continue
                        if (ret == 200):
                            if len(self.verifyThenAddBlock(block)) != 0:
                                self.initChain()
                                break
                        else:
                            self.initChain()
                            break
                    m_info['blocksCount'] = len(m_Blocks)
                    continue    #with ret being 200m, this ends the loop!!!
                del allPeersInfo[maxIdx]
                continue

            #TODO verify that the claimed block matched its advertisemnt in
            #TODO  blockscount, tx and cumulativeDifficulty!!
            #{"about": "SoftUniChain/0.9-csharp",
            # "nodeId": "1a22d3…9b2f", chainId: "c6da93eb…c47f",
            # "nodeUrl": "http://chain-node-03.herokuapp.com",
            # "peers": 2, "currentDifficulty": 5,
            # "blocksCount": 25, "cumulativeDifficulty": 127
            # "confirmedTransactions": 208, "pendingTransactions": 7
            # }


    def prepareNewCandidateBlock(self):
        m_candidateBlock.clear()
        m_candidateBlockBalance.clear()
        m_candidateBlock.update(deepcopy(m_static_emptyBlock)) #contains coinbase
        m_candidateBlock['index'] = len(m_Blocks)
        m_candidateBlock['prevBlockHash'] = m_Blocks[-1]['blockHash']
        m_BufferMinerCandidates.clear()

        #TODO add a maximum number for TX here
        for tx in m_pendingTX:
            m_candidateBlock['transactions'].append(tx)
        # TODO add all leftover transactions


    def getMissingBlocksFromPeer(self, base,peer):
        m_BufferMinerCandidates.clear()
        m_candidateBlockBalance.clear()
        while True:
            url = base + str(len(m_Blocks))
            res, stat = c_peer.sendGETToPeer(url)
            if (stat == 200):
                m, l, f = checkRequiredFields(res, m_genesisSet[0], [], False)
                if (len(m) == 0):
                    err = self.verifyThenAddBlock(res)
                    if (len(err)>0):
                        #TODO roll back por what?
                        return err
                    #TODO now we should inform all our peers about the block, apart form the one which sent
                    c_peer.sendAsynchPOSTToPeers("peers/notify-new-block", res,peer)
            else:
                # TODO must roll back or not?????
                return "No valid information, disconnect..."
            if(len(m_Blocks)>=res['index']):
                break
           # TODO now asynch we must send the new blocks to all peers for info?
        # TODO cleear up pending transactions
        # clear the separate flag for block other GETS
        return ""

    #TODO should this be replaced with verifyThenAddBlock??
    def receivedBlockNotificationFromPeer(self, blockInfo):
        m, l, f = checkRequiredFields(blockInfo, m_informsPeerNewBlock, [],False)
        if (len(m) == 0) and (l == 0):
            if (blockInfo['blocksCount']<len(m_Blocks)):
                return errMsg("Chain shorter than current, current is:" +str(len(m_Blocks)), 400)
            if (blockInfo['blocksCount'] == len(m_Blocks)):
                if (blockInfo['cumulativeDifficulty'] < m_stats['m_cumulativeDifficulty']):
                    return errMsg("Chain difficulty lower current, current is:" + str(m_stats['m_cumulativeDifficulty']), 400)
                elif (blockInfo['cumulativeDifficulty'] == m_stats['m_cumulativeDifficulty']):
                    # Note: we ignore timestamp and use the other criterioa to settle
                    # TODO first compare the length of TX, longer wins
                    # TODO else compare the value involved
                    # if still not then just let the future decideor what to resolve direct conflict?
                    return errMsg("Chain difficulty equal current, current is:" + str(m_stats['m_cumulativeDifficulty']), 400)
                else:
                    keepBlock = m_Blocks[len(m_Blocks)-1] #keep for potential roll back!
                    del m_Blocks[len(m_Blocks)-1]

            base = blockInfo['nodeUrl']
            url=base
            if (base[-1] != "/"):
                  base = base+"/"
            base = base + "blocks/"
            shareToPeers = len(m_Blocks)    # start point
            #TODO keep POST lock now active with a separate flag!!!
            #TODO make sure that threading does not create issues later
            #but as of now it is better to ack first the notification and then
            #start assking for blocks, as there could be more than one
            threadx = Thread(target=self.getMissingBlocksFromPeer, args=(base,url))
            threadx.start()
            return setOK("Thank you for the notification.")
        else:
            return errMsg("Invalid block structure", 400)


    def verifyThenAddBlock(self, block):
        #check structure of block and TX, but not yet the balances
        err = verifyBlockAndAllTX(block)
        if (len(err)) > 0:
            return err

        #structures are all corrcet so now check balances and update them
        err = confirmUpdateBalances(block['transactions'], block['index'])
        if (len(err) > 0):
            return err
        # clear all transactions involved in the block
        m_Blocks.append(deepcopy(block))
        # get urlblocks
        # clear the transaction in the block for ours
        self.prepareNewCandidateBlock()
        m_info['currentDifficulty'] = 5 #TODO shall we make the new difficulty flexible??? is hti sthe right place?
        m_info['blocksCount'] = len(m_Blocks)
        m_info['cumulativeDifficulty'] = m_info['cumulativeDifficulty'] + block['difficulty']
        m_info['confirmedTransactions'] = m_info['confirmedTransactions'] + len(block['transactions'])
        m_info['pendingTransactions'] = len(m_pendingTX)
        return ""

    def getBlockByNumber(self, blockNr):
        if (blockNr >= 0):
            if (blockNr < len(m_Blocks)):
                #TODO first we assume blockID equals bolckID as we simplify this
                # nonethe less should we check the index in the block matches the outside??
                # if no then how????
                return m_Blocks[blockNr]
        return{}

    def getJSONBlockByNumber(self, blockNr):
        blk = self.getBlockByNumber(blockNr)
        if (len(blk) > 0):
            return jsonify(blk), 200
        response = {
            'errorMsg': 'BlockNumber not valid or not existent: '+str(blockNr)
        }
        return jsonify(response), 400
