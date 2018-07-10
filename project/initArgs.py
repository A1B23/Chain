from project.nspec.blockchain.modelBC import m_genesisSet
from project.utils import genNodeID
from project.classes import c_blockchainNode
from project.nspec.blockchain.verify import initPendingTX
from time import sleep
from project import app
from argparse import ArgumentParser
from project.models import m_cfg, m_info
from project.pclass import c_peer
from threading import Thread
import sys
from project.nspec.miner.miner import initMiner
import sqlite3
from project.nspec.wallet.modelW import m_db


def finalise(peer, port, type):
    # default for peers is exactly one, but if started up with more, more are supported
    # the argument sets the time how often the checks are made in seconds to verify if the peer still replies
    useVis = m_cfg['canTrack']
    #temporarily switch off any delay to allow peer initialisation to go ahead without delay
    m_cfg['canTrack'] = False
    c_peer.setPeersAs(peer, port)
    thread = Thread(target=c_peer.checkEveryXSecs)
    thread.start()
    while m_cfg['statusPeer'] == True:
        sleep(1)
    if type == "BCNode":
        c_blockchainNode.c_blockchainHandler.resetChain()
        #thread = Thread(target=initPendingTX)
        #thread.start()
        initPendingTX()
    elif type == "Miner":
        initMiner()
    elif type == "Wallet":
        #CREATE TABLE `Wallet` ( `ID` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `WName` TEXT NOT NULL UNIQUE, `privKey` TEXT, `pubKey` TEXT, `address` TEXT, `KName` TEXT, `ChkSum` TEXT )
        m_db['db'] = sqlite3.connect(m_db['DATABASE'])

    m_cfg['canTrack'] = useVis

@app.after_request
def after_request(response):
    # this allows the visualiser to support CORS
    #to be more secure, should not allow '*' but only allow the local visualiser, but have not succeeded, so open all
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    return response


def main(type):
    m_cfg['type'] = type
    parser = ArgumentParser()
    host, port, peer = init(parser)
    thread = Thread(target=finalise, args=(peer, port, type))
    thread.start()
    app.run(host=host, port=port, threaded=True)


def init(parser):
    parser.add_argument('-p', '--port', default=5555, type=int, help='port to listen on')
    parser.add_argument('-hip', '--host', default="127.0.0.6", help='hostname/IP')
    parser.add_argument('-con', '--connect', default="2,5", help='list of 127.0.0.x peers to send messages')
    parser.add_argument('-cID', '--chainID', default="", help='identify net by genesis blockHash')
    parser.add_argument('-nID', '--netID', default=1, type=int, help='identify net by pre-defined ID 0: Academy, 1: NAPCoin')
    parser.add_argument('-miP', '--minPeers', default=1, type=int, help='minimum number of peers to maintain if posible')
    parser.add_argument('-maP', '--maxPeers', default=1, type=int, help='max peer communication, if more peers are known')
    parser.add_argument('-trk', '--canTrack', default="N", help='use delay option to hold GET/POST until visualisation is updated')
    parser.add_argument('-mod', '--mode', default="Y", help='modus of miner to work, e.g. y=await user to trigger mining')
    parser.add_argument('-deb', '--asDebug', default="N", help='activate the debug GUI for the node instead of the user GUI')

    args = parser.parse_args()
    port = args.port
    if (port < 1024) or (port > 65535):
        print("No valid port ...." + str(port))
        sys.exit(-1)

    host = args.host
    cID = args.chainID
    useNet = args.netID
    print("Started")
    m_info['nodeId'] = genNodeID()
    cnt = 0
    if cID != "":
        for gen in m_genesisSet:
            cnt = cnt+1
            if gen['blockHash'] == cID:
                useNet = cnt

    if (useNet < 0) or (useNet >= len(m_genesisSet)):
        print("No valid net identified ....")
        sys.exit(-1)

    m_info['nodeUrl'] = "http://"+host+":"+str(port)
    m_info['chainId'] = m_genesisSet[useNet]['blockHash']
    m_cfg['minPeers'] = args.minPeers
    m_cfg['maxPeers'] = args.maxPeers
    m_cfg['mode'] = args.mode
    if args.canTrack == "Y":
        m_cfg['canTrack'] = True
        print("Animation delay activated")

    if args.asDebug == "Y":
        m_cfg['debug'] = True
        print("Debug GUI activated")
        m_cfg['type'] = "*"+m_cfg['type']

    #if we want to have navkov as peer for testing blocks enable next line can soon be removed
    #c_peer.setPeersAs("https://stormy-everglades-34766.herokuapp.com",80)
    #TODO search for 'navkov has wrong nodeUrl info' and enable the modeUrl correction as well
    print(m_cfg)
    print(m_info)
    # maxBytes to small number, in order to demonstrate the generation of multiple log files (backupCount).
    # handler = RotatingFileHandler('app'+str(host)+'_'+m_cfg['type']+'.log', maxBytes=1000000, backupCount=3)
    # # getLogger(__name__):   decorators loggers to file + werkzeug loggers to stdout
    # # getLogger('werkzeug'): decorators loggers to file + nothing to stdout
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.INFO)
    # log.addHandler(handler)
    return host, port, args.connect
