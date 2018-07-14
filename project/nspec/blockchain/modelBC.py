# Your models here.
from project.models import defAdr,defNodeID,defHash,defPub,defSig,m_TemplateSingleBalance,defFaucet,defGenesisDate
from copy import deepcopy

m_Blocks = []
m_newBlock = {}
m_pendingTX = {}
m_BufferMinerCandidates = {}
minBlockReward = 50000
maxSameBlockPerMiner = 5
m_peerToBlock = {}


m_stats = {
    "m_minFee": 10,
    "m_cumulativeDifficulty": 0
}

m_coinBase = {
    "from": defAdr,     # fix
    "to": defAdr,       # miners address received via GET
    "value": -1,                                       # sum of all transaction fees
    "fee": 0,                                               # miners don't pay fees, so zero
    "dateCreated": "2018-02-10T17:53:48.972Z",              # coinBase creation timestamp, mining time must be later
    "data": "coinbase tx",
    "senderPubKey": defPub,                         # fix for 'out of the air money
    "transactionDataHash": "4dfc3e0ef89ed603ed54e47435a18b…176a", #updated each time as timestamp changes
    "senderSignature": [defSig, defSig],
    "transferSuccessful": True,                             # we predict success or it will be deleted anyway
}

m_transaction = {
    "from": defAdr,
    "to": defAdr,
    "value": 0,
    "fee": 0,
    "dateCreated":  "2018-02-10T17:53:48.972Z",
    "data": "coinbase tx",
    "senderPubKey": defPub,
    # to insert "transactionDataHash": "needtocalculatethehashhere",
    "senderSignature": [defSig, defSig],
    #to insert" minedInBlockIndex": 1,
    # to insert "transferSuccessful": True,
}

m_staticTransactionRef = {
    "from": defAdr,
    "to": defAdr,
    "value": -1,
    "fee": -1,
    "dateCreated":  "2018-02-10T17:53:48.972Z",
    "data": "Coinbase TX",
    "senderPubKey": defPub,
    "transactionDataHash": "needtocalculatethehashhere",
    "senderSignature": [defSig, defSig],
    "minedInBlockIndex": 0,
    "transferSuccessful": True,
}

m_staticBalanceInfo = {
    "curBalance": -1,
    "createdInBlock": -1,
    "confirm": []
}

m_candidateMiner = {
    "index": 1,
    "transactionsIncluded": 0,
    "difficulty": 5,
    "expectedReward": minBlockReward , #even if changed here, the code corrects again
    "rewardAddress": "",
    "blockDataHash": "15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
}

m_minerFoundNonce = {
    "blockDataHash": "15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
    "dateCreated": "2018-05-20T04:36:36Z",
    "nonce": "735530",
    "blockHash": "0000020135f1c30b68733e9805f52fdc758fff4b07149929edbd995d30167ae1"
}

m_static_emptyBlock = {
    "index": 0,
    "transactions": [{}],   #reserve the first for coinbase
    "difficulty": 5,
    "prevBlockHash": defHash,
    "minedBy": defAdr,
    # changes with new faucet address
    "blockDataHash":"15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
    ## next three need to be added after miner got his block
    # also need to comparet he blockDataHash being the same!!!!
    #"nonce":0,
    #"dateCreated":"2018-01-01T00:00:00.000Z",
    # changes with new faucet address
    #"blockHash":"c6da93eb4249cb5ff4f9da36e2a7f8d0d61999221ed6910180948153e71cc47f"
}

m_candidateBlock = {
    "index": 0,
    "transactions": [{}], # first is empty for coinbase
    "difficulty": 5,
    "minedBy": defAdr,
    # changes with new faucet address
    "blockDataHash": defHash,
    ## next three need to be added after miner got his block
    # also need to comparet he blockDataHash being the same!!!!
    #"nonce":0,
    #"dateCreated":"2018-01-01T00:00:00.000Z",
    # changes with new faucet address
    #"blockHash":"c6da93eb4249cb5ff4f9da36e2a7f8d0d61999221ed6910180948153e71cc47f"
}

m_informsPeerNewBlock = {
    "blocksCount": -1,
    "cumulativeDifficulty": -1,
    "nodeUrl": "" #""http://chain-node-03.herokuapp.com:5555"
}

m_genesisSet = [
    #Academy net
    {"index":0,"transactions":[{"from":"0000000000000000000000000000000000000000",
                                "to":"f3a1e69b6176052fcc4a3248f1c5a91dea308ca9",
                                "value":1000000000000,"fee":0,"dateCreated":"2018-01-01T00:00:00.000Z",
                                "data":"genesis tx",
                                "senderPubKey":"00000000000000000000000000000000000000000000000000000000000000000",
                                "transactionDataHash":"8a684cb8491ee419e7d46a0fd2438cad82d1278c340b5d01974e7beb6b72ecc2",
                                "senderSignature":["0000000000000000000000000000000000000000000000000000000000000000",
                                                   "0000000000000000000000000000000000000000000000000000000000000000"],
                                "minedInBlockIndex":0,"transferSuccessful":True}],
                    "difficulty":0,"minedBy":"0000000000000000000000000000000000000000",
                    "blockDataHash":"15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
                    "nonce":0,"dateCreated":"2018-01-01T00:00:00.000Z",
                    "blockHash":"c6da93eb4249cb5ff4f9da36e2a7f8d0d61999221ed6910180948153e71cc47f"
    },
    #NAPCoin
    {
        "index":0,
        "transactions": [{
            "from": defAdr,
            # faucet address
            "to": defFaucet,
            "value": 1000000000000,
            "fee": 0,
            "dateCreated": defGenesisDate,
            "data": "genesis tx",
            "senderPubKey": defPub,
            #changes with new faucet address
            "transactionDataHash": "8a684cb8491ee419e7d46a0fd2438cad82d1278c340b5d01974e7beb6b72ecc2",
            "senderSignature": [defSig, defSig],
            "minedInBlockIndex": 0,
            "transferSuccessful": True
        }],
        "difficulty":0,
        "minedBy":defAdr,
        # changes with new faucet address
        "blockDataHash":"15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
        "nonce":0,
        "dateCreated":"2018-01-01T00:00:00.000Z",
        # changes with new faucet address
        "blockHash":"c6da93eb4249cb5ff4f9da36e2a7f8d0d61999221ed6910180948153e71cc47f"
    }
]

m_AllBalances = {}
m_balHistory = {
    #blockNumber: m_singleBalance
}
m_candidateBlockBalance = {}
m_completeBlock = deepcopy(m_genesisSet[1])
m_added = {
    "prevBlockHash": 0
}
m_completeBlock.update(m_added)


