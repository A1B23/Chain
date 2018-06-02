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

candidate = {}
cfg = {'zero_string': '00000000000000000000000000000',
       'maxNonce': 2147483647,  #typical Java max, so stick to it to avoid endless search
       'peer': -1,
       'miner_address': -1,
       'mode': 'n', #by default keep mining, if started with 'y', miner will wait for user
       'pulling': True
    }

# requires for GET to the blockchain network
def miner_get(url, data=None):
    #TODO put this into main node as well with content type etc....
    response = requests.get(url, data=data, headers={'content-type': 'application/json', 'accept': 'application/json'})
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
    return getFutureTimeStamp(candidate['difficulty']*1000)

def pullCandidate():
    while True:
        print("==== First Stage : Request a mining to Node ===================")
        if (cfg['mode'] == "y"):
            print("enter m <return> to start mining")
            choice = "s"
            while (choice != "m"):
                choice = input().lower()

        cfg['pulling'] = True
        try:
            resp_text = getCandidate()
            if candidate['blockDataHash'] != resp_text['blockDataHash']:
                candidate['blockDataHash'] = resp_text['blockDataHash']
                candidate['difficulty'] = resp_text['difficulty']
                candidate['dateCreated'] = getEstimatedTimeStamp()
                candidate['fixDat'] = candidate['blockDataHash'] + "|" + candidate['dateCreated'] + "|"
                candidate['nonce'] = random.randint(0, cfg['maxNonce'])  # avoid that each miner starts at same level
                candidate['oriNonce'] = candidate['nonce']  #prepare to avoid unneccessary looping
        except Exception:
            print("No/Invalid peer reply, retry...."+str(cfg['peer']))
            sleep(1)    # no peer, give a bit of time to recover, keep the 'pulling' flag to avoid waste of calc power
            continue
        cfg['pulling'] = False
        sleep(int(resp_text['difficulty']/2))
        cfg['pulling'] = False  # just confirm finish pulling in case of race condition with failed submission

def doMine():
    # miners continue to try to mine
    # request some block for mining to the networks(Node)
    # then try to find a hashing code and nonce value to meet with the difficulty
    while True:
        try:
            # Request and wait a response from the N/W
            foundSolution = False

            while (foundSolution == False):
                if (cfg['pulling'] == True):
                    sleep(1)
                    continue

                candidate['nonce'] = (candidate['nonce'] + 1) % cfg['maxNonce']  # increment modulus max
                if (candidate['nonce'] == candidate['oriNonce']):
                    break

                minedBlockHash = hashlib.sha256((fx + str(candidate['nonce'])).encode("utf8")).hexdigest()

                if minedBlockHash[:candidate['difficulty']] == cfg['zero_string'][:candidate['difficulty']]:
                    foundSolution = True

            if (foundSolution == False):
                # TODO try additional pulling?
                print("Full circle completed, mining stopped, awaiting next candidate block")
                sleep(1)
                continue
            # After finding a hashcode, now submit the mined block by POST
            # Data for POST
            data = {
                "blockDataHash": candidate['blockDataHash'],
                "dateCreated": candidate['dateCreated'],
                "nonce": str(candidate['nonce']),
                "blockHash": minedBlockHash
            }

            print("==== Second Stage : Post for mining result with Data to Node :", data)
            resp = requests.post(peer + "mining/submit-mined-block", json=data)
            resp_text = json.loads(resp.text)
            print("==== Second Stage : Response Received(Return code): ", resp.status_code)
            if (resp.status_code == 200):
                print("==========================")
                print("      MINING SUCCESS ")
                print("==========================")
            else:
                print("Error message: ", resp_text['errorMsg'])
        except Exception:
            print("Exception occurred... pause ...")
            cfg['pulling'] = True # set flag as if pulling to wait for new candidate being pulled


# main function : miner start from here
def main():
    parser = ArgumentParser()  # Albert
    parser.add_argument('-a', '--address', action="store", dest="address", help="miner address", default="spam1")
    # Albert parser.add_option('-u', '--url', action="store", dest="url", help="url of a node", default="spam2")
    parser.add_argument('-p', '--port', default=5555, type=int, help='port to listen on')
    parser.add_argument('-hip', '--host', default="127.0.0.80", help='hostname/IP')
    parser.add_argument('-con', '--connect', default="127.0.0.2", help='list of 127.0.0.x peers to send messages')
    parser.add_argument('-cID', '--chainID', default="", help='identify net by genesis blockHash')
    parser.add_argument('-nID', '--netID', default=1, type=int, help='identify net by pre-defined ID 0: Academy, 1: NAPCoin')
    parser.add_argument('-mod', '--mode', default="y", help='modus of miner to work, e.g. y=await user to trigger mining')

    args = parser.parse_args()
    cfg['miner_address'] = args.address
    cfg['mode'] = args.mode
    cfg['peer'] = args.connect + ":" + str(args.port) + "/"
    print("miner_address: ", cfg['miner_address'], "peer url: ", cfg['peer'])
    cfg['pulling'] = True
    thread = Thread(target=pullCandidate)
    thread.start()
    doMine()        #TODO adjust to thread an include flask to communicate with the node


#TODO add the same to main node so that is can be called programmatically as well
if __name__ == "__main__":
    main()
    #test = "df8f114897188bcc68b97ebe2b673d3c92de986024abe565df0a4f8702c1742b|2018-02-11T20:31:32.397Z|1453826"
    #res = hashlib.sha256(test.encode("utf8")).hexdigest()
