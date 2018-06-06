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

candidate = {}

cfg = {
    'zero_string': '00000000000000000000000000000',
    'maxNonce': 2147483647,  #typical Java max, so stick to it to avoid endless search
    'peer': -1,
    'miner_address': -1,
    'mode': 'n', #by default keep mining, if started with 'y', miner will wait for user
    'pulling': False,
}

# requires for GET to the blockchain network
def miner_get(url):
    #TODO put application type tec. this into main node as well with content type etc....
    response = requests.get(url, headers={'content-type': 'application/json', 'accept': 'application/json'})
    return response


def getCandidate():
    resp = miner_get(cfg['peer'] + "mining/get-mining-job/" + cfg['miner_address'])
    print("==== First Stage : Response Received from Node: ", resp.text)
    return json.loads(resp.text)


def getEstimatedTimeStamp():
    # we need to estimate the reasonable time is takes to find solution
    # which is based on difficulty, because if the timestamp is not realistic
    # and we want to adjust difficulty based on actual calculatoin power, then the
    # timestamp will not work, but this assumes the timestamp is a crucial element for
    # the decision
    return getFutureTimeStamp(candidate['difficulty']*1000) #TODO test


def isDataValid(resp_text):
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
    # TODO this isHard is wrong, after successful mine he still continues looping
    if (len(candidate) == 0):
        if (cfg['mode'] == "y"):
            print("enter m <return> to start mining")
            choice = "s"
            cfg['pulling'] = False
            while (choice != "m"):
                choice = input().lower()

        if (cfg['pulling'] == True):
            return #already pulling

    cfg['pulling'] = True
    while (cfg['pulling'] == True):
        print("==== First Stage : Request mining data from Node: "+str(cfg['peer']))
        try:
            resp_text = getCandidate()
            if (isDataValid(resp_text) == False):
                # no point to waste time and effort on this invalid/incomplete candidate
                print("Invalid peer reply, ignored....")
                sleep(5)
                continue

            if ((len(candidate) == 0) or (candidate['blockDataHash'] != resp_text['blockDataHash'])):
                candidate.clear()
                candidate['blockDataHash'] = resp_text['blockDataHash']
                candidate['difficulty'] = resp_text['difficulty']
                candidate['dateCreated'] = getEstimatedTimeStamp()
                candidate['fixDat'] = candidate['blockDataHash'] + "|" + candidate['dateCreated'] + "|"
                candidate['nonce'] = random.randint(0, cfg['maxNonce']-1)  # avoid that each miner starts at same level
                print("Start Nonce = "+str(candidate['nonce']))

            cfg['pulling'] = False
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
            sleep(int(candidate['difficulty']/2))
            cfg['pulling'] = False  # just confirm finish pulling in case of race condition with failed submission
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
            count=0
            show = 0
            while (foundSolution == False):
                if ((cfg['pulling'] == True) or (len(candidate) == 0)):
                    print("Wait for pulling to complete...")
                    sleep(1)
                else:
                    candidate['nonce'] = (candidate['nonce'] + 1) % cfg['maxNonce']  # increment modulus max
                    count = count + 1
                    show = show + 1
                    if (show > 5000):
                        print(str(count) + " "+str(candidate['nonce']))
                        show = 0

                    if (count >= cfg['maxNonce']):
                        print("Max loop reached")
                        break
                    #this doe snot use the make minershash as it is optimised for fixdata
                    minedBlockHash = hashlib.sha256((candidate['fixDat'] + str(candidate['nonce'])).encode("utf8")).hexdigest()

                    if minedBlockHash[:candidate['difficulty']] == cfg['zero_string'][:candidate['difficulty']]:
                        foundSolution = True

            if (foundSolution == True):
                # After finding a hashcode, now submit the mined block by POST
                # Data for POST
                data = {
                    "blockDataHash": candidate['blockDataHash'],
                    "dateCreated": candidate['dateCreated'],
                    "nonce": str(candidate['nonce']),
                    "blockHash": minedBlockHash
                }

                print("==== Second Stage : Post for mining result with Data to Node :", data)
                resp = requests.post(cfg['peer'] + "mining/submit-mined-block", json=data)

                if (resp.status_code == 200):
                    print("==========================")
                    print("      MINING SUCCESS " + str(candidate['nonce']-candidate['oriNonce']))
                    print("==========================")
                else:
                    print("Error message: ", resp_text['errorMsg'])
            else:
                print("No solution found")
        except Exception:
            print("Exception occurred... clear and refresh candidate")

        candidate.clear()
        pull()


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
