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
from project.nspec.wallet.modelW import m_db
from contextlib import closing
import re


class wallet:
    def form_post(self,request):
        if request.form['action'] == 'Sign in':
            priv_key_hex = request.form['wallet_priv_key']
            pub_addr = get_public_address(priv_key_hex)
            return render_template('wallet.html', pub_addr=pub_addr)

        if request.form['action'] == 'Send coins':
            #url = request.form['url'] #Albert: this should go to configured peer instead of from GUI
            #url = peerURL + "/transactions/send"  # Albert
            #print("============URL: ", url)
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

    def createWallet(self, json):
        try:
            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                #TODO sanitise wallet name
                wal = json['name']
                pattern = re.compile("^[A-Z0-9a-z_]+$")
                if (not pattern.match(wal)):
                    return errMsg("Invalid wallet name.", 400)
                if (wal in self.listAllWallets()):
                    return errMsg("Creating Wallet " + wal + " failed.", 400)
                cur = con.cursor()
                cur.execute("INSERT INTO Wallet (WName,privKey,pubKey,address,KName,ChkSum) VALUES(?, ?, ?, ?,?,?)",(wal,"prK","pK","@","*","000"))
                con.commit()
                return setOK(wal)
        except Exception:
            return errMsg("Creating Wallet "+ wal + " failed.", 400)

    def listAllWallets(self):
        try:
            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                con.row_factory = sqlite3.Row

                cur = con.cursor()
                cur.execute("SELECT DISTINCT WName from Wallet")

                rows = cur.fetchall()
                wal = []
                for row in rows:
                    wal.extend(row)
                return wal
        except Exception:
            return errMsg("Creating Wallet "+wal+ " failed.", 400)
        return []

    def getAllWallets(self):
        return setOK({"walletList": self.listAllWallets()})


    def getAllKeys(self,params):
        wal = params['wallet']
        try:
            pattern = re.compile("^[A-Z0-9a-z_]+$")
            if (not pattern.match(wal)):
                return errMsg("Invalid wallet name.", 400)

            with closing(sqlite3.connect(m_db['DATABASE'])) as con:
                con.row_factory = sqlite3.Row

                cur = con.cursor()
                cmd = "SELECT"
                sel = False
                if ("py" in params['sel']):
                    cmd = cmd + " pubKey,"
                    sel = True

                if ("ay" in params['sel']):
                    cmd = cmd + " address,"
                    sel = True

                if ("ny" in params['sel']):
                    cmd = cmd + " KName"
                    sel = True

                if (sel == False):
                    cmd = cmd + " pubKey, address, KName"
                else:
                    if (cmd.endswith(",")):
                        cmd = cmd[0:-1]

                cmd = cmd + " FROM Wallet WHERE WName='" + wal + "'"
                cur.execute(cmd)

                keys = []
                for row in cur.fetchall():
                    keys.extend(row)
                return setOK({"keyList": keys})
        except Exception:
            return errMsg("Collecting keys for wallet " + wal + " failed.", 400)

