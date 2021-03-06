# This file contains data models and references used by multiple player, like node, wallet
# etc. The modules may have their own model data structures as well
import re

m_debug = {
    'file' : 0
}

defSig = "0000000000000000000000000000000000000000000000000000000000000000"
defPub = "00000000000000000000000000000000000000000000000000000000000000000"
defAdr = "0000000000000000000000000000000000000000"
defNodeID = "000000000000000000000000"
defHash = "f24d66fe6fd6856484c72a223507f7f048c17d8ca152e02809a6bbb0b7b33335"

re_addr = re.compile("^[0-9a-f]{"+str(len(defAdr))+"}$")
re_pubKey = re.compile("^[0-9a-f]{"+str(len(defPub))+"}$")

m_peerSkip = []
m_Delay = []

m_visualCFG = {"active": False, "pattern": []}

m_peerInfo = {
    "numberFail": 0,
    "active": False,
    "nodeId": "Pending...",
    "wrongType": 0,
    "source": "startup"
}

m_TemplateSingleBalance = {
  # "safeBalance": "not provided: this is a matter of user preference, it should be done by wallet, not the node",   #deviates from confirm count 6+
  "confirmedBalance": 0,
  "pendingBalance": 0
}


m_cfg = {
    "activePeers": {},    # number of bilateral working peers
    "shareToPeers": {},    # number of bilateral working peers
    "peerOption": {},  # uses peerInfo
    "peerAvoid": [],
    "maxPeers": -1,
    "minPeers": -1,
    "peerDrop": 5,  # how often can a peer not reply when checked
    "maxWrong": 3,  # how many wrong type replies do we accept before we drop and move to avoid
    "newPeer": [],
    "peersCheckDelay": 45,  # default seconds to wait to check all peers again
    # 0 means all commands accepted, POST blocks against get
    # 1 means we are reloading the entire blocks at startup, so until this is finished, no reply
    # 2 means we are checking for peers again... default for starting up
    "chainInit": False,
    "checkingPeers": True,
    "canTrack": False,
    "debug": False,
    "shutdown": False,
    "type": "TBD",
    "chainLoaded": False,
    "checkingChain": False
}

m_info = {
    "about": "not yet",
    "nodeId": "not yet",
    "chainId": -1,  # is set during init to th e genesis block hash
    "nodeUrl": "m",
    "peers": 0,
    "currentDifficulty": 5,
    "blocksCount": 0,
    "cumulativeDifficulty": 0,
    "confirmedTransactions": 0,
    "pendingTransactions": 0,
    "type": "TBD",
}


useNet = 1

#simple locking to prevent GET/POST collision
m_simpleLock = []
m_isPOST = []

m_permittedGET = [
    "/info",  # TODO need to bring up???
    "/debug$",
    "/debug/reset-chain",
    "/blocks$",
    "/blocks/[0-9]+$",
    "/transactions/pending",
    "/transactions/confirmed",
    "/transactions/[0-9a-fA-F]+$",
    "/balances",
    "/address/[0-9a-fA-F]+/transactions",
    "/address/[0-9a-fA-F]+/balance",
    "/peers",
    "/listNodes",
    "/mining/get-mining-job/[0-9a-fA-F]+$"
]

m_permittedPOST = [
    "/transactions/send",
    "/peers/connect",
    "/peers/notify-new-block",
    "/mining/submit-mined-block"
]

m_signed_txn_order = [
    "from",
    "to",
    "value",
    "fee",
    "dateCreated",
    "data",
    "senderPubKey",
    "transactionDataHash",
    "senderSignature"
]

m_transaction_order = [
    "from",
    "to",
    "value",
    "fee",
    "dateCreated",
    "data",
    "senderPubKey"
]

m_txorderForBlockHash = [
    "from",
    "to",
    "value",
    "fee",
    "dateCreated",
    "data",
    "senderPubKey"
    "transactionDataHash",
    "senderSignature",
    "minedInBlockIndex",
    "transferSuccessful"
]

m_candidateMiner_order = [
    "index",
    "transactions",
    "difficulty",
    "prevBlockHash",
    "minedBy"
]

m_Miner_order = [
    "blockDataHash",
    "dateCreated",
    "nonce"
]




