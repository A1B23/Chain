from project.models import defAdr, defHash, defPub, defSig

m_Blocks = []
m_newBlock = {}
m_pendingTX = {}
m_BufferMinerCandidates = {}
minBlockReward = 5000000 #all measured in microcoins
maxSameBlockPerMiner = 5
#m_peerToBlock = {}


m_stats = {
    "m_minFee": 10, #microcoins
}

m_coinBase = {
    "from": defAdr,     # fix
    "to": defAdr,       # miners address received via GET
    "value": -1,                                       # sum of all transaction fees
    "fee": 0,                                               # miners don't pay fees, so zero
    "dateCreated": "2018-02-10T17:53:48.972Z",              # coinBase creation timestamp, mining time must be later
    "data": "coinbase tx",
    "senderPubKey": defPub,                         # fix for 'out of the air money
    "transactionDataHash": defHash,          #updated each time as timestamp changes
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
    "transferSuccessful": True
}

m_staticBalanceInfo = {
    "curBalance": 0,
    "createdInBlock": -1,
    "confirm": []
}

m_candidateMiner = {
    "index": 1,
    "transactionsIncluded": 0,
    "difficulty": 5,
    "expectedReward": minBlockReward , #even if changed here, the code corrects again
    "rewardAddress": "",
    "blockDataHash": defHash
}

m_minerFoundNonce = {
    "blockDataHash": defHash,
    "dateCreated": "2018-05-20T04:36:36Z",
    "nonce": "735530",
    "blockHash": defHash
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
    "nodeUrl": "" ,#""http://chain-node-03.herokuapp.com:5555",
    "blockHash": defHash #added by PDPCCoin to reduce bounce effects
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
    #new PDPCCoin generated with 2 faucet and two sponsors
    {
        "blockDataHash": "f1bbf9dc627a813c1ee02dcbd2f094a9d7e59aec4cda4bb2a2b85bd917756770",
        "blockHash": "a74bab3e391e07dca560847f261285635be36fab40716053b0ea4067be69ae27",
        "dateCreated": "2018-07-15T10:59:40.720Z",
        "difficulty": 0,
        "index": 0,
        "minedBy": "0000000000000000000000000000000000000000",
        "nonce": 0,
        "transactions": [
          {
            "data": "Genesis Faucet: PDPC faucet 1",
            "dateCreated": "2018-07-15T10:59:40.532Z",
            "fee": 0,
            "from": "0000000000000000000000000000000000000000",
            "minedInBlockIndex": 0,
            "senderPubKey": "00000000000000000000000000000000000000000000000000000000000000000",
            "senderSignature": [
              "0000000000000000000000000000000000000000000000000000000000000000",
              "0000000000000000000000000000000000000000000000000000000000000000"
            ],
            "to": "f8a32f5bc22d7557c23e498c59b76d7f68d1bff7",
            "transactionDataHash": "fb5bd02314b50a5e78e8c4a4debb521c502262566e87576a3e2832bc3ac5227e",
            "transferSuccessful": True,
            "value": 1000000000
          },
          {
            "data": "Genesis Faucet: PDPC faucet 2",
            "dateCreated": "2018-07-15T10:59:40.720Z",
            "fee": 0,
            "from": "0000000000000000000000000000000000000000",
            "minedInBlockIndex": 0,
            "senderPubKey": "00000000000000000000000000000000000000000000000000000000000000000",
            "senderSignature": [
              "0000000000000000000000000000000000000000000000000000000000000000",
              "0000000000000000000000000000000000000000000000000000000000000000"
            ],
            "to": "6d8b355740dd9ae894251eb67a78a60ec5c7c9b3",
            "transactionDataHash": "a64f4a9b1f267525b00ad4477c6c551a2cb5929962465dea7c546a17e4ef8704",
            "transferSuccessful": True,
            "value": 1000000
          },
          {
            "data": "Genesis TX: Lucky draw winner if ever found",
            "dateCreated": "2018-07-15T10:59:40.720Z",
            "fee": 0,
            "from": "0000000000000000000000000000000000000000",
            "minedInBlockIndex": 0,
            "senderPubKey": "00000000000000000000000000000000000000000000000000000000000000000",
            "senderSignature": [
              "0000000000000000000000000000000000000000000000000000000000000000",
              "0000000000000000000000000000000000000000000000000000000000000000"
            ],
            "to": "13a1e69b6176052fcc4a1248f1c5a91dea308ca9",
            "transactionDataHash": "1fe10e3a7418257fc59b00f81f382859e8ffccd4cacd394e7f25e02c5fd827aa",
            "transferSuccessful": True,
            "value": 1112
          }
        ]
      },
    #OldNAPCoin
    # {
    #     "index":0,
    #     "transactions": [{
    #         "from": defAdr,
    #         # faucet address
    #         "to": defAdr,
    #         "value": 1000000000000,
    #         "fee": 0,
    #         "dateCreated": defGenesisDate,
    #         "data": "genesis tx",
    #         "senderPubKey": defPub,
    #         #changes with new faucet address
    #         "transactionDataHash": "8a684cb8491ee419e7d46a0fd2438cad82d1278c340b5d01974e7beb6b72ecc2",
    #         "senderSignature": [defSig, defSig],
    #         "minedInBlockIndex": 0,
    #         "transferSuccessful": True
    #     }],
    #     "difficulty":0,
    #     "minedBy":defAdr,
    #     # changes with new faucet address
    #     "blockDataHash":"15cc5052fb3c307dd2bfc6bcaa057632250ee05104e4fb7cc75e59db1a92cefc",
    #     "nonce":0,
    #     "dateCreated":"2018-01-01T00:00:00.000Z",
    #     # changes with new faucet address
    #     "blockHash":"c6da93eb4249cb5ff4f9da36e2a7f8d0d61999221ed6910180948153e71cc47f"
    # }
]

m_AllBalances = {}
m_balHistory = {
    #blockNumber: m_singleBalance
}
m_completeBlock = {}


