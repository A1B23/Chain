from project.pclass import c_peer
from project.models import m_cfg, m_info
from project.nspec.blockchain.modelBC import *
from project.utils import *
from logging.handlers import RotatingFileHandler
import logging


def init(parser):
    parser.add_argument('-p', '--port', default=5555, type=int, help='port to listen on')
    parser.add_argument('-hip', '--host', default="127.0.0.2", help='hostname/IP')
    parser.add_argument('-con', '--connect', default="4", help='list of 127.0.0.x peers to send messages')
    parser.add_argument('-cID', '--chainID', default="", help='identify net by genesis blockHash')
    parser.add_argument('-nID', '--netID', default=1, type=int, help='identify net by pre-defined ID 0: Academy, 1: NAPCoin')
    parser.add_argument('-minP', '--minPeers', default=1, type=int, help='minimum number of peers to maintain if posible')
    parser.add_argument('-maxP', '--maxPeers', default=1, type=int, help='max peer communication, if more peers are known')

    args = parser.parse_args()
    port = args.port
    host = args.host
    #skey = args.sharedKey
    cID = args.chainID
    useNet = args.netID
    print("Started")
    m_info['nodeId']=genNodeID()
    cnt = 0
    if (cID != ""):
        for gen in m_genesisSet:
            cnt= cnt+1
            if (gen['blockHash']==cID):
                useNet = cnt

    if (useNet <0) or (useNet >= len(m_genesisSet)):
        print("No valid net identified ....")
        sys.exit(-1)

    if (port <1024) or (port > 100000):
        print("No valid port ....")
        sys.exit(-1)
    m_info['nodeUrl'] = "http://"+host+":"+str(port)
    m_info['chainId'] = m_genesisSet[useNet]['blockHash']
    m_cfg['minPeers']= args.minPeers
    m_cfg['maxPeers']= args.maxPeers
    #setSharedKey(skey) # -1= not shared, 0 used preconfigured, 1 create based on given nonce
    c_peer.setPeersAs(args.connect, port)
    #if we want to have navkov as peer for testing blocks enable next line can soon be removed
    #c_peer.setPeersAs("https://stormy-everglades-34766.herokuapp.com",80)
    #search for 'navkov has wrong nodeUrl info' and enable the modeUrl correction as well
    print(m_cfg)
    print(m_info)
    # maxBytes to small number, in order to demonstrate the generation of multiple log files (backupCount).
    # handler = RotatingFileHandler('app'+str(host)+'_'+m_cfg['type']+'.log', maxBytes=1000000, backupCount=3)
    # # getLogger(__name__):   decorators loggers to file + werkzeug loggers to stdout
    # # getLogger('werkzeug'): decorators loggers to file + nothing to stdout
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.INFO)
    # log.addHandler(handler)
    return host, port