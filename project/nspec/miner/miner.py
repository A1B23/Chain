import hashlib
from time import sleep
import random
from project.utils import getFutureTimeStamp
from threading import Thread
from project.nspec.blockchain.modelBC import m_candidateMiner, minBlockReward
from project.utils import checkRequiredFields
from project.models import defHash, m_cfg
from project.nspec.miner.modelM import *
from project.pclass import c_peer
from project.nspec.wallet.transactions import get_public_address, generate_private_key


def miner_get(url):
    try:
        response, code = c_peer.sendGETToPeer(url)
        return response
    except Exception:
        return {'peerError': "No data received from peer"}


def getCandidate():
    for peer in m_cfg['peers']:
        resp = miner_get(peer + "/mining/get-mining-job/" + cfg['address'])
        print("==== First Stage : Response Received from Node: ", str(resp))
        return resp
    print(" no peer listed...")
    return ""


def getEstimatedTimeStamp(diff):
    # we need to estimate the reasonable time is takes to find solution
    # which is based on difficulty, because if the timestamp is not realistic
    # and we want to adjust difficulty based on actual calculatoin power, then the
    # timestamp will not work, but this assumes the timestamp is a crucial element for
    # the decision
    return getFutureTimeStamp(diff*1000) #TODO test


def isDataValid(resp_text):
    # TODO update the meanoign of Err1 etc.... or remove
    m, l, f = checkRequiredFields(resp_text, m_candidateMiner, [], True)
    if (len(m) > 0) or (l != 0):
        print("Err1")
        return False

    if (resp_text['difficulty'] > len(cfg['zero_string'])) or (resp_text['difficulty'] < 0):
        print("Err1")
        return False

    if (resp_text['rewardAddress'] != cfg['address']) or (resp_text['index'] <= 0):
        print("Err2")
        return False

    if (len(defHash) != len(resp_text['blockDataHash']) or (resp_text['expectedReward']< minBlockReward)):
        print("Err3")
        return False

    if resp_text['transactionsIncluded'] <= 0:
        print("Err4")
        return False

    return True


def pull():
    print("status: "+str(cfg['scanning']))
    if cfg['scanning'] < 8:
        return
    elif cfg['scanning'] > 8:
        cfg['scanning'] = 0
        if m_cfg['mode'] == "Y":
            print("enter m <return> to start mining")
            choice = "s"
            cfg['pulling'] = False
            while (choice != "m"):
                choice = input().lower()

    print("==== First Stage : Request mining data from Node: "+str(m_cfg['peers']))
    try:
        if m_cfg['canTrack'] and (cfg['scanning'] == 8):
            print("Delay pull for animation....")
            sleep(3) #TODO This sleep is trial first
        resp_text = getCandidate()
        if "peerError" in resp_text:
            return
        if isDataValid(resp_text) is False:
            # no point to waste time and effort on this invalid/incomplete candidate
            print("Invalid node block data detected, ignored....")
            cfg['scanning'] = 10
            sleep(5)
            return

        if (cfg['scanning'] <5) or (cfg['lastHash'] != resp_text['blockDataHash']):
            cfg['scanning'] = 5
            cfg['lastHash'] = resp_text['blockDataHash']
            candidateTmp = {}
            candidateTmp['blockDataHash'] = resp_text['blockDataHash']
            candidateTmp['difficulty'] = resp_text['difficulty']
            candidateTmp['dateCreated'] = getEstimatedTimeStamp(candidateTmp['difficulty'])
            candidateTmp['fixDat'] = candidateTmp['blockDataHash'] + "|" + candidateTmp['dateCreated'] + "|"
            candidateTmp['nonce'] = random.randint(0, cfg['maxNonce']-1)  # avoid that each miner starts at same level
            print("Start Nonce = "+str(candidateTmp['nonce']))
            cfg['scanning'] = 6
            while (cfg['scanning'] == 6):
                sleep(1)
            candidate.clear()
            candidate.update(candidateTmp)
            cfg['scanning'] = 8

        return
    except Exception:
        print("No/Invalid peer reply, retry....")
        sleep(5)  # no peer, give a bit of time to recover, keep the 'pulling' flag to avoid waste of calc power

    return


def pullCandidate():
    while True:
        try:
            print("Initiate timed pull for refresh")
            pull()
            if len(candidate) > 0:
                sleep(int(candidate['difficulty']/2))
            else:
                sleep(2)

        except Exception:
            print("Pulling candidate block failed...")


def doMine():
    # miners continue to try to mine
    # request some block for mining to the networks(Node)
    # then try to find a hashing code and nonce value to meet with the difficulty
    while True:
        try:
            # Request and wait a response from the N/W
            foundSolution = False
            count = 0
            #TODO remove the show once it works?
            show = 0
            minedBlockHash = "N/A"
            while foundSolution is False:
                if cfg['scanning'] == 6:
                    cfg['scanning'] = 7
                if cfg['scanning'] != 8:
                    sleep(1)
                    continue
                else:
                    candidate['nonce'] = (candidate['nonce'] + 1) % cfg['maxNonce']  # increment modulus max
                    count = count + 1
                    show = show + 1
                    if show > 20_000:
                        print(str(count) + " "+str(candidate['nonce']))
                        show = 0

                    if count >= cfg['maxNonce']:
                        print("Max loop reached")
                        break
                    #this does not use the make minershash as it is optimised for fixDat to be faster
                    minedBlockHash = hashlib.sha256((candidate['fixDat'] + str(candidate['nonce'])).encode("utf8")).hexdigest()

                    if minedBlockHash[:candidate['difficulty']] == cfg['zero_string'][:candidate['difficulty']]:
                        foundSolution = True

            if foundSolution is True:
                # After finding a hashcode, now submit the mined block by POST
                # Data for POST
                ndata = {
                    "blockDataHash": candidate['blockDataHash'],
                    "dateCreated": candidate['dateCreated'],
                    "nonce": candidate['nonce'],
                    "blockHash": minedBlockHash
                }
                data.clear()
                data.update(ndata)

                print("==== Second Stage : Post for mining result with Data to Node :", data)
                for peer in m_cfg['peers']:
                    resp = c_peer.doPOST(peer + "/mining/submit-mined-block", json=data)
                    break
                cfg['scanning'] = 10
                if resp.status_code == 200:
                    print("==========================")
                    print("      MINING SUCCESS (" + str(count) + " tries): " + resp.text)
                    print("==========================")
                else:
                    print("Error message: ", resp.text)
            else:
                print("No solution found")
        except Exception:
            print("Exception occurred... clear and refresh candidate")
        print("Round finished, start new...")
        cfg['scanning'] = 10


def initMiner():
    random.seed(a=getFutureTimeStamp(0))
    cfg['pulling'] = True
    cfg['privKey'] = generate_private_key()
    cfg['address'] = get_public_address(cfg['privKey'])
    thread = Thread(target=pullCandidate)
    thread.start()
    thread2 = Thread(target=doMine)
    thread2.start()

    #test = "df8f114897188bcc68b97ebe2b673d3c92de986024abe565df0a4f8702c1742b|2018-02-11T20:31:32.397Z|1453826"
    #res = hashlib.sha256(test.encode("utf8")).hexdigest()
