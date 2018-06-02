# Your models here.

defSig ="0000000000000000000000000000000000000000000000000000000000000000"
defPub = "00000000000000000000000000000000000000000000000000000000000000000"
defAdr ="0000000000000000000000000000000000000000"
defNodeID="000000000000000000000000"
defHash="f24d66fe6fd6856484c72a223507f7f048c17d8ca152e02809a6bbb0b7b33335"


m_peerSkip = []

m_peerInfo = {
    "numberFail": 0,
    "active": False,
    "nodeId": "Pending..."
}

m_SingleBalance = {
  "safeBalance": 0,   #confirm count 6+
  "confirmedBalance": 1000000,    #TODO set to zero after testing, currently it is needed to allow the balance issue
  "pendingBalance": 0
}


m_cfg = {
    "type": "TBD",
    "peers": {},
    "maxPeers": -1,
    "minPeers": -1,
    "peerDrop" : 5, # how often can a peer not reply when checked
    "peersCheck": 10, # TODO how many second to wait to check all peers again
    # 0 means all commands accepted, POST blocks against get
    # 1 means we are reloading the entire blocks at startup, so until this is finished, no reply
    # 2 means we are checking for peers again... default for starting up
    "statusChain": False,
    "statusPeer": True
}

m_info = {
    "about": "NAPCoin",
    "nodeId": "1a22d39b2f",
    "chainId": 1, #indx into the coinbase set 0: Academy 1: NapCoin
    "nodeUrl": "m",
    "peers": 0,
    "currentDifficulty": 5,
    "blocksCount": 0,
    "cumulativeDifficulty": 0,
    "confirmedTransactions": 0,
    "pendingTransactions": 0
}


useNet=1

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
    "/listNodes",  # TODO test only
    "/mining/get-mining-job/[0-9a-fA-F]+$"
]

m_permittedPOST = [
    "/transactions/send",  # TODO POST
    "/peers/connect",  # TODO POST
    "/peers/notify-new-block",  # TODO POST
    "/mining/submit-mined-block"  # TODO POST
]

