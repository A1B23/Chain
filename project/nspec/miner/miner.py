import hashlib
from time import sleep
import random
from threading import Thread
from project.nspec.blockchain.modelBC import m_candidateMiner, minBlockReward
from project.utils import checkRequiredFields, getFutureTime
from project.models import defHash, m_cfg
from project.nspec.miner.modelM import cfg, newCandidate
from project.pclass import c_peer
from project.classes import c_walletInterface
from copy import deepcopy


def miner_get(url):
    try:
        response = c_peer.sendGETToPeers(url)
        return response
    except Exception:
        return {'peerError': "No data received from peer"}


def getCandidate():
    try:
        resp = miner_get("/mining/get-mining-job/" + cfg['address'])
        resp, code = resp[0][0]
        return resp
    except Exception:
        return {'peerError': True}


def isDataValid(resp_text):
    m, l, f = checkRequiredFields(resp_text, m_candidateMiner, [], True)
    if (len(m) > 0) or (l != 0):
        print("required fields not matched")
        return False

    if (resp_text['difficulty'] > len(cfg['zero_string'])) or (resp_text['difficulty'] < 0):
        print("Difficulty not possible")
        return False

    if (resp_text['rewardAddress'] != cfg['address']) or (resp_text['index'] <= 0):
        print("Wrong reward address")
        return False

    if len(defHash) != len(resp_text['blockDataHash']):
        print("Wrong Hash length in blockDataHash"+resp_text['blockDataHash'])
        return False

    if resp_text['expectedReward'] < minBlockReward:
        print("Wrong Hash or too low expectedRewards: " + str(resp_text['expectedReward']))
        return False

    if resp_text['transactionsIncluded'] <= 0:
        print("No transaction at all")
        return False

    return True


def changeNonceDate():
    cfg['findNonce'] = False
    while cfg['waitAck'] is False:
        sleep(1)
    cfg['countSame'] = 0
    #TODO how to realistically estimate solution date, what are permitted differences?
    newCandidate['dateCreated'] = getFutureTime((newCandidate['difficulty']-4)*(newCandidate['difficulty']-4)*10)
    newCandidate['fixDat'] = newCandidate['blockDataHash'] + "|" + newCandidate['dateCreated'] + "|"
    newCandidate['nonce'] = random.randint(0, cfg['maxNonce'] - 1)  # avoid that each miner starts at same level
    print("Start Nonce " + str(newCandidate['nonce']))
    cfg['findNonce'] = True
    cfg['waitAck'] = False
    return

def pull():
    try:
        print("asking")
        resp_text = getCandidate()
        if "peerError" in resp_text:
            print("Peer error, sleep")
            sleep(3)
            return
        if isDataValid(resp_text) is False:
            # no point to waste time and effort on this invalid/incomplete candidate
            print("Invalid node block data detected, ignored....")
            sleep(3)
            return

        if (cfg['findNonce'] is False) or (cfg['lastHash'] != resp_text['blockDataHash']):
            print("new block data")
            cfg['findNonce'] = False
            while cfg['waitAck'] is False:
                sleep(1)
            cfg['lastHash'] = resp_text['blockDataHash']
            newCandidate['blockDataHash'] = resp_text['blockDataHash']
            newCandidate['difficulty'] = resp_text['difficulty']
            changeNonceDate()
        else:
            cfg['countSame'] = cfg['countSame'] + 1
            #TODO stratgey: go by number of pulls or go by number of tries? Here it is pulls
            #but aside from pulls if we ever reach maxcount of nonce tries, we also change
            if (cfg['countSame'] > cfg['refresh']) and (cfg['foundSolution'] is False):
                #as the block has not changed, we change the date and restart
                changeNonceDate()


    except Exception:
        print("No/Invalid peer reply, retry....")
        sleep(5)  # no peer, give a bit of time to recover, keep the 'pulling' flag to avoid waste of calc power

    return


def pullCandidate():
    thread = Thread(target=doMine)
    thread.start()
    while m_cfg['shutdown'] is False:
        try:
            pull()
            sleep(int(newCandidate['difficulty']/2)+1)
        except Exception:
            print("Pulling candidate block failed...")


def doMine():
    # miners continue to try to mine
    # request some block for mining to the networks(Node)
    # then try to find a hashing code and nonce value to meet with the difficulty
    while m_cfg['shutdown'] is False:
        while cfg['findNonce'] is False:
            sleep(1)
            cfg['waitAck'] = True
        if m_cfg['mode'] == "Y":
            print("Enter m <return> to start mining")
            choice = "s"
            while choice != "m":
                choice = input().lower()
            while cfg['findNonce'] is False:
                sleep(1)
                cfg['waitAck'] = True
        candidate = deepcopy(newCandidate)
        cfg['waitAck'] = False
        target = cfg['zero_string'][:candidate['difficulty']]
        try:
            # Request and wait a response from the N/W
            cfg['foundSolution'] = False
            count = 0
            #TODO remove the show once it works?
            show = 0
            minedBlockHash = "N/A"
            while (cfg['foundSolution'] is False) and (cfg['findNonce'] is True):
                candidate['nonce'] = candidate['nonce'] + 1
                if candidate['nonce'] >= cfg['maxNonce']:
                    candidate['nonce'] = 0
                    print("wrap around encountered")
                count = count + 1
                show = show + 1
                if show > 25000:
                    print(str(count) + " "+str(candidate['nonce']))
                    show = 0

                if count >= cfg['maxNonceTry']:
                    print("Max trial number reached, get new date")
                    cfg['waitAck'] = True
                    changeNonceDate()
                    candidate = deepcopy(newCandidate)
                    count = 0

                #this does not use the make minershash as it is optimised for fixDat to be faster
                minedBlockHash = hashlib.sha256((candidate['fixDat'] + str(candidate['nonce'])).encode("utf8")).hexdigest()

                if minedBlockHash[:candidate['difficulty']] == target:
                    cfg['foundSolution'] = True

            cfg['findNonce'] = False
            cfg['done'] = True
            if cfg['foundSolution'] is True:
                # After finding a hashcode, now submit the mined block by POST
                # Data for POST
                ndata = {
                    "blockDataHash": candidate['blockDataHash'],
                    "dateCreated": candidate['dateCreated'],
                    "nonce": candidate['nonce'],
                    "blockHash": minedBlockHash
                }

                sent = False
                for peer in m_cfg['activePeers']:
                    resp = c_peer.doPOST(url=peer + "/mining/submit-mined-block", json=ndata)
                    sent = True
                    break
                if sent is False:
                    for peer in m_cfg['shareToPeers']:
                        resp = c_peer.doPOST(url=peer + "/mining/submit-mined-block", json=ndata)
                        sent = True
                        break
                if (sent is True) and (resp.status_code == 200):
                    print("MINING SUCCESS (" + str(count) + " tries): " + resp.text)
                else:
                    print("MINING FAIL: ", resp.text)
            else:
                print("No solution found or new block came in")
        except Exception:
            cfg['findNonce'] = False
            print("Exception occurred... clear and refresh candidate")


def initMiner(IP):
    random.seed(a=hashlib.sha256(getFutureTime(0).encode("utf8")))
    cfg['pulling'] = True
    #TODO make minerWallet name configurable so that they don't overwrite each other when run locally
    wallet = 'minerWallet' + (IP[-2:].replace(".", "x"))
    if c_walletInterface.hasWallet(wallet) is False:
        c_walletInterface.addKeysToWalletBasic({'name': wallet, 'user': wallet+'AsUser', 'numKeys': 1, 'keyNames': ['minerKey']}, wallet)
    repl = c_walletInterface.getDataFor(['name', 'minerKey'], wallet, "", wallet+'AsUser')
    cfg['address'] = repl[4]
    thread = Thread(target=pullCandidate)
    thread.start()


    #test = "df8f114897188bcc68b97ebe2b673d3c92de986024abe565df0a4f8702c1742b|2018-02-11T20:31:32.397Z|1453826"
    #res = hashlib.sha256(test.encode("utf8")).hexdigest()
