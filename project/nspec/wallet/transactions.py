from Crypto.Random import random
from pycoin.ecdsa import generator_secp256k1
import hashlib


def generate_private_key() -> str:
  private_key = hex(random.getrandbits(256))
  return private_key[2:]
  
def ripemd160(msg: str) -> str:
  hash_bytes = hashlib.new('ripemd160', msg.encode("utf8")).digest()
  return hash_bytes.hex()

def helper_sha256(msg: str) -> int:
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

def get_public_address_from_privateKey(priv_key_hex):
    priv_key_int = private_key_hex_to_int(priv_key_hex)
    pub_key = private_key_to_public_key(priv_key_int)
    pub_key_compressed = get_pub_key_compressed(pub_key)
    return get_public_address_from_publicKey(pub_key_compressed)

def get_public_address_from_publicKey(pub_key_compressed):
    #pub_key_compressed = get_pub_key_compressed(pub_key)
    pub_addr = public_key_compressed_to_address(pub_key_compressed)
    #TODO add leading zeros to ensure correct length!!!! just in case
    return pub_addr
    
