from Crypto.Random import random
from pycoin.ecdsa import generator_secp256k1, sign, verify
from urllib.parse import urlparse
from flask import jsonify, request, render_template
import hashlib, os, json, binascii, datetime, requests
from project.nspec.wallet.transactions import *
from project.pclass import c_peer
from project.models import m_info

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




