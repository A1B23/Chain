import hashlib
from time import sleep
import datetime
import time
import random
from threading import Thread
from project.nspec.blockchain.modelBC import m_candidateMiner, minBlockReward
from project.utils import checkRequiredFields, getFutureTime, d
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
        if len(resp) == 1:
            resp, code = resp[0]
        else:
            resp, code = resp[0][0]
        return resp
    except Exception:
        return {'peerError': True}


def isDataValid(resp_text):
    m, l, f = checkRequiredFields(resp_text, m_candidateMiner, [], True)
    if (len(m) > 0) or (l != 0):
        d("required fields not matched")
        return False

    #TODO shoul dthis be further limited to half of zero and at least 5???
    if (resp_text['difficulty'] >= len(cfg['zero_string'])) or (resp_text['difficulty'] < 0):
        d("Difficulty not possible")
        return False

    if (resp_text['rewardAddress'] != cfg['address']) or (resp_text['index'] <= 0):
        d("Wrong reward address")
        return False

    if len(defHash) != len(resp_text['blockDataHash']):
        d("Wrong Hash length in blockDataHash"+resp_text['blockDataHash'])
        return False

    if resp_text['expectedReward'] < minBlockReward:
        d("Wrong Hash or too low expectedRewards: " + str(resp_text['expectedReward']))
        return False

    if resp_text['transactionsIncluded'] <= 0:
        d("No transaction at all")
        return False

    return True


def changeNonceDate():
    d("change nonce")
    cfg['countSame'] = 0
    #TODO how to realistically estimate solution date, what are permitted differences?
    newCandidate['dateCreated'] = getFutureTime((newCandidate['difficulty']-4)*(newCandidate['difficulty']-4)*10)
    cfg['dateCreated'] = newCandidate['dateCreated']
    newCandidate['fixDat'] = newCandidate['blockDataHash'] + "|" + newCandidate['dateCreated'] + "|"
    newCandidate['nonce'] = random.randint(0, cfg['maxNonce'] - 1)  # avoid that each miner starts at same level
    d("Start Nonce " + str(newCandidate['nonce']))
    d("nonce done")
    return


def pull():
    try:
        d("asking")
        cfg['pulling'] = True
        resp_text = getCandidate()
        d("got "+str(resp_text))
        if "peerError" in resp_text:
            d("Peer error, sleep")
            sleep(3)
            return
        if isDataValid(resp_text) is False:
            # no point to waste time and effort on this invalid/incomplete candidate
            d("Invalid node block data detected, ignored....")
            sleep(3)
            return
        d("ok check, miner was idle "+str(cfg['done']))
        if cfg['blockHash'] != resp_text['blockDataHash']:
            d("new block data")
            cfg['done'] = True #stop any ongoing looping

        if cfg['done'] is True:
            d("prepare block data for miner whenever miner is ready, even if we already have it all set")
            cfg['nonceCnt']
            cfg['blockHash'] = resp_text['blockDataHash']
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
        cfg['pulling'] = False
    except Exception:
        d("No/Invalid peer reply, retry....")
        sleep(5)  # no peer, give a bit of time to recover, keep the 'pulling' flag to avoid waste of calc power
        # we keep the pulling flag, as without peer no point to churn CPUf
    return


def pullCandidate():
    thread = Thread(target=doMine)
    thread.start()
    cfg['foundSolution'] = False
    while m_cfg['shutdown'] is False:
        try:
            while cfg['foundSolution'] is True:
                # if it is true, we are just sending, or we have a delay in sending for simulation
                # so no point to ask for new block, just sleep a bit
                sleep(1)
            pull()
            sleep(int(newCandidate['difficulty']/2)+2)
        except Exception:
            print("Pulling candidate block failed...")


def doMine():
    # miners continue to try to mine
    # request some block for mining to the networks(Node)
    # then try to find a hashing code and nonce value to meet with the difficulty
    while m_cfg['shutdown'] is False:
        cfg['foundSolution'] = False
        cfg['done'] = True
        cfg['pulling'] = True
        if m_cfg['mode'] == "Y":
            d("Enter m <return> to (re-)start mining, candidate changed or new:")
            choice = 0
            while True:
                try:
                    if choice > 0:
                        d("Invalid request: "+sel)
                    choice = choice + 1
                    sel = input().lower()
                    if sel == 'm':
                        sel = 0
                        break
                    if sel[0] == "d":
                        secs = int(sel[1:])
                        if secs > 0:
                            sel = datetime.datetime.now() + datetime.timedelta(seconds=secs)
                            sel = "d" + str(int(time.mktime(sel.timetuple())))
                            break
                    if sel[0] == "s":
                        secs = int(sel[1:])
                        if (secs >= 0) and (secs < 60):
                            break
                except Exception:
                    d("Invalid input: "+sel)
            cfg['mineSend'] = sel
        while cfg['pulling'] is True:
            sleep(1)
        cfg['done'] = False
        candidate = deepcopy(newCandidate)
        target = cfg['zero_string'][:candidate['difficulty']]
        cfg['nonceCnt']=0
        try:
            count = 0
            # show progress of nonce finding
            show = 0
            minedBlockHash = "N/A"
            while (cfg['foundSolution'] is False) and (cfg['done'] is False):
                candidate['nonce'] = candidate['nonce'] + 1
                if candidate['nonce'] >= cfg['maxNonce']:
                    candidate['nonce'] = 0
                    d("wrap around encountered")
                count = count + 1
                show = show + 1
                if show > 25000:
                    cfg['nonceCnt'] = show
                    d(str(count) + " "+str(candidate['nonce']))
                    show = 0

                if count >= cfg['maxNonceTry']:
                    d("Max trial number reached, get new date")
                    cfg['waitAck'] = True
                    changeNonceDate()
                    candidate = deepcopy(newCandidate)
                    count = 0

                #this does not use the make minershash as it is optimised for fixDat to be faster
                minedBlockHash = hashlib.sha256((candidate['fixDat'] + str(candidate['nonce'])).encode("utf8")).hexdigest()

                if minedBlockHash[:candidate['difficulty']] == target:
                    cfg['foundSolution'] = True

            cfg['done'] = True
            if cfg['foundSolution'] is True:
                cfg['nonceCnt'] = show
                # After finding a hashcode, now submit the mined block by POST
                # Data for POST
                ndata = {
                    "blockDataHash": candidate['blockDataHash'],
                    "dateCreated": candidate['dateCreated'],
                    "nonce": candidate['nonce'],
                    "blockHash": minedBlockHash
                }

                sent = False
                if cfg['mineSend'] != 0:
                    try:
                        if cfg['mineSend'][0] == "d":
                            sel = int(cfg['mineSend'][1:])
                            while int(time.mktime(datetime.datetime.now().timetuple())) < sel:
                                d("Wait to send due to delay...")
                                sleep(1)
                        elif cfg['mineSend'][0] == "s":
                            sel = int(cfg['mineSend'][1:])
                            isLower = (datetime.datetime.now().second <= sel)
                            while datetime.datetime.now().second != sel:
                                if (isLower is True) and (datetime.datetime.now().second >= sel):
                                    break
                                else:
                                    isLower = (datetime.datetime.now().second <= sel)
                                d("Wait to send due seconds check..." + str(isLower))
                                sleep(1)
                    except Exception:
                        print("send control invalid: "+cfg['mineSend'])
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
                    d("MINING SUCCESS (" + str(count) + " tries): " + resp.text)
                else:
                    d("MINING FAILED: ", resp.text)
            else:
                d("No solution found or new block came in")
        except Exception:
            d("Exception occurred... clear and refresh candidate")


def initMiner(IP):
    random.seed(a=hashlib.sha256(getFutureTime(0).encode("utf8")))
    cfg['pulling'] = True
    # TODO make minerWallet name configurable so that they don't overwrite each other when run locally
    # using IP is just a quick work around
    wallet = 'minerWallet' + (IP.replace(".", "x"))
    if c_walletInterface.hasWallet(wallet) is False:
        c_walletInterface.addKeysToWalletBasic({'name': wallet, 'user': wallet+'AsUser', 'numKeys': 1, 'keyNames': ['minerKey']}, wallet)
    repl = c_walletInterface.getDataFor(['name', 'minerKey'], wallet, "", wallet+'AsUser')
    cfg['address'] = repl[4]
    thread = Thread(target=pullCandidate)
    thread.start()


    #test = "df8f114897188bcc68b97ebe2b673d3c92de986024abe565df0a4f8702c1742b|2018-02-11T20:31:32.397Z|1453826"
    #res = hashlib.sha256(test.encode("utf8")).hexdigest()
