from project.nspec.wallet.transactions import generate_private_key, private_key_hex_to_int, private_key_to_public_key
from project.nspec.wallet.transactions import get_pub_key_compressed, public_key_compressed_to_address,helper_sha256
from project.pclass import c_peer
from project.models import m_transaction_order
from pycoin.ecdsa import generator_secp256k1, sign
from project.utils import setOK, errMsg, putDataInOrder, getTime
import sqlite3
from project.nspec.wallet.modelW import m_db, regexWallet
from contextlib import closing
import re
from project.nspec.blockchain.verify import verifyAddr



class faucet:

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
            ret = self.doSelect(cmd)
            repl = []
            for k in ret:
                if k.startswith("addr"):
                    repl.append(k)
                else:
                    if k[-1] == "#":
                        repl.append(k+"no")
                    else:
                        repl.append(k[0:k.rindex("#")]+"#yes")

            return setOK({"keyList": repl})

        except Exception:
            return errMsg("Collecting keys for wallet " + wal + " failed.")

