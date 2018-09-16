import json
import ast
import requests
from time import sleep
from sys import exit

runSequence = ['doubleSpend']

urls = {
    "w52": "http://127.0.0.52:5555",
    "f92": "http://127.0.0.92:5555",
    "n04": "http://127.0.0.4:5555",
    "n02": "http://127.0.0.2:5555"
}

cmds = {
    'doubleSpend': [
        ("f92", "GET", "/wallet/list/wallet/genesisPDPCCoin", 200),
        ("Wallet gives the node 100", "inf1"),
        ("f92", "POST", "/wallet/transfer",
         {"walletDest": "", "receiver": ["pubKey", "c2e16fe3302a68c75f978429648066b7832765582583ed23fdc207cf8a2052c30"],
          "fee": 10, "amount": 100, "source": ["address", "f8a32f5bc22d7557c23e498c59b76d7f68d1bff7"],
          "walletSrc": "genesisPDPCCoin", "walletPW": "", "msg": "", "user": "genesisPDPCCoin"}, 201),
        ("w52", "GET", "/wallet/list/wallet/User", 200),
        ("Check the balance in the wallet is pending", "inf"),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 0, "pendingBalance": 100}),
        ("Mining is now required to complete the TX from faucet to node", "inf"),
        ("Mining completed ", "act"),
        ("Check that the balance is now confirmed", "inf1"),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 100, "pendingBalance": 0}),
        ("Cut the node connections", "inf1"),
        ("n04", "POST", "/peers/disconnect", {"peerUrl": "http://127.0.0.2:5555"}, 200),
        ("n02", "POST", "/peers/disconnect", {"peerUrl": "http://127.0.0.4:5555"}, 200),
        ("Wallet now sends first transaction to itself (yeah, not a smart double spend...) at first node", "inf1"),
        ("w52", "POST", "/wallet/transfer",
            {"receiver":["publicKey", "7e15c2789a6af71ab416cac27dd939aaa290992f187dc95acf8145164436d4550"],
             "walletDest": "withk", "fee":20, "amount":50,
             "source":["publicKey", "c2e16fe3302a68c75f978429648066b7832765582583ed23fdc207cf8a2052c30"],
             "walletSrc": "withk", "walletPW": "KeyPassword", "msg": "selftransfer1", "user": "User"}, 201),
        ("n04", "GETx0", "/transactions/pending", 200, {"data": "selftransfer1",
                    "from": "e8d45ee24d2131ce685f3dd76d352f2ba9e6f2e1",
                    "to": "11c00799d4f7c04868482e4d75c8a1a8db46d354", "value": 50}),
        ("Node accepted TX correctly, verify balance", "inf"),
        ("Values are 100, -20, because the 50 going out come in again, put 20 fees go away", "inf"),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 100, "pendingBalance": -20}),
        ("Switch the wallet connection to the other node", "inf"),
        ("w52", "POST", "/peers/disconnect", {"peerUrl": "http://127.0.0.4:5555"}, 200),
        ("w52", "POST", "/peers/connect", {"peerUrl": "http://127.0.0.2:5555"}, 200),
        ("Connection from wallet to node is there, can pre-mine other node already", "act"),
        ("Wallet verifies that this new node does not know about first TX, so balance is still higher", "inf"),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 100, "pendingBalance": 0}),
        ("Wallet now sends doublespend TX to itself (yeah, not a smart double spend...) at second node", "inf1"),
        ("w52", "POST", "/wallet/transfer",
                    {"receiver":["publicKey", "7e15c2789a6af71ab416cac27dd939aaa290992f187dc95acf8145164436d4550"],
                     "walletDest": "withk", "fee":20, "amount":80,
                     "source":["publicKey", "c2e16fe3302a68c75f978429648066b7832765582583ed23fdc207cf8a2052c30"],
                     "walletSrc": "withk", "walletPW": "KeyPassword", "msg": "doublespend", "user": "User"}, 201),
        ("Verify that node has accepted doubleSpend attempt", "inf"),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 100, "pendingBalance": -20}),
        ("Confirm that it is a different TX than the other node", "inf"),
        ("n02", "GETx0", "/transactions/pending", 200, {"data": "doublespend",
                                            "from": "e8d45ee24d2131ce685f3dd76d352f2ba9e6f2e1",
                                            "to": "11c00799d4f7c04868482e4d75c8a1a8db46d354", "value": 80}),
        ("Mine the first TX", "act"),
        ("Reconnect the doublespend node to the previous node to get its block and remove doublespend", "inf1"),
        ("n02", "POST", "/peers/connect", {"peerUrl": "http://127.0.0.4:5555"}, 200),
        ("n04", "POST", "/peers/connect", {"peerUrl": "http://127.0.0.2:5555"}, 200),
        ("Wait for block being synchronised", "act"),
        ("The node should now have a unsuccessful TX", "inf1"),
        ("n02", "GETx0", "/transactions/pending", 200, {"data": "doublespend",
                                                        "transferSuccessful": False, "value": 80}),
        ("w52", "GET", "/wallet/list/allbalance/withk/User", 200, {"confirmedBalance": 80, "pendingBalance": 0}),
        ("Confirm that instead of 80 coins only 50 coins moved to the other key","inf1"),
        ("The key sending the 50 has now 30 as 100-50-20 = 30","inf"),
        ("w52", "GET",
         "/wallet/list/balance/publicKey/withk/c2e16fe3302a68c75f978429648066b7832765582583ed23fdc207cf8a2052c30/User",200,
         {"confirmedBalance": 30, "pendingBalance": 0}),
        ("The key receiving the 50 has now 30, not the 80 which the doublespend TX would have given","inf"),
        ("The balance also confirms that the second TX fee was not counted", "inf"),
        ("w52", "GET",
         "/wallet/list/balance/publicKey/withk/7e15c2789a6af71ab416cac27dd939aaa290992f187dc95acf8145164436d4550/User",
         200,
         {"confirmedBalance": 50, "pendingBalance": 0}),
        ("Mine the block to see the unsuccessful TX is mined in the block (makes error, so 1 error ok!)","act"),
        ("n02", "GET", "/blocks/3", 200, {"transactions": {}}),
    ]
}

totalErr = []


def pin(mes):
    print(mes)
    totalErr.append(mes)


def doPOST(url, data):
    print("POST " + url)
    return requests.post(url=url, json=data, headers={'accept': 'application/json'})


def doGET(url):
    print("GET: " + url)
    return requests.get(url=url, headers={'accept': 'application/json'})


def runSeq():
    try:
        for seq in runSequence:
            print("********************** Sequence starting: " + seq)
            for tst in cmds[seq]:
                res = 3
                if tst[1] == "POST":
                    res = res + 1
                if len(tst) > res + 1:
                    for exp in tst[res+1]:
                        print("("+tst[0]+" expects / " + str(exp) + ": " + str(tst[res+1][exp])+")")
                res = 3
                idx = -1
                if tst[1] == "GET":
                    ret = doGET(urls[tst[0]] + tst[2])
                elif tst[1].startswith("GETx"):
                    ret = doGET(urls[tst[0]] + tst[2])
                    idx = int(tst[1][4:])
                elif tst[1] == "POST":
                    ret = doPOST(urls[tst[0]] + tst[2], tst[3])
                    res = res + 1
                elif tst[1] == "act":
                    print("!!!! Confirm and press <Enter> once: '" + tst[0] + "' ... ")
                    input().lower()
                    print("Continuing...")
                    continue
                elif tst[1] == "inf":
                    print("{{ " + tst[0] + " }} ")
                    continue
                elif tst[1] == "inf1":
                    print("... " + tst[0] + " ... ")
                    sleep(2)
                    continue
                if len(tst) > res:
                    if ret.status_code != tst[res]:
                        pin("----- Unexpected status code: " + str(ret.status_code))
                if len(tst) > res + 1:
                    if idx > -1:
                        txt = ret.text.replace(": false", ": False").replace(": true", ": True")
                        x = ast.literal_eval(txt)
                        if len(x) < idx:
                            pin("----- Answer too short, expected " + str(idx))
                            continue
                        js = x[idx]
                    else:
                        js = json.loads(ret.text)
                    for exp in tst[res+1]:
                        if exp not in js:
                            pin("----- Missing item: "+exp)
                            continue
                        if js[exp] != tst[res+1][exp]:
                            pin("----- Invalid value " + str(js[exp]) + " instead of " + str(tst[res+1][exp]) + " for " + exp)
                            continue
                        print("+ " + str(exp) + ": " + str(js[exp]))

            print("**********************  Sequence completed: " + seq)
            print("Total issues: " + len(totalErr))
            for err in totalErr:
                print(err)
    except Exception:
        print("***************************************************************")
        print("Exception occurred, ensure the nodes are all up and running ...")
        print("***************************************************************")
        print("Total issues: " + len(totalErr))
        for err in totalErr:
            print(err)
        exit(-1)


runSeq()
