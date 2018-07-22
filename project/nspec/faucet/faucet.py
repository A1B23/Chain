from project.utils import setOK, errMsg
from project.nspec.wallet.modelW import regexWallet
import re
import project.classes


class faucet:
    def getAllKeys(self, params):
        #TODO split this in wallet o get the data an d then wallet return and faucet process further at the end
        wal = 'unidentified'
        try:
            wal = params['wallet']
            pattern = re.compile(regexWallet)
            if not pattern.match(wal):
                return errMsg("Invalid wallet name.")

            cmd = "SELECT"
            sel = False
            if "py" in params['sel']:
                cmd = cmd + " 'pubkey:' || pubKey,"
                sel = True

            if "ay" in params['sel']:
                cmd = cmd + " 'addr:' || address,"
                sel = True

            if "ny" in params['sel']:
                cmd = cmd + " 'name:' || KName"
                sel = True

            if sel is False:
                cmd = cmd + " pubKey, address, KName"
            else:
                if cmd.endswith(","):
                    cmd = cmd[0:-1]

            cmd = cmd + " FROM Wallet WHERE WName='" + wal + "'"
            ret = project.classes.c_walletInterface.doSelect(cmd)
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

    def checkLimit(self, json):
        try:
            fee = json['fee']
            if fee != 10:   #miminum permitted so
                return "Invalid fee"
            total = fee + json['amount']
            addrN = json['source'][0]
            if (addrN != "address") or ((json['receiver'][0] != "address") and (json['receiver'][0] != "pubKey")):
                return "Invalid address reference"
            addr = json['source'][1]
            src = json['walletSrc']
            for k in project.classes.c_walletInterface.doSelect("SELECT " + json['receiver'][0]+" FROM Wallet WHERE WName='" + src + "' AND User='" + src + "'"):
                if k == json['receiver'][1]:
                    return "Invalid recipient reference" #no payment to faucet itself, which just drains the funds

            maxTotal = project.classes.c_walletInterface.doSelect("SELECT KName FROM Wallet WHERE WName='" + src + "' AND User='" + src + "' AND address='"+addr+"'")
            if json['walletPW'] != maxTotal[0].split("#")[2]:
                 return "Invalid address reference"
            if (fee >= total) or (total > int(maxTotal[0].split("#")[1])):
                return "Sum outside permitted range for individual request"
            return ""
        except Exception:
            return "Invalid JSON object"


