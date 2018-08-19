newCandidate = {}

cfg = {
    'zero_string': '00000000000000000000000000000',
    'maxNonce': 2147483640,  #typical Java max, so stick to it to avoid endless search
    'findNonce': False,
    'waitAck': False,
    'done': True,
    'blockHash': "",
    'address': "",
    'countSame': 0,
    'refresh': 5,   # this may in future be adjusted to match the difficulty and creation rate of TXs
    'foundSolution': False,
    'maxNonceTry': 2147483640/2, # same as maxNonce/2, in case we see a possibility/need to limit tries
    'mineSend': 0,
    'nonceCnt': 0

}
