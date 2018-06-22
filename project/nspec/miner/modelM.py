candidate = {}

cfg = {
    'zero_string': '00000000000000000000000000000',
    'maxNonce': 2147483647,  #typical Java max, so stick to it to avoid endless search
    'peer': -1,
    'miner_address': -1,
    'mode': 'n', #by default keep mining, if started with 'y', miner will wait for user
    'scanning': 10,
    'lastHash': ""
}

data = {
    "blockDataHash": -1,
    "dateCreated": -1,
    "nonce": -1,
    "blockHash": -1
}