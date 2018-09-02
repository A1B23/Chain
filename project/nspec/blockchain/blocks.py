from project.nspec.blockchain.verify import verifyBlockAndAllTX, verifyBlockAndAllTXOn
from project.nspec.blockchain.balance import m_AllBalances, confirmUpdateBalances, confirmRevertBalances
from project.nspec.blockchain.balance import updateTempBalance, setBalanceTo
from threading import Thread
from project.models import useNet, m_info, m_cfg
from project.nspec.blockchain.modelBC import m_Blocks, m_genesisSet, m_candidateBlock, m_pendingTX, m_BufferMinerCandidates
from project.nspec.blockchain.modelBC import m_informsPeerNewBlock, m_balHistory, m_static_emptyBlock
from project.utils import checkRequiredFields, isSameChain, setOK, errMsg, sha256StrToHex, d
from project.models import defHash
from project.pclass import c_peer
from copy import deepcopy
import sys
from time import sleep


class blockchain:
    status = {'getMissingBlocks': False}

    def resetChainReply(self):
        self.resetChain()
        response = {
          "message": "The chain was reset to its genesis block"
        }
        return setOK(response)

    def clearChainLoadGenesis(self):
        m_cfg['chainLoaded'] = False
        m_Blocks.clear()
        m_balHistory.clear()
        m_pendingTX.clear()
        m_AllBalances.clear()
        m_BufferMinerCandidates.clear()

        m_info['chainId'] = m_genesisSet[useNet]['blockHash']
        m_info['currentDifficulty'] = m_genesisSet[useNet]['difficulty'] #TODO correct??? or hard coded 5 to start?
        m_info['blocksCount'] = 1
        m_info['cumulativeDifficulty'] = 0
        m_info['confirmedTransactions'] = len(m_genesisSet[useNet]['transactions'])
        m_info['pendingTransactions'] = 0

        err = verifyBlockAndAllTX(m_genesisSet[useNet])
        if len(err) > 0:
            print("Ooops, it appears that the genesis Block is not correct, please fix...  "+err)
            sys.exit(-1)

        #the genesis block TX shows how many coins went to faucet and to donors
        err = confirmUpdateBalances(m_genesisSet[useNet]['transactions'], True)
        if len(err) > 0:
            print("Ooops, it appears that the genesis Block is not correct, please fix... " + err)
            sys.exit(-1)
        m_Blocks.append(deepcopy(m_genesisSet[useNet]))
        m_cfg['chainLoaded'] = True

    def initChain(self, onePeer="", fetchAll=False, hashFetch=False):
        self.clearChainLoadGenesis()

        if fetchAll is False:
            # get the blocks one by one, due to size or whatever (later maybe even only getting the hashes!
            threadx = Thread(target=self.getMissingBlocksFromPeer,args=(onePeer, -1, False, {}))
            threadx.start()
            return
        else:
            if hashFetch is True:
                allPeersInfo = c_peer.sendGETToPeers("blocks/hash/0/100/"+str(len(defHash))) #TODO how to detemine? use info first?
            else:
                self.getAllBlocksOneReadDirect()
        m_cfg['chainLoaded'] = True

    def resetChain(self):
        m_cfg['chainInit'] = True
        try:
            self.initChain("", True, False)
        except Exception:
            print("Seems no peers ready yet....")
        m_cfg['chainInit'] = False

    def getAllBlocksOneReadDirect(self):
        # coming here we are sure that we have back-up or nothing to loose!
        allPeersInfo = c_peer.sendGETToPeers("info")
        ret = -1

        while (ret != 200) and (len(allPeersInfo)>0):
            #some peers exists and may have blocks, so we follow them
            maxIdx = -1
            maxDiff = -1
            cnt = -1
            for detail, detail200 in allPeersInfo:
                cnt = cnt + 1
                if detail200 != 200:
                    #TODO actually should remove!!!!
                    continue
                m, l, f = checkRequiredFields(detail, m_info, [], False)
                if (isSameChain(detail) is True) and (len(m) == 0):
                    if maxDiff < detail['cumulativeDifficulty']:
                        maxDiff = detail['cumulativeDifficulty']
                        maxIdx = cnt
            if maxIdx >= 0:
                bestPeer = allPeersInfo[maxIdx][0]['nodeUrl']
                #bestPeer = bestPeer[0]
                #bestPeer = bestPeer['nodeUrl']
                blockList, ret = c_peer.sendGETToPeer(bestPeer+"/blocks")
                if ret == 200:
                    isFirst = True
                    for block in blockList:
                        if isFirst is True:
                            #TODO compare block with my genesis
                            # if any verification fails, set ret to -1
                            isFirst = False
                            m_info['cumulativeDifficulty'] = block['difficulty']
                            continue
                        if ret == 200:
                            if len(self.verifyThenAddBlock(block)) != 0:
                                self.clearChainLoadGenesis()
                                break
                        else:
                            self.clearChainLoadGenesis()
                            break
                    m_info['blocksCount'] = len(m_Blocks)
                    continue    # with ret being 200, this ends the loop!!!
                del allPeersInfo[maxIdx]
                continue

    def prepareNewCandidateBlock(self):
        m_candidateBlock.clear()
        m_candidateBlock.update(deepcopy(m_static_emptyBlock)) # contains coinbase
        bindex = len(m_Blocks)
        m_candidateBlock['index'] = bindex
        m_candidateBlock['prevBlockHash'] = m_Blocks[-1]['blockHash']
        m_BufferMinerCandidates.clear()

        #TODO add a maximum number for TX here
        m_candidateBlock['transactions'].clear()
        for txh in m_pendingTX:
            dx = deepcopy(m_pendingTX[txh])
            dx['minedInBlockIndex'] = bindex
            dx['transferSuccessful'] = True
            m_candidateBlock['transactions'].append(dx)

    def handleChainBackTracking(self, peer):
        try:
            ret = self.handleBackTracking(peer)
        except Exception:
            d("Major issue in backtracking, stopped back tracking")
            ret = errMsg("Exception raised, invalid peer claim")
        m_cfg['checkingChain'] = False
        return ret

    def balanceWrong(self):
        return errMsg(d("Oh oh, balances oif same chains are different, fork unrepairable"))

    def handleBackTracking(self, peer):
        # now we now there is a chain fork, as some hash link is different at the end of our chain
        # we may have no block yet, or the blocks are same index yet conflict hash, but ut was decided
        # by length of chain or by roll of dice that the other chain has won, if it can remain consistent
        # 1. find first/deepest different block by binary increased range
        knownDiffIdx = len(m_Blocks)-1
        srchLen = 1
        start = knownDiffIdx
        hlen = len(defHash)
        while True:
            fromBlock = start-srchLen
            if fromBlock < 0:
                fromBlock = 0
            url = "/blocks/hash/"+str(fromBlock)+"/"+str(fromBlock + srchLen-1)+"/0"
            try:
                res, stat = c_peer.sendGETToPeer(peer + url)
            except Exception:
                return errMsg(d("Unsupported block claimed "))

            if stat != 200:
                return errMsg(d("Unsupported/Invalid block claimed"))
            if len(res) != srchLen:
                return errMsg(d("Insufficient data received"))

            idx, hash = res[0]
            if (idx != fromBlock) or (len(hash) != hlen):
                return errMsg(d("Invalid answer to block: "+idx))
            if hash == m_Blocks[fromBlock]['blockHash']:
                break
            if fromBlock <= 0:
                return errMsg(d("Different chain must be assumed"))
            srchLen = srchLen * 2
            start = fromBlock

        # 2. find the first block which is different, big data would call for binary search....
        for indx in range(1, len(res)):
            idx, hash = res[indx]
            if len(hash) != hlen:
                return errMsg(d("Invalid answer to block: "+idx))
            if hash != m_Blocks[fromBlock+indx]['blockHash']:
                knownDiffIdx = fromBlock+indx
                break

        # 3. up to the different block, our balances must be equal else we are totally out of synch
        myBal = {}
        self.getBalanceFromToBlock(0, knownDiffIdx-1, myBal)
        try:
            yourBal, stat = c_peer.sendGETToPeer(peer + "/blockBalances/" + str(knownDiffIdx-1))
        except Exception:
            return errMsg(d("Unsupported blockBalance"))

        if stat != 200:
            return errMsg(d("Unsupported blockBalance"))

        if len(myBal) != len(yourBal):
            return self.balanceWrong()

        for chk in myBal:
            if (chk not in yourBal) or (myBal[chk] != yourBal[chk]):
                return self.balanceWrong()

        # 4. save current status in case the other chain has faults
        tempBlocks = m_Blocks[knownDiffIdx:]
        del m_Blocks[knownDiffIdx:]
        if len(m_pendingTX) > 0:
            tmpTx = m_pendingTX[0:]
            m_pendingTX.clear()
        setBalanceTo(myBal, knownDiffIdx-1)
        d("All saved and ok, no get all the blocks...")

        # TODO current difficult must be adjusted
        ret = self.getBlocksFromPeer(peer, -1, False, {}, 2, False)

        #TODO how to insert now the old pending TX, would be nice to not just skip them
        # but as a lot has changed, some may not be valid anymore, so need to test them
        if ret != "":
            # TODO arg, must restore
            return errMsg(d("Invalid blocks received, loading aborted"))

        return setOK("Thank you for the notification.")

    def asynchNotifyPeers(self):
        try:
            forPeer = deepcopy(m_informsPeerNewBlock)
            forPeer["blocksCount"] = len(m_Blocks)
            forPeer["cumulativeDifficulty"] = m_info['cumulativeDifficulty']
            forPeer["nodeUrl"] = m_info['nodeUrl']
            forPeer["blockHash"] = m_Blocks[-1]['blockHash']
            c_peer.sendAsynchPOSTToPeers("peers/notify-new-block", forPeer)
        except Exception:
            return

    def checkChainSituation(self, source, blockInfo):
        #We arrive here either because a block notification was sent,
        #or because our peer got an info claiming the peer has longer chain.
        # here we decide on the situation of whether blocks are simply added on top
        # or if something more compliucated is needed, e.g. go back the stack to find
        # common block and then recover shared TXs etc. etc.
        #These are shared among info and block notification
        #   "nodeUrl": sender
        #   "blocksCount": 25, "cumulativeDifficulty": 127
        # added by PDPCOin : blockHash for notification
        #only in info:
        #   "confirmedTransactions": 208
        try:
            d("checking status due to " + source)
            peer = blockInfo['nodeUrl']
            if blockInfo['blocksCount'] < len(m_Blocks):
                d("stay with local chain anyway as it is longer than for " + peer)
                self.asynchNotifyPeers()
                return errMsg("Notified chain shorter than local current, current is:" + str(len(m_Blocks)))
            if source == "notification":
                if 'blockHash' in blockInfo: #PDPCCoin specific shortcut
                    if blockInfo['blockHash'] == m_Blocks[-1]['blockHash']:
                        d("is the same, probably rebound...")
                        return setOK("Thank you for the notification.")
            while m_cfg['checkingChain'] is True:
                d("Already checking chain status, so complete the first one")
                #return errMsg("Please wait for current synchronisation to complete...")
                sleep(1)
            m_cfg['checkingChain'] = True

            if blockInfo['blocksCount'] == len(m_Blocks):
                d("blocks on par, check next step with "+peer)
                #this means we have conflict on the same top block, probably parallel mined
                if blockInfo['cumulativeDifficulty'] < m_info['cumulativeDifficulty']:
                    self.asynchNotifyPeers()
                    m_cfg['checkingChain'] = False
                    d("local difficulty higher, no change")
                    return errMsg("Peers chain cumulativeDifficulty lower than local current, current is:" + str(m_info['cumulativeDifficulty']))
                else:
                    # we have same height and same or lower difficulty, so we need to roll the dice for now
                    # based on hash
                    #get the actual block from peer
                    res, stat = self.getNextBlock(peer, -1)
                    if stat == 200:
                        # yoursbetter must not be based on the claim but based
                        # on the block data and its difficulty versus my cumulative
                        # else an attacker might cheat with high claim but low delivery
                        # 0) we ignore your cumDiff
                        # a) myDiff versus your blockDifficulty
                        # b) mycum-myDiff+yourDiff == your claimed cumDif
                        d("got peer block as requested with OK")
                        # We repeat the check here in case we had info instead of notification!
                        if res['blockHash'] == m_Blocks[-1]['blockHash']:
                            d("anyway the same")
                            m_cfg['checkingChain'] = False
                            return setOK("Thank you for the notification.")
                        # need to include difficulty in this decision
                        yoursBetter = blockInfo['cumulativeDifficulty'] > m_info['cumulativeDifficulty']
                        if yoursBetter is False:
                            yoursBetter = res['difficulty'] > m_Blocks[-1]['difficulty']
                        if yoursBetter is False:
                            d("same block difficulty")
                            #we are confirmed same same in all, so lets roll the deterministic dice
                            #by crossing the two inputs instead of checking umber of TX or value etc.,
                            #all of which could lead to easier rigging than dice
                            lstDice = ""
                            indexMy=0
                            indexYou=0
                            dice = "x"
                            xst = [res['blockDataHash'], m_Blocks[-1]['blockHash'], m_Blocks[-1]['blockDataHash'], res['blockHash']]
                            xst.sort()
                            for lst in xst:
                                lstDice = lstDice + lst
                            while indexMy == indexYou:
                                lstDice = lstDice+dice
                                d("roll the dice...")
                                dice = sha256StrToHex(lstDice)[0]
                                d("Dice value:"+str(dice))
                                indexMy = m_Blocks[-1]['blockHash'].index(dice)
                                indexYou = res['blockHash'].index(dice)
                                d(str(indexMy) + " vs " + str(indexYou))
                                if (indexYou > indexMy):
                                    yoursBetter = True
                            d("dice said yoursBetter :" + str(yoursBetter))
                        if yoursBetter is True:
                            if res['prevBlockHash'] != m_Blocks[-1]['prevBlockHash']:
                                d("hashes different need to settle backtrack")
                                return self.handleChainBackTracking(peer)
                            d("!!!we conceeded, add peers block from "+peer)
                            restor = m_Blocks[-1]
                            confirmRevertBalances(restor['transactions'])
                            del m_Blocks[-1]
                            err = self.checkAndAddBlock(res, True)
                            if len(err) > 0:
                               d("something was wrong, restore own previous block")
                               self.checkAndAddBlock(restor, True)
                               m_cfg['checkingChain'] = False
                               return errMsg("Invalid block received")
                        else:
                            self.asynchNotifyPeers()
                            d("local copy maintained after all")
                            i=0
                        m_cfg['checkingChain'] = False
                        return setOK("Thank you for the notification.")
                    m_cfg['checkingChain'] = False
                    d("The reply did not have the correct fields")
                    return errMsg("No proper reply, ignored")
            else:
                d("local chain appears shorter anyway, so just ask for up to block "+str(blockInfo['blocksCount']))
                # the peer claims to be ahead of us with at leats one block, so catch up until something happens
                # easy case just add the new block on top, and each block is checked fully, no backtrack
                res, stat = self.getNextBlock(peer, 0)
                if stat == 200:
                    # backtrack into the stack!!!
                    if res['prevBlockHash'] != m_Blocks[-1]['blockHash']:
                        d("hashes different need to settle backtrack")
                        return self.handleChainBackTracking(peer)
                    if source == 'notification':
                        d("Sender want a reply, so process")
                        err = self.getMissingBlocksFromPeer(blockInfo['nodeUrl'], blockInfo['blocksCount'], True, res)
                        m_cfg['checkingChain'] = False
                        if len(err) > 0:
                            return errMsg(err)
                        return setOK("Thank you for the notification.")
                    else:
                        d("this is info internal, so create thread and don't care result")
                        threadx = Thread(target=self.getMissingBlocksFromPeer, args=(blockInfo['nodeUrl'], blockInfo['blocksCount'], False, res))
                        threadx.start()
                m_cfg['checkingChain'] = False
                return errMsg("Invalid block received")  # for info this is ignored anyway
        except Exception:
            m_cfg['checkingChain'] = False
            return errMsg("Processing error occurred")

    def getNextBlock(self, peer, offset):
        if (len(peer) > 0) and (peer[-1] != "/"):
            peer = peer + "/"
        base = "blocks/"
        url = base + str(len(m_Blocks)+offset)
        try:
            res, stat = c_peer.sendGETToPeer(peer + url)
        except Exception:
            d("peer failed" + peer)
            return "Block not available at " + peer, -1  # do not change it is checked outside

        if stat == 200:
            d("got peer block as requested with OK")
            m, l, f = checkRequiredFields(res, m_genesisSet[0], [], False)
            if len(m) == 0:
                if res['index'] == len(m_Blocks)+offset:
                    return res, stat
        return "Block not available/valid at " + peer, -1  # do not chnage it is checked outside

    def getMissingBlocksFromPeer(self, peer, upLimit, isAlert, gotBlock, retry=2):
        return self.getBlocksFromPeer(peer,upLimit,isAlert,gotBlock,retry,True)

    def getBlocksFromPeer(self, peer, upLimit, isAlert, gotBlock, retry, isCheck):
        if isCheck and (self.status['getMissingBlocks'] is True):
            d("Already checking on missing blocks, return empty")
            return ""
        try:
            self.status['getMissingBlocks'] = True
            d("Work on missing block"+peer)
            while True:
                if (upLimit > 1) and (upLimit <= len(m_Blocks)):
                    self.status['getMissingBlocks'] = False
                    m_cfg['chainLoaded'] = True
                    m_cfg['checkingChain'] = False
                    return ""
                if len(gotBlock) > 0:
                    stat = 200
                    res = gotBlock
                    gotBlock = {}
                else:
                    res, stat = self.getNextBlock(peer, 0)
                if stat == 200:
                    if res['difficulty'] < m_info['currentDifficulty']:
                        m_cfg['checkingChain'] = False
                        return "Invalid difficulty in block detected"
                    err = self.checkAndAddBlock(res, isAlert)
                    if len(err) > 0:
                        m_cfg['chainLoaded'] = True
                        m_cfg['checkingChain'] = False
                        return "Invalid block received"
                else:
                    if stat == -1:  # special signal telling us no more blocks there
                        m_cfg['checkingChain'] = False
                        self.status['getMissingBlocks'] = False
                        return ""
                    retry = retry - 1 # maybe block has not spread well yet
                    if retry <= 0:
                        self.status['getMissingBlocks'] = False
                        m_cfg['chainLoaded'] = True
                        m_cfg['checkingChain'] = False
                        return "No valid information, stopped block updates."
        except Exception:
            self.status['getMissingBlocks'] = False
        m_cfg['checkingChain'] = False
        m_cfg['chainLoaded'] = (len(m_Blocks) > 0)
        return "Verification failed"

    def checkAndAddBlock(self, res, isAlert):
        err = self.verifyThenAddBlock(res)
        if len(err) > 0:
            self.status['getMissingBlocks'] = False
            return err
        # inform all our peers about the block
        m_BufferMinerCandidates.clear()
        if isAlert is True:
            self.asynchNotifyPeers()
        self.status['getMissingBlocks'] = False
        return ""

    def receivedBlockNotificationFromPeer(self, blockInfo):
        #TODO do we want to check if NodeUrl and real sender are identical??
        try:
            m, l, f = checkRequiredFields(blockInfo, m_informsPeerNewBlock, [], False)
            if (len(m) == 0) and (l == 0):
                return self.checkChainSituation('notification', blockInfo)
        except Exception:
            i=0

        return errMsg("Invalid block structure")

    def verifyThenAddBlock(self, block):
        try:
            #TODO test this, it was only checking for lower before!!!
            if (block['index'] != len(m_Blocks)):
                return "Block index invalid"
        except Exception:
            return "Invalid block"
        # check structure of block and TX, but not yet the balances
        err = verifyBlockAndAllTX(block)
        if len(err) > 0:
            return err

        # structures are all corrcet so now check balances and update them
        # clearing of all pending transactions involved in the block is done inside completed updatebalance!
        err = confirmUpdateBalances(block['transactions'], False)
        if len(err) > 0:
            return err

        m_Blocks.append(deepcopy(block))
        self.prepareNewCandidateBlock()
        m_info['currentDifficulty'] = 5 #TODO shall we make the new difficulty flexible??? is hti sthe right place?
        m_info['blocksCount'] = len(m_Blocks)
        m_info['cumulativeDifficulty'] = m_info['cumulativeDifficulty']*(block['difficulty']+1) #slides claim 16^ but even nakov chain does not follow
        m_info['confirmedTransactions'] = m_info['confirmedTransactions'] + len(block['transactions'])
        m_info['pendingTransactions'] = len(m_pendingTX)
        return ""

    def getBlockByNumber(self, blockNr):
        if blockNr >= 0:
            if blockNr < len(m_Blocks):
                return m_Blocks[blockNr]
        return{}

    def getJSONBlockByNumber(self, blockNr):
        blk = self.getBlockByNumber(blockNr)
        if len(blk) > 0:
            return setOK(blk)
        return errMsg('BlockNumber not valid or not existent: '+str(blockNr))

    # this is not part of standard Nakov, but useful for info testing and debugging and
    # later for chain verifications or fast loading
    def getBlockHash(self, params):
        try:
            hfrom = +params['from']
            hto = +params['to']
            hlength = +params['cnt']
            if (hfrom < 0) or (hfrom >= len(m_Blocks)) or (hto < hfrom) or \
                    (hlength < 0) or (hlength > len(defHash)):
                return errMsg("Inconsistent request")
            repl = []
            if hlength == 0:
                hlength = len(defHash)
            for x in range(hfrom, hto+1):
                if x >= len(m_Blocks):
                    break
                repl.append([x, m_Blocks[x]['blockHash'][0:hlength]])
            return setOK(repl)
        except Exception:
            return errMsg("Invalid parameters")

    def getBlockBalances(self, para):
        bal = {}
        err = self.getBalanceFromToBlock(0, para['to'], bal)
        if err != "":
            return errMsg(err)
        return setOK(bal)

    def getBalanceFromToBlock(self, startBlock, lastBlock, calcBal):
        if (startBlock < 0) or (lastBlock > len(m_Blocks)-1):
            return "invalid range"

        for idx in range(startBlock, lastBlock+1):
            blk = m_Blocks[idx]
            # check structure of block and TX, but not yet the balances
            err = verifyBlockAndAllTXOn(blk, False)
            if len(err) > 0:
                return err

            if updateTempBalance(blk['transactions'], calcBal) is False:
                return "Block rejected, invalid TX detected in block: " + idx

        return ""
