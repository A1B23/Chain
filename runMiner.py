import json
import requests
import time, datetime
import hashlib
import sys
from argparse import ArgumentParser
from time import sleep
import random
from project.utils import getFutureTimeStamp
from threading import Thread
from project.nspec.blockchain.modelBC import m_candidateMiner, minBlockReward
from project.utils import checkRequiredFields, makeMinerHash
from project.models import defHash
from project.nspec.miner.modelM import *


def miner_get(url):
    #TODO put application type tec. this into main node as well with content type etc....
    response = requests.get(url, headers={'content-type': 'application/json', 'accept': 'application/json'})
    return response


def getCandidate():
    resp = miner_get(cfg['peer'] + "mining/get-mining-job/" + cfg['miner_address'])
    print("==== First Stage : Response Received from Node: ", resp.text)
    return json.loads(resp.text)


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
    if ((len(m) > 0) or (l != 0)):
        print("Err1")
        return False

    if ((resp_text['difficulty'] > len(cfg['zero_string'])) or (resp_text['difficulty'] < 0)):
        print("Err1")
        return False

    if ((resp_text['rewardAddress'] != cfg['miner_address']) or (resp_text['index'] <= 0)):
        print("Err2")
        return False

    if (len(defHash) != len(resp_text['blockDataHash']) or (resp_text['expectedReward']< minBlockReward)):
        print("Err3")
        return False

    if (resp_text['transactionsIncluded'] <=0):
        print("Err4")
        return False

    return True


def pull():
    #print(" .... len " +str(len(candidate))+ " scan " + str(cfg['scanning'])+ " pull "+str(cfg['pulling']))
    if (cfg['scanning'] < 8):
        return

    if (cfg['scanning'] >8):
        cfg['scanning'] = 0
        if (cfg['mode'] == "y"):
            print("enter m <return> to start mining")
            choice = "s"
            cfg['pulling'] = False
            while (choice != "m"):
                choice = input().lower()


    print("==== First Stage : Request mining data from Node: "+str(cfg['peer']))
    try:
        resp_text = getCandidate()
        if (isDataValid(resp_text) == False):
            # no point to waste time and effort on this invalid/incomplete candidate
            print("Invalid node block data detected, ignored....")
            cfg['scanning'] = 10
            sleep(5)
            return

        if ((cfg['scanning'] <5) or (cfg['lastHash'] != resp_text['blockDataHash'])):
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
            if (len(candidate)>0):
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
            while (foundSolution == False):
                if (cfg['scanning'] == 6):
                    cfg['scanning'] = 7
                if (cfg['scanning'] != 8):
                    sleep(1)
                    continue
                else:
                    candidate['nonce'] = (candidate['nonce'] + 1) % cfg['maxNonce']  # increment modulus max
                    count = count + 1
                    show = show + 1
                    if (show > 10000):
                        print(str(count) + " "+str(candidate['nonce']))
                        show = 0

                    if (count >= cfg['maxNonce']):
                        print("Max loop reached")
                        break
                    #this does not use the make minershash as it is optimised for fixDat to be faster
                    minedBlockHash = hashlib.sha256((candidate['fixDat'] + str(candidate['nonce'])).encode("utf8")).hexdigest()

                    if minedBlockHash[:candidate['difficulty']] == cfg['zero_string'][:candidate['difficulty']]:
                        foundSolution = True

            if (foundSolution == True):
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
                resp = requests.post(cfg['peer'] + "mining/submit-mined-block", json=data)
                if (resp.status_code == 200):
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


def main():
    parser = ArgumentParser()  # TODO extend and integrate to initarg
    parser.add_argument('-a', '--address', default="ab2018", help="miner address")
    parser.add_argument('-p', '--port', default=5555, type=int, help='port to listen on')
    parser.add_argument('-hip', '--host', default="127.0.0.80", help='hostname/IP')
    parser.add_argument('-con', '--connect', default="127.0.0.2", help='list of 127.0.0.x peers to send messages')
    parser.add_argument('-cID', '--chainID', default="", help='identify net by genesis blockHash')
    parser.add_argument('-nID', '--netID', default=1, type=int, help='identify net by pre-defined ID 0: Academy, 1: NAPCoin')
    parser.add_argument('-mod', '--mode', default="y", help='modus of miner to work, e.g. y=await user to trigger mining')
    random.seed(a=getFutureTimeStamp(0))
    args = parser.parse_args()
    cfg['miner_address'] = args.address
    cfg['mode'] = args.mode
    cfg['peer'] = args.connect + ":" + str(args.port) + "/"
    if (not cfg['peer'][:4] == 'http'):
        cfg['peer'] = "http://"+cfg['peer']
    print("miner_address: ", cfg['miner_address'], "peer url: ", cfg['peer'])
    cfg['pulling'] = True
    thread = Thread(target=pullCandidate)
    thread.start()
    doMine()        #TODO adjust to thread an include flask to communicate with the node


if __name__ == "__main__":
    main()
    #test = "df8f114897188bcc68b97ebe2b673d3c92de986024abe565df0a4f8702c1742b|2018-02-11T20:31:32.397Z|1453826"
    #res = hashlib.sha256(test.encode("utf8")).hexdigest()
