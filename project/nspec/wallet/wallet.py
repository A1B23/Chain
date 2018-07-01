from Crypto.Random import random
from pycoin.ecdsa import generator_secp256k1, sign, verify
from urllib.parse import urlparse
from flask import jsonify, request, render_template
import hashlib, os, json, binascii, datetime, requests
from project.nspec.wallet.transactions import *
from project.pclass import c_peer
from project.models import m_info
from project.utils import setOK,errMsg
import sqlite3
from project.nspec.wallet.modelW import m_db, regexWallet
from contextlib import closing
import re


class wallet:
    #TODO remove the two routines when transition is completed
    def form_post(self,request):
        if request.form['action'] == 'Sign in':
            priv_key_hex = request.form['wallet_priv_key']
            pub_addr = get_public_address(priv_key_hex)
            return render_template('wallet.html', pub_addr=pub_addr)

        if request.form['action'] == 'Send coins':
            # priv_key_hex = "7e4670ae70c98d24f3662c172dc510a085578b9ccc717e6c2f4e547edd960a34"
            priv_key_hex = request.form['wallet_priv_key']
            print("============Priv key: ", priv_key_hex)
            wallet_addr = request.form['wallet_addr']
            print("============Wallet addr: ", wallet_addr)
            recipient_addr = request.form['recipient_addr']
            print("============Recipient addr: ", recipient_addr)
            no_of_coins = int(request.form['no_of_coins'])
            print("============No of coins: ", no_of_coins)
            #Albert
            msg = "Txn from wallet " + m_info['nodeUrl']
            txn_data = send_txn(priv_key_hex, recipient_addr, msg, no_of_coins)
            # req = requests.post("http://stormy-everglades-34766.herokuapp.com/transactions/send", json=txn_data)
            try:
                req = c_peer.sendPOSTToPeers("transactions/send", txn_data)[0] #[0] is fixed as only one peer
                print("response is: ", req.json())
                # return jsonify(txn_data), 200
                return render_template('wallet.html', response=req.json(), pub_addr=wallet_addr)
            except:
                return render_template('wallet.html', response="Error, no peer etc.", pub_addr=wallet_addr)


    def send(self):
        # priv_key_hex = transactions.generate_private_key()
        priv_key_hex = "7e4670ae70c98d24f3662c172dc510a085578b9ccc717e6c2f4e547edd960a34"
        receiver_addr = "f51362b7351ef62253a227a77751ad9b2302f911"
        msg = "From wallet"
        # API_ENDPOINT = url+"/transactions/send"
        txn_data = transactions.send_txn(priv_key_hex, receiver_addr, msg)
        req = c_MainIntf.c_peer.sendPOSTToPeers("transactions/send", txn_data)  # Albert
        print("response is: ", req[0])
        return jsonify(txn_data), 200

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
        try:
            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                wal = json['name']
                pattern = re.compile(regexWallet)
                if (not pattern.match(wal)):
                    return errMsg("Invalid wallet name.", 400)
                if (self.hasWallet(wal)):
                    return errMsg("Creating Wallet '" + wal + "' failed.", 400)
                if (json['numKeys']<=0) or (json['numKeys'] > 5):
                    return errMsg("Invalid number of keys requested.", 400)
                cur = con.cursor()
                keys = []
                s = set(json['keyNames'])
                if (len(s) != len(json['keyNames'])):
                    return errMsg("Invalid name list for keys, contains duplicates", 400)

                for idx in range(0, json['numKeys']):
                    name = ""
                    if (len(json['keyNames'])>idx):
                        name = json['keyNames'][idx]
                    keys.append(self.createKey(wal, name, json['user']))

                cur.executemany("INSERT INTO Wallet (WName,privKey,pubKey,address,KName,ChkSum,User) VALUES(?, ?, ?, ?,?,?,?)", keys)
                con.commit()
                return setOK(wal)
        except Exception:
            return errMsg("Creating Wallet " + wal + " failed.", 400)

    def listAllWallets(self, user):
        try:
            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                con.row_factory = sqlite3.Row

                cur = con.cursor()
                cur.execute("SELECT DISTINCT WName from Wallet WHERE User='"+user+"'")

                rows = cur.fetchall()
                wal = []
                for row in rows:
                    wal.extend(row)
                return wal
        except Exception:
            return []


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

    def getKeyBalance(self, params):
        keys = self.getDataFor([params['sel'], params['key']], params['wallet'], "",params['user'])
        if (len(keys)>4):
            addr = keys[4]
            resps = c_peer.sendGETToPeers("address/" + addr + "/balance")
            # TODO should we compare all replies??? Not really??? Just take first one?
            respText, respCode = resps[0]
            if (respCode == 200):
                return setOK(respText)
            else:
                return errMsg(respText['errorMsg'], respCode)
        return errMsg("Invalid parameters provided", 400)

    def getAllKeys(self, params):
        wal = 'unidentified'
        try:
            wal = params['wallet']
            pattern = re.compile(regexWallet)
            if (not pattern.match(wal)):
                return errMsg("Invalid wallet name.", 400)

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
            return errMsg("Collecting keys for wallet " + wal + " failed.", 400)


    def getDataFor(self, keyRef, wallet, limit, user):
        cmd = "SELECT "
        if (limit == ""):
            cmd = cmd + "* "
        else:
            cmd = cmd + limit

        cmd = cmd + " from Wallet where WName='" + wallet + "' AND "
        if (keyRef[0] == "address"):
            cmd = cmd + "address='"+keyRef[1]
        elif (keyRef[0] == "publicKey"):
            cmd = cmd + "pubKey='"+keyRef[1]
        elif (keyRef[0] == "name"):
            cmd = cmd + "KName='" + keyRef[1]
        cmd = cmd + "' AND User='" + user +"'"
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
                return errMsg("Invalid source wallet name", 400)
            if (not self.hasWallet(fromWallet)):
                return errMsg("Invalid source wallet name", 400)
            #TODO use PW to encrypt/decrypt keys!!!!
            pw = params['walletPW'].strip()
            msg = params['msg'].strip()
            toWallet = params['walletDest']

            finalAddress = params['receiver']
            if (toWallet == ""):
                if (finalAddress[0] == "address"):
                    recAddress = finalAddress[1]
                else:
                    recAddress = public_key_compressed_to_address(finalAddress[1])
            else:
                if (not pattern.match(toWallet)):
                    return errMsg("Invalid destination wallet name", 400)
                if (not self.hasWallet(toWallet)):
                    return errMsg("Invalid destination wallet name", 400)
                keys = self.getDataFor(finalAddress, toWallet, "address",user)
                recAddress = keys[0]
            keys = self.getDataFor(keyref, fromWallet, "")
            #TODO get address based on wallet info and database verification even for address
            #get final address based on SQL query with final address and walref
            if (len(keys)>0):
                pk = keys[2]
                senderPK = keys[3]
                senderAddr = keys[4]
                signedTX, TxExpectedHash = self.signTx(pk, recAddress, msg, value, fee, senderAddr, senderPK)
                #TODO do we want to verify the TX hash somehow after we received the reply from node?
                resps = c_peer.sendPOSTToPeers("transactions/send", signedTX)
                #TODO should we compare all replies??? Not really??? Just take first one?
                resp = resps[0].json()
                return setOK(resp)
            return errMsg("Payment/transfer failed due to parameter for keys", 400)
        except Exception:
            return errMsg("Payment/transfer failed due to parameter error", 400)


    def signTx(self, priv_key_hex, receiver_addr, msg, value,fee, pub_addr, pub_key_compressed):
        timestamp = datetime.datetime.now().isoformat()
        timestamp = timestamp + "Z"
        transaction = {"from": pub_addr, "to": receiver_addr, "value": value, "fee": fee,
                       "dateCreated": timestamp, "data": msg, "senderPubKey": pub_key_compressed}

        # Hash and sign
        tran_hash = sha256(putDataInOrder(m_transaction_order, transaction))
        tran_signature = sign(generator_secp256k1, private_key_hex_to_int(priv_key_hex), tran_hash)
        tran_signature_str = (str(hex(tran_signature[0]))[2:], str(hex(tran_signature[1]))[2:])

        # Signed txn has appended signature; hash is not appended, but may be verified when receiving reply
        transaction["senderSignature"] = tran_signature_str
        return transaction, hex(tran_hash)[2:]
