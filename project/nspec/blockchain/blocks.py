from project.nspec.blockchain.verify import verifyBlockAndAllTX
from project.nspec.blockchain.balance import m_AllBalances, confirmUpdateBalances, updateTempBalance
from threading import Thread
from project.models import useNet, m_info, m_cfg
from project.nspec.blockchain.modelBC import m_Blocks, m_genesisSet, m_candidateBlock, m_pendingTX, m_BufferMinerCandidates
from project.nspec.blockchain.modelBC import m_informsPeerNewBlock, m_balHistory, m_static_emptyBlock
from project.utils import checkRequiredFields, isSameChain, setOK, errMsg, sha256StrToHex
from project.models import defHash
from project.pclass import c_peer
from copy import deepcopy
import sys
from time import sleep
from flask import jsonify


class blockchain:
    status = {'getMissingBlocks': False}

    def setNetBasedOnChainID(self, id):
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

        #addNewRealBalance(defAdr, 0)
        err = verifyBlockAndAllTX(m_genesisSet[useNet], True)
        if len(err) > 0:
            print("Ooops, it appears that the genesis Block is not correct, please fix...  "+err)
            sys.exit(-1)

        #the genesis block TX shows how many coins went to faucet and to donors
        err = confirmUpdateBalances(m_genesisSet[useNet]['transactions'], True)
        if len(err) > 0:
            print("Ooops, it appears that the genesis Block is not correct, please fix... " + err)
            sys.exit(-1)
        m_Blocks.append(deepcopy(m_genesisSet[useNet]))


    def initChain(self,onePeer="", fetchAll=False, hashFetch=False):
        self.clearChainLoadGenesis()

        if fetchAll is False:
            #get the blocks one by one, due to size or whatever (later maybe even only getting the hashes!
            threadx = Thread(target=self.getMissingBlocksFromPeer,args=(onePeer, -1, False))
            threadx.start()
            return
        else:
            if hashFetch is True:
                allPeersInfo = c_peer.sendGETToPeers("blocks/hash/0/100/"+str(len(defHash))) #TODO how to detemine? use info first?
            else:
                self.getAllBlocksOneReadDirect()
        m_cfg['chainLoaded'] = True


    def resetChain(self):
        m_cfg['statusChain'] = True
        m_cfg['statusChain'] = False
        try:
            self.initChain("", True, False)
        except Exception:
            print("Seems no peers ready yet....")
        m_cfg['statusChain'] = False


    def getAllBlocksOneReadDirect(self):
        #coming here we are sure that we have back-up or nothing to loose!
        allPeersInfo = c_peer.sendGETToPeers("info")
        ret = -1
        bestPeer=""

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
                #navkov has wrong nodeUrl info, so change this to fix url is used in initargs!!!
                #bestPeer = 'https://stormy-everglades-34766.herokuapp.com'
                blockList, ret = c_peer.sendGETToPeer(bestPeer+"/blocks")
                if ret == 200:
                    isFirst = True
                    for block in blockList:
                        if isFirst is True:
                            #TODO compare block with my genesis
                            # if any verification fails, set ret to -1
                            isFirst = False
                            #cumDiff = cumDiff + block['difficulty']
                            m_info['cumulativeDifficulty']= block['difficulty']
                            continue
                        if ret == 200:
                            if len(self.verifyThenAddBlock(block)) != 0:
                                self.clearChainLoadGenesis()
                                break
                        else:
                            self.clearChainLoadGenesis()
                            break
                    m_info['blocksCount'] = len(m_Blocks)
                    continue    #with ret being 200m, this ends the loop!!!
                del allPeersInfo[maxIdx]
                continue


    def prepareNewCandidateBlock(self):
        m_candidateBlock.clear()
        m_candidateBlock.update(deepcopy(m_static_emptyBlock)) #contains coinbase
        m_candidateBlock['index'] = len(m_Blocks)
        m_candidateBlock['prevBlockHash'] = m_Blocks[-1]['blockHash']
        m_BufferMinerCandidates.clear()

        #TODO add a maximum number for TX here
        m_candidateBlock['transactions'].clear()
        m_candidateBlock['transactions'].extend(m_pendingTX)


    def handleChainBackTracking(self, res, source, blockInfo):
        #TODO think of a way to handle this after the initial simple cases worked
        m_cfg['checkingChain'] = False
        return errMsg("Backtracking into chain is not yet supported, this is permanent fork in the network ")

    def checkChainSituation(self, source, blockInfo):
        #We arrive here either because a block notification was sent,
        #or because our peer got an info claiming the peer has longer chain.
        # here we decide on the situation of whether blocks are simply added on top
        # or if something more compliucated is needed, e.g. go back the stack to find
        # common block and then recover shared TXs etc. etc.
        #These are shared among info and block notification
        #   "nodeUrl": sender
        #   "blocksCount": 25, "cumulativeDifficulty": 127
        #only in info:
        #   "confirmedTransactions": 208
        try:
            print("checking status")
            while m_cfg['checkingChain'] is True:
                print("Already checking chain status, so complete the first one")
                #return errMsg("Please wait for current synchronisation to complete...")
                sleep(1)
            m_cfg['checkingChain'] = True
            peer = blockInfo['nodeUrl']
            if blockInfo['blocksCount'] < len(m_Blocks):
                print("local chain longer than for " + peer)
                m_cfg['checkingChain'] = False
                return errMsg("Notified chain shorter than local current, current is:" + str(len(m_Blocks)))
            elif blockInfo['blocksCount'] == len(m_Blocks):
                print("blocks on par, check next step with "+peer)
                #this means we have conflict on the same top block, probably parallel mined
                if blockInfo['cumulativeDifficulty'] < m_info['cumulativeDifficulty']:
                    #TODO by right we should notify the other node of our top block, so that he adjusts!?
                    m_cfg['checkingChain'] = False
                    print("local difficulty higher, no change")
                    return errMsg("Notified chain cumulativeDifficulty lower local current, current is:" + str(m_info['cumulativeDifficulty']))
                else :
                    # we have same height and same or lower difficulty, so we need to roll the dice for now
                    # based on hash

                    #get the actual block from peer
                    if (len(peer) > 0) and (peer[-1] != "/"):
                        peer = peer + "/"
                    base = "blocks/"
                    url = base + str(len(m_Blocks)-1)
                    print("seems we have conflict, get details from peer")
                    try:
                        res, stat = c_peer.sendGETToPeer(peer + url)
                    except Exception:
                        m_cfg['checkingChain'] = False
                        print("peer failed"+peer)
                        return errMsg("Unsupported block claimed by "+peer)
                    if stat == 200:
                        print("got peer block as requested with OK")
                        m, l, f = checkRequiredFields(res, m_genesisSet[0], [], False)
                        if len(m) == 0:
                            yoursBetter = False
                            if res['prevBlockHash'] != m_Blocks[-1]['prevBlockHash']:
                                print("hashes different need to settle backtrack")
                                return self.handleChainBackTracking(res, source, blockInfo)
                            if blockInfo['cumulativeDifficulty'] == m_info['cumulativeDifficulty']:
                                print("samer cumulDiff")
                                if res['difficulty'] == m_Blocks[-1]['difficulty']:
                                    print("roll the dice")
                                    #we are confirmed same same in all, so lets roll the deterministic dice
                                    #by crossing the two inputs
                                    myStr = res['blockDataHash']+m_Blocks[-1]['blockHash']
                                    yourStr = m_Blocks[-1]['blockDataHash']+res['blockHash']
                                    if myStr != yourStr:
                                        yoursBetter = sha256StrToHex(yourStr) > sha256StrToHex(myStr)
                            else:
                                #peer claimed its total difficulty is higher but on same level
                                #as per standard Nakov with fixed difficulty his is actually not possible for
                                #blocks on the same height, but for future and to check we see and acceptd
                                yoursBetter = (res['difficulty'] > m_Blocks[-1]['difficulty'])
                                if yoursBetter is False:
                                    m_cfg['checkingChain'] = False
                                    print("inconsistent claim between info and real block cumDif")
                                    return errMsg("Inconsistent cumulativeDifficulty claim")
                            if yoursBetter is True:
                                print("finally we conceed, add peers block from "+peer)
                                restor = m_Blocks[-1]
                                del m_Blocks[-1]
                                err = self.checkAndAddBlock(res, False, peer)
                                if len(err) > 0:
                                    print("something was wrong, restore own previous block")
                                    m_Blocks.append(restor)
                                    m_cfg['checkingChain'] = False
                                    return errMsg("Invalid block received")
                            else:
                                # TODO by right we should notify the other node of our top block as we win
                                print("local copy maintained after all")
                                i=0
                            m_cfg['checkingChain'] = False
                            return setOK("Thank you for the notification.")
                        m_cfg['checkingChain'] = False
                        print("The reply did not have the correct fields")
                        return errMsg("No proper reply, ignored")
                    m_cfg['checkingChain'] = False
                    return errMsg("Unsupported block claim by " + peer)
            else:
                print("local chain appears shorter anyway, so just ask for up to block "+str(blockInfo['blocksCount']))
                #the peer claims to be ahead of us with at leats one block, so catch up until something happens
                # easy case just add the new block on top, and each block is checked fully, no backtrack
                if source == 'notification':
                    print("Sender want a reply, so process")
                    err = self.getMissingBlocksFromPeer(blockInfo['nodeUrl'], blockInfo['blocksCount'], True)
                    m_cfg['checkingChain'] = False
                    if len(err) > 0:
                        return errMsg(err)
                    return setOK("Thank you for the notification.")
                else:
                    print("this is info internal, so create thread and don't care result")
                    threadx = Thread(target=self.getMissingBlocksFromPeer,args=(blockInfo['nodeUrl'], blockInfo['blocksCount'], False))
                    threadx.start()
                    m_cfg['checkingChain'] = False
        except Exception:
            m_cfg['checkingChain'] = False
            return errMsg("Porcessing error occured")



    def getMissingBlocksFromPeer(self, peer, upLimit, isAlert):
        if self.status['getMissingBlocks'] is True:
            return ""
        try:
            retry = 2
            self.status['getMissingBlocks'] = True
            if (len(peer) > 0) and (peer[-1] != "/"):
                peer = peer + "/"
            base = "blocks/"
            print("Work on missing block"+peer)
            while True:
                if (upLimit > 1) and (upLimit <= len(m_Blocks)):
                    self.status['getMissingBlocks'] = False
                    m_cfg['chainLoaded'] = True
                    m_cfg['checkingChain'] = False
                    return ""
                url = base + str(len(m_Blocks))
                try:
                    res, stat = c_peer.sendGETToPeerToAnyone(peer, url)
                except Exception:
                    self.status['getMissingBlocks'] = False
                    m_cfg['chainLoaded'] = True
                    m_cfg['checkingChain'] = False
                    return ""
                if stat == 200:
                    m, l, f = checkRequiredFields(res, m_genesisSet[0], [], False)
                    if len(m) == 0:
                        err = self.checkAndAddBlock(res, isAlert, peer)
                        if len(err) >0:
                            m_cfg['chainLoaded'] = True
                            m_cfg['checkingChain'] = False
                            return "Invalid block received"
                else:
                    if (stat == 400) and ('errorMsg' in res) and ('or not exist' in res['errorMsg']):
                        m_cfg['checkingChain'] = False
                        self.status['getMissingBlocks'] = False
                        return ""
                    retry = retry - 1 #maybe block has not spread well yet
                    if retry <= 0:
                        self.status['getMissingBlocks'] = False
                        m_cfg['chainLoaded'] = True
                        m_cfg['checkingChain'] = False
                        return "No valid information, stopped block updates."
                    #continue  # must continue as we have no res[index]
        except Exception:
            self.status['getMissingBlocks'] = False
        m_cfg['checkingChain'] = False
        m_cfg['chainLoaded'] = (len(m_Blocks) > 0)
        return "Verification failed"

    def checkAndAddBlock(self, res, isAlert, peer):
        err = self.verifyThenAddBlock(res)
        if len(err) > 0:
            self.status['getMissingBlocks'] = False
            return err
        # inform all our peers about the block
        m_BufferMinerCandidates.clear()
        if isAlert is True:
            toPeer = deepcopy(m_informsPeerNewBlock)
            toPeer["blocksCount"] = len(m_Blocks)
            toPeer["cumulativeDifficulty"] = m_info['cumulativeDifficulty']
            toPeer["nodeUrl"] = m_info['nodeUrl']
            c_peer.sendAsynchPOSTToPeers("peers/notify-new-block", toPeer, peer)
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
            if (block['index'] < len(m_Blocks)):
                return "Block already available"
        except Exception:
            return "Invalid block"
        #check structure of block and TX, but not yet the balances
        err = verifyBlockAndAllTX(block, False)
        if len(err) > 0:
            return err

        #structures are all corrcet so now check balances and update them
        # clearing of all pending transactions involved in the block is done inside completed updatebalance!
        err = confirmUpdateBalances(block['transactions'], False)
        if len(err) > 0:
            return err

        m_Blocks.append(deepcopy(block))
        self.prepareNewCandidateBlock()
        m_info['currentDifficulty'] = 5 #TODO shall we make the new difficulty flexible??? is hti sthe right place?
        m_info['blocksCount'] = len(m_Blocks)
        m_info['cumulativeDifficulty'] = m_info['cumulativeDifficulty']*16 + block['difficulty'] #slides claim 16^ but even nakov chain does not follow
        m_info['confirmedTransactions'] = m_info['confirmedTransactions'] + len(block['transactions'])
        m_info['pendingTransactions'] = len(m_pendingTX)
        return ""


    #this is for temporary calculation as we need to verify an entire segment before adding to the blockchain
    # def verifyThenStoreBlock(self, block, mblocks, minfo, balList):
    #     #check structure of block and TX, but not yet the balances
    #     err = verifyBlockAndAllTX(block, False)
    #     if len(err) > 0:
    #         return err
    #
    #     if updateTempBalance(block['transactions'], balList) is False:
    #         return "Block rejected, invalid TX detected "
    #
    #     mblocks.append(deepcopy(block))
    #     minfo['cumulativeDifficulty'] = minfo['cumulativeDifficulty']*16 + block['difficulty'] #slides claim 16^ but even nakov chain does not follow
    #     minfo['confirmedTransactions'] = minfo['confirmedTransactions'] + len(block['transactions'])
    #     return ""


    #TODO if this is not used anywhere else, shoift to next routin as fix code
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

    #this is not part of standard Nakov, but useful for info testing and debugging and
    #later for chain verifications or fast loading
    def getBlockHash(self, params):
        try:
            hfrom = +params['from']
            hto = +params['to']
            hlength = +params['cnt']
            if (hfrom < 0) or (hfrom >= len(m_Blocks)) or (hto < hfrom) or \
                    (hlength < 0) or (hlength > len(defHash)):
                return errMsg("Inconsistent request")
            repl = {}
            if hlength == 0:
                hlength = len(defHash)
            for x in range(hfrom, hto+1):
                if x >= len(m_Blocks):
                    break
                repl.update({""+str(x): m_Blocks[x]['blockDataHash'][0:hlength]})
            return setOK(repl)
        except Exception:
            return errMsg("Invalid parameters")
