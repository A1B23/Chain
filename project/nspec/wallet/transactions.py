from Crypto.Random import random
from pycoin.ecdsa import generator_secp256k1, sign, verify
from urllib.parse import urlparse
from flask import Flask, jsonify, request
import hashlib, os, json, binascii, datetime, requests
from project.utils import sha256ToHex,putDataInOrder
from project.models import m_transaction_order

myHash = {}
peerURL = "https://stormy-everglades-34766.herokuapp.com" #Albert

def generate_private_key() -> str:
  private_key = hex(random.getrandbits(256))
  #print("Private key (hex):", private_key)
  return private_key[2:]
  
def ripemd160(msg: str) -> str:
  hash_bytes = hashlib.new('ripemd160', msg.encode("utf8")).digest()
  return hash_bytes.hex()

def sha256(msg: str) -> int:
  msg2 = msg.encode("utf8")
  hash_bytes = hashlib.sha256(msg2).digest()
  return int.from_bytes(hash_bytes, byteorder="big")

def private_key_hex_to_int(private_key_hex: str):
  return int(private_key_hex, 16) 
  
def private_key_to_public_key(private_key):
  return (generator_secp256k1 * private_key).pair()
  
def get_pub_key_compressed(pub_key):
  return hex(pub_key[0])[2:] + str(pub_key[1] % 2)
  
def public_key_compressed_to_address(public_key_compressed):
  return ripemd160(public_key_compressed)

def get_public_address(priv_key_hex):
    priv_key_int = private_key_hex_to_int(priv_key_hex)
    pub_key = private_key_to_public_key(priv_key_int)
    pub_key_compressed = get_pub_key_compressed(pub_key)
    pub_addr = public_key_compressed_to_address(pub_key_compressed)
    return pub_addr
  
def send_txn(priv_key_hex, receiver_addr, msg, value):
    #priv_key_hex = "7e4670ae70c98d24f3662c172dc510a085578b9ccc717e6c2f4e547edd960a34"  
    #priv_key_hex = generate_private_key()
    priv_key_int = private_key_hex_to_int(priv_key_hex)
    pub_key = private_key_to_public_key(priv_key_int)
    pub_key_compressed = get_pub_key_compressed(pub_key)
    pub_addr = public_key_compressed_to_address(pub_key_compressed)
    print("Private key (hex): ", priv_key_hex)
    print("Public key: ", pub_key_compressed)
    print("Public addr: ", pub_addr)

    timestamp = datetime.datetime.now().isoformat()
    timestamp = timestamp + "Z"
    #receiver_addr = "f51362b7351ef62253a227a77751ad9b2302f911"
    #JSON of txn to be sent  
    transaction = {"from": pub_addr, "to": receiver_addr, "value": value, "fee": 20, 
    "dateCreated": timestamp, "data": msg, "senderPubKey": pub_key_compressed}

    # transaction = {"from":"0000000000000000000000000000000000000000","to":"f3a1e69b6176052fcc4a3248f1c5a91dea308ca9",
    #                "value":1000000000000,"fee":0,"dateCreated":"2018-01-01T00:00:00.000Z","data":"genesis tx",
    #                "senderPubKey":"00000000000000000000000000000000000000000000000000000000000000000"}
    #  #              "transactionDataHash":"8a684cb8491ee419e7d46a0fd2438cad82d1278c340b5d01974e7beb6b72ecc2",

    json_encoder = json.JSONEncoder(separators=(',',':'))
    tran_json = json_encoder.encode(transaction)
    #print("transaction (json): ", tran_json)

    # Hash and sign
    tran_hash = sha256(putDataInOrder(m_transaction_order, transaction))
    print("transaction hash (sha256): ", hex(tran_hash)[2:])
    myHash.update({"hash": hex(tran_hash)[2:]})
    tran_signature = sign(generator_secp256k1, priv_key_int, tran_hash)

    element1 = str(hex(tran_signature[0]))[2:]
    element2 = str(hex(tran_signature[1]))[2:]
    tran_signature_str = (element1,element2)

    #print("transaction signature: ", tran_signature_str)

    # Signed txn (appended hash and signature)
    signed_txn = {"from": pub_addr, "to": receiver_addr, "value": value, "fee": 20,
        "dateCreated": timestamp, "data": msg, "senderPubKey": pub_key_compressed,
        "senderSignature": tran_signature_str}

    print("Signed Txn: ",signed_txn)

    valid = verify(generator_secp256k1, pub_key, tran_hash, tran_signature)
    print("Is signature valid? " + str(valid))
    return signed_txn
    
