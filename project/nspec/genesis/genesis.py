from project.utils import setOK, errMsg, getTime, sha256ToHex, makeMinerHash, makeBlockDataHash
from project.nspec.blockchain.modelBC import m_staticTransactionRef, m_coinBase, m_static_emptyBlock
from project.nspec.genesis.modelG import m_data, m_dataInit
from project.models import m_transaction_order, defAdr
from copy import deepcopy
import project.classes
from project.nspec.blockchain.verify import verifyBlockAndAllTX
from project.nspec.blockchain.balance import updateConfirmedBalance
import json



class genesis:

    def initGenesis(self):
        m_data.clear()
        m_data.update(deepcopy(m_dataInit))
        return

    def setID(self, data):
        if m_data['chainRef'] != "":
            return errMsg("Current chainRef set: "+m_data['chainRef'])

        if project.classes.c_walletInterface.hasWallet('genesis' + data['chainRef']) is True:
            return errMsg("Wallet reference already exists")

        m_data.clear()
        m_data.update(deepcopy(m_dataInit))
        m_data['chainRef'] = data['chainRef']
        return setOK("chain ID set to: "+data['chainRef'])

    def checkTX(self, data):
        if m_data['chainRef'] == "":
            return "Missing chainRef "
        if data['chainRef'] != m_data['chainRef']:
            return "Current chainRef not matching: " + m_data['chainRef']

        if (isinstance(data['initVal'], int) is False) or (data['initVal'] < 0):
            return "Invalid start value"

        if ('maxVal' in data) and ((isinstance(data['maxVal'], int) is False) or
                                   (data['maxVal'] < 0) or (data['maxVal'] > data['initVal'])):
            return "Invalid maximal donation value"

        #TODO check address is of string no space 0-9a-f
        if ('address' in data) and ((isinstance(data['address'], str) is False) or
                                   (len(data['address']) != len(defAdr)) or (data['address'] == defAdr)):
            return "Invalid address value"

        return ""

    def genFaucet(self, data):
        ret = self.checkTX(data)
        if len(ret) > 0:
            return errMsg(ret)

        m_data['TXList'].append(data)
        return setOK(str(len(m_data['TXList'])) + " TXs registered. Most recent type: Faucet")


    def useTX(self, data):
        ret = self.checkTX(data)
        if len(ret) > 0:
            return errMsg(ret)

        m_data['TXList'].append(data)
        return setOK(str(len(m_data['TXList'])) + " TXs registered. Most recent type: Given TX")

    def genTX(self, data):
        ret = self.checkTX(data)
        if len(ret) > 0:
            return errMsg(ret)
        m_data['TXList'].append(data)
        return setOK(str(len(m_data['TXList'])) + " TXs registered. Most recent type: creating TX")

    def makeTX(self, data, address, date):
        newTX = deepcopy(m_coinBase)
        newTX["to"] = address
        newTX["value"] = data['initVal']
        newTX["fee"] = 0
        newTX["dateCreated"] = date
        if (data['type'] == "genFaucet"):
            newTX["data"] = "Genesis Faucet: "+data['comment']
        else:
            newTX["data"] = "Genesis TX: " + data['comment']
        newTX["transactionDataHash"] = sha256ToHex(m_transaction_order, newTX)
        newTX["senderSignature"] = m_staticTransactionRef["senderSignature"]
        newTX["minedInBlockIndex"] = 0
        return newTX

    def genGX(self, data):
        try:
            if m_data['chainRef'] == "":
                return errMsg("Missing chainRef ")
            if data['chainRef'] != m_data['chainRef']:
                return errMsg("Current chainRef not matching: " + m_data['chainRef'])
            for jtx in m_data['TXList']:
                if jtx['chainRef'] != m_data['chainRef']:
                    return errMsg("One of the TX has invalid chainRef: " + jtx['chainRef'])
            if project.classes.c_walletInterface.hasWallet('genesis' + data['chainRef']) is True:
                return errMsg("Genesis/faucet/wallet reference already exists")

            gen = deepcopy(m_static_emptyBlock)
            del gen['prevBlockHash']
            gen['transactions'].clear()
            wallet = 'genesis' + m_data['chainRef']
            cnt = 0
            for data in m_data['TXList']:
                if data['type'] == "genFaucet":
                    # 'disguise' the maxDonation and the password in DB as key name
                    kname = str(cnt) +'#'+ str(data['maxVal'])+'#'+str(data['privVal'])
                    project.classes.c_walletInterface.addKeysToWalletBasic(
                        {'name': wallet, 'user': wallet, 'numKeys': 1, 'keyNames': [kname]}, wallet)
                    repl = project.classes.c_walletInterface.getDataFor(['name', kname], wallet, "", wallet)
                    gen['transactions'].append(self.makeTX(data, repl[4], getTime()))
                    cnt = cnt + 1
                elif data['type'] == "useTX":
                    gen['transactions'].append(self.makeTX(data, data['address'], getTime()))
                elif data['type'] == "genTX":
                    gen['transactions'].append(self.makeTX(data, data['address'], getTime()))
            gen["blockDataHash"] = makeBlockDataHash(gen, True)
            gen["dateCreated"] = getTime()
            gen["nonce"] = 0
            gen["difficulty"] = 0
            gen["blockHash"] = makeMinerHash(gen)
            gen["index"] = 0
            ret = verifyBlockAndAllTX(gen)
            if len(ret) > 0:
                return errMsg(ret)
            ret = updateConfirmedBalance(gen['transactions'], True)
            fin = {"balances": ret, "genesis": gen}
            fnam = "Genesis_"+m_data['chainRef']+".json"
            with open(fnam, 'w') as outfile:
                outfile.write(json.dumps(fin, sort_keys=True, indent=42))
            return setOK(fin)
        except Exception:
            #TODO clear database
            return errMsg("Some data failure detected")

    def updGX(self, data):
        if m_data['chainRef'] == "":
            return errMsg("Missing chainRef ")
        if data['chainRef'] != m_data['chainRef']:
            return errMsg("Current chainRef not matching: " + m_data['chainRef'])
        for jtx in data['TXList']:
            if jtx['chainRef'] != m_data['chainRef']:
                return errMsg("One of the TX has invalid chainRef: " + jtx['chainRef'])
        m_data.clear()
        m_data.update(data)
        return setOK("Data updated without major verifications")

    def viewGX(self):
        return setOK(m_data)


