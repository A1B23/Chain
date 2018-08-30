from project.nspec.wallet.transactions import generate_private_key, private_key_hex_to_int, private_key_to_public_key
from project.nspec.wallet.transactions import get_pub_key_compressed, public_key_compressed_to_address,helper_sha256
from project.pclass import c_peer
from project.models import m_transaction_order, defSig
from pycoin.ecdsa import generator_secp256k1, sign
from project.utils import setOK, errMsg, putDataInOrder, getTime
import sqlite3
from project.nspec.wallet.modelW import m_db, regexWallet, m_balanceData
from contextlib import closing
import re
from project.nspec.blockchain.verify import verifyAddr
from copy import deepcopy


class wallet:
    def createKey(self, wal, name, user):
        # (wal,"prK","pK","@","*","000")
        prk = generate_private_key()
        priv_key_int = private_key_hex_to_int(prk)
        pub_key = private_key_to_public_key(priv_key_int)
        pub_key_compressed = get_pub_key_compressed(pub_key)
        pub_addr = public_key_compressed_to_address(pub_key_compressed)
        if (name == ""):
            name = pub_addr
        return (wal,prk,pub_key_compressed,pub_addr,name,"000",user)

    def createWallet(self, json):
        wal = json['name']
        if (self.hasWallet(wal)):
            return errMsg("Creating Wallet '" + wal + "' failed.")
        return self.addKeysToWallet(json, wal)

    def createKeys(self, json):
        wal = json['name']
        if (not self.hasWallet(wal)):
            return errMsg("Wallet '" + wal + "' not found.")
        cmd = "SELECT DISTINCT KName from Wallet WHERE User='"+json['user']+"' AND WName='"+wal+"' AND ("
        knames = ""
        pattern = re.compile(regexWallet)
        for idx in range(0, json['numKeys']):
            if (len(json['keyNames']) > idx):
                if (len(knames)>0):
                    knames = knames + " OR "
                if (not pattern.match(json['keyNames'][idx])):
                    return errMsg("Invalid key name, use a-z, aA-Z and numbers only.")
                knames = knames + "KName='" + json['keyNames'][idx] + "'"
        if (len(knames)>0):
            cmd = cmd + knames + ")"
            rpl = self.doSelect(cmd)
            if (len(rpl)>0):
                cmd = "Duplicate name(s):"
                for nam in rpl:
                    cmd = cmd + nam + ","
                return errMsg(cmd + " no key(s) generated")

        return self.addKeysToWallet(json, wal)

    def addKeysToWallet(self, json, wal):
        mes,code = self.addKeysToWalletBasic(json,wal)
        if code == 200:
            return setOK(mes)
        return errMsg(mes, code)

    def addKeysToWalletBasic(self, json, wal):
        try:
            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                pattern = re.compile(regexWallet)
                if (not pattern.match(wal)):
                    return "Invalid wallet name, use a-z, aA-Z and numbers only.", 400

                if (not pattern.match(json['user'])):
                    return "Invalid wallet name, use a-z, aA-Z and numbers only.", 400

                if (json['numKeys'] <= 0) or (json['numKeys'] > 5):
                    return "Invalid number of keys provided.", 400
                cur = con.cursor()
                keys = []
                s = set(json['keyNames'])
                if (len(s) != len(json['keyNames'])):
                    return "Invalid name list for keys, contains duplicates", 400
                for idx in range(0, json['numKeys']):
                    name = ""   #empty names are resolved to address
                    if (len(json['keyNames'])>idx):
                        name = json['keyNames'][idx]
                    keys.append(self.createKey(wal, name, json['user']))

                cur.executemany("INSERT INTO Wallet (WName,privKey,pubKey,address,KName,ChkSum,User) VALUES(?, ?, ?, ?,?,?,?)", keys)
                con.commit()
                return str(len(s))+" keys generated for wallet " + wal, 200
        except Exception:
            return "Creating Wallet " + wal + " failed.", 400

    def listAllWallets(self, user):
        return self.doSelect("SELECT DISTINCT WName from Wallet WHERE User='"+user+"'")

    def hasWallet(self,wallet):
        return (len(self.doSelect("SELECT DISTINCT WName from Wallet WHERE WName='"+wallet+"'")) > 0)

    def getAllWallets(self,user):
        return setOK({"walletList": self.listAllWallets(user)})

    def doSelect(self, cmd):
        with closing(sqlite3.connect(m_db['DATABASE'])) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(cmd)
            keys = []
            for row in cur.fetchall():
                keys.extend(row)
            return keys

    def collectKeyBalance(self, addr):
        resps = c_peer.sendGETToPeers("address/" + addr + "/balance")
        # TODO should we compare all replies??? Not really??? Just take first one?
        return resps[0]

    def getKeyBalance(self, params):
        keys = self.getDataFor([params['sel'], params['key']], params['wallet'], "", params['user'])
        if (len(keys)>4):
            respText, respCode = self.collectKeyBalance(keys[4])
            if (respCode == 200):
                return setOK(respText)
            else:
                return errMsg(respText['errorMsg'], respCode)
        return errMsg("Invalid parameters provided")

    def getAllKeys(self, params):
        wal = 'unidentified'
        try:
            wal = params['wallet']
            pattern = re.compile(regexWallet)
            if (not pattern.match(wal)):
                return errMsg("Invalid wallet name.")

            cmd = "SELECT"
            sel = False
            if ("py" in params['sel']):
                cmd = cmd + " 'pubkey:' || pubKey,"
                sel = True

            if ("ay" in params['sel']):
                cmd = cmd + " 'addr:' || address,"
                sel = True

            if ("ny" in params['sel']):
                cmd = cmd + " 'name:' || KName"
                sel = True

            if (sel == False):
                cmd = cmd + " pubKey, address, KName"
            else:
                if (cmd.endswith(",")):
                    cmd = cmd[0:-1]

            cmd = cmd + " FROM Wallet WHERE WName='" + wal + "'"
            return setOK({"keyList": self.doSelect(cmd)})

        except Exception:
            return errMsg("Collecting keys for wallet " + wal + " failed.")

    def getDataFor(self, keyRef, wallet, limit, user):
        cmd = "SELECT "
        if (limit == ""):
            cmd = cmd + "* "
        else:
            cmd = cmd + limit

        cmd = cmd + " from Wallet where WName='" + wallet + "' AND "
        if (keyRef[0] == "address"):
            cmd = cmd + "address='"+keyRef[1]
        elif (keyRef[0] == "pubKey"):
            cmd = cmd + "pubKey='"+keyRef[1]
        elif (keyRef[0] == "name"):
            cmd = cmd + "KName='" + keyRef[1]
        cmd = cmd + "' AND User='" + user + "'"
        return self.doSelect(cmd)

    def payment(self, params):
        try:
            #TODO verify that params has all elements before processing
            fee = params['fee']
            value = params['amount']
            keyref = params['source']
            fromWallet = params['walletSrc']
            user = params['user']
            pattern = re.compile(regexWallet)
            if (not pattern.match(fromWallet)):
                return errMsg("Invalid source wallet name")
            if (not self.hasWallet(fromWallet)):
                return errMsg("Invalid source wallet name")
            #TODO use PW to encrypt/decrypt keys!!!!
            pw = params['walletPW'].strip()
            msg = params['msg'].strip()
            toWallet = params['walletDest']

            finalAddress = params['receiver']
            if (toWallet == ""):
                if (finalAddress[0] == "address"):
                    recAddress = finalAddress[1]
                elif (finalAddress[0] == "pubKey"):
                    recAddress = public_key_compressed_to_address(finalAddress[1])
                else:
                    return errMsg("Invalid recipient reference")
            else:
                if (not pattern.match(toWallet)):
                    return errMsg("Invalid destination wallet name")
                if (not self.hasWallet(toWallet)):
                    return errMsg("Invalid destination wallet name")
                recAddress = self.getDataFor(finalAddress, toWallet, "address", user)[0]
            keys = self.getDataFor(keyref, fromWallet, "", user)
            #get address based on wallet info and database verification even for address
            #get final address based on SQL query with final address and walref
            if (len(keys)>0):
                privKey = keys[2]
                senderPK = keys[3]
                senderAddr = keys[4]
                colErr = verifyAddr(senderAddr, senderPK) + verifyAddr(recAddress)
                if len(colErr) > 0:
                    return errMsg(colErr)
                signedTX, TxExpectedHash = self.signTx(privKey, recAddress, msg, value, fee, senderAddr, senderPK)
                #TODO do we want to verify the TX hash somehow after we received the reply from node?
                resps = c_peer.sendPOSTToPeers("transactions/send", signedTX)
                if len(resps) == 0:
                    return errMsg("No peer reachable, please retry again or check peer settings...")
                #TODO should we compare all replies??? Not really??? Just take first one...
                for xx in resps:
                    if len(xx) != 0:
                        return xx[0].text, xx[0].status_code
                return errMsg("No peer reachable, please retry again or check peer settings...")
            return errMsg("Payment/transfer failed due to parameter for keys")
        except Exception:
            return errMsg("Payment/transfer failed due to parameter error")

    def signTx(self, priv_key_hex, receiver_addr, msg, value,fee, pub_addr, pub_key_compressed):
        timestamp = getTime()
        transaction = {"from": pub_addr, "to": receiver_addr, "value": value, "fee": fee,
                       "dateCreated": timestamp, "data": msg, "senderPubKey": pub_key_compressed}

        # Hash and sign
        tran_hash = helper_sha256(putDataInOrder(m_transaction_order, transaction))
        tran_signature = sign(generator_secp256k1, private_key_hex_to_int(priv_key_hex), tran_hash)
        sig1 = str(hex(tran_signature[0]))[2:]
        sig2 = str(hex(tran_signature[1]))[2:]
        while len(sig1) < len(defSig):
            sig1 = "0"+sig1
        while len(sig2) < len(defSig):
            sig2 = "0"+sig2
        # Signed txn has appended signature; hash is not appended, but may be verified when receiving reply
        transaction["senderSignature"] = [sig1, sig2]
        return transaction, hex(tran_hash)[2:]

    def getAllBalance(self, params):
        try:
            user = params['user']
            bal = deepcopy(m_balanceData)
            for key in self.doSelect("SELECT address FROM Wallet WHERE User='" + user + "'"):
                val, respCode = self.collectKeyBalance(key)
                if (respCode == 200):
                    self.sumBalance(bal, val)
            return setOK(bal)
        except Exception:
            return errMsg("Seems to have peer issues....")

    def sumBalance(self, bal, val):
        bal['confirmedBalance'] = bal['confirmedBalance'] + val['confirmedBalance']
        bal['pendingBalance'] = bal['pendingBalance'] + val['pendingBalance']
        # bal['safeBalance'] = bal['safeBalance'] + val['safeBalance']

    def getWalletBalance(self, params):
        try:
            wal = params['wallet']
            user = params['user']
            bal = deepcopy(m_balanceData)
            for key in self.doSelect("SELECT address FROM Wallet WHERE WName='" + wal + "' AND User='" + user + "'"):
                val, respCode = self.collectKeyBalance(key)
                if (respCode == 200):
                    self.sumBalance(bal, val)
            return setOK(bal)
        except Exception:
            return errMsg("Seems to have peer issues....")

    def getWalletKeyBalance(self, params):
        try:
            wal = params['wallet']
            user = params['user']
            bal = {}
            for addr in self.doSelect("SELECT address FROM Wallet WHERE WName='" + wal + "' AND User='" + user + "'"):
                val, respCode = self.collectKeyBalance(addr)
                if (respCode == 200):
                    bal2 = deepcopy(m_balanceData)
                    bal2['confirmedBalance'] = val['confirmedBalance']
                    bal2['pendingBalance'] = val['pendingBalance']
                    bal[addr] = bal2
            return setOK(bal)
        except Exception:
            return errMsg("Seems to have peer issues....")

    def getAllTX(self, params):
        try:
            user = params['user']
            type = int(params['type'])
            return self.filterTX(type, self.doSelect("SELECT address, KName, pubKey FROM Wallet WHERE User='" + user + "'"))
        except Exception:
            return errMsg("Seems to have peer issues....")

    def getWalletTX(self, params):
        try:
            wal = params['wallet']
            user = params['user']
            type = int(params['type'])
            return self.filterTX(type, self.doSelect("SELECT address, KName, pubKey FROM Wallet WHERE User='" + user + "' AND WName='"+wal+"'"))
        except Exception:
            return errMsg("Seems to have peer issues....")

    def filterTX(self, type, l):
        tx = []
        if (len(l) < 3):
            return setOK(tx)
        query = [l[i:i + 3] for i in range(0, len(l), 3)]
        for addrx in query:
            resps = c_peer.sendGETToPeers("address/" + addrx[0] + "/transactions")
            # TODO should we compare all replies??? Not really??? Just take first one?
            (text, code) = resps[0]
            if (code == 200):
                if (type<2):
                    trxn = {'address':addrx[0]}
                elif (type<4):
                    trxn = {'keyName': addrx[1]+"/"+addrx[0]}
                elif (type < 6):
                    trxn = {'publicKey': addrx[2]+"/"+addrx[0]}

                trxn['transactions'] = []
                for trx in text['transactions']:
                    if ("minedInBlockIndex" in trx):
                        if (type == 0) or (type == 2) or (type == 4):
                            trxn['transactions'].append(trx)
                    else:
                        if (type == 1) or (type == 3) or (type == 5):
                            trxn['transactions'].append(trx)
                if (len(trxn['transactions'])>0):
                    tx.append(trxn)
        return setOK(tx)
