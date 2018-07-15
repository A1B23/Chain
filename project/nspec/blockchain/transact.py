from project.nspec.blockchain.verify import m_pendingTX
from project.models import defAdr, defHash
from project.nspec.blockchain.modelBC import m_Blocks
from project.utils import setOK, errMsg

class transactions:
    def getPendTXByAddress(self, address):
        response = []
        for tx in m_pendingTX:
            if (address == ""):
                response.append(m_pendingTX[tx])
            else:
                if (m_pendingTX[tx]['from'] == address) or (m_pendingTX[tx]['to'] == address):
                    response.append(m_pendingTX[tx])
        return response

    def getTXForAddress(self ,address):
        #TODO move to models
        reply = {
          "address": "undefined",
          "transactions": []
        }
        if (len(address) != len(defAdr)):
            errMsg("Inavlid Address Len")
        response = self.getPendTXByAddress(address)
        # if a given hash is found already, no other exists, else keep searching
        #there is no pending, so return all
        # if (len(hash) == 0) or (len(response) == 0):
        response.extend(self.getConfirmedTXByAddress(address))

        if (len(response) > 0):
            reply['address'] = address
            #we must sort the list by date time in ascending order
            reply['transactions'] = sorted(response, key=lambda k: k['dateCreated'])
            return setOK(reply)

        return errMsg("No transactions found for: "+address, 404)


    def getConfirmedTXByAddress(self,address):
        response = []
        for b in m_Blocks:
            for tx in b['transactions']:
                if (address != ""):
                    if (tx['from'] == address) or (tx['to'] == address):
                        response.append(tx)
                else:
                    # Opps, no skipping of coinbases
                    ##if (tx['from'] != defAdr):
                    response.append(tx)
        return response


    def getPendTXByHash(self,hash):
        response = []
        for tx in m_pendingTX:
            if (hash == ""):
                response.append(m_pendingTX[tx])
            else:
                # if a given hash is found already, no other exists, else keep searching
                if (tx == hash):
                    response.append(m_pendingTX[tx])
                    break
        return response


    def getPendingTX(self,hash):
        if ((hash != "") and (len(hash) != len(defHash))):
            return errMsg("Invalid Hash Len")
        return setOK(self.getPendTXByHash(hash))


    def getConfirmedTXByHash(self,hash):
        response = []
        for b in m_Blocks:
            for tx in b['transactions']:
                if (hash != ""):
                    # if a given hash is found already, no other exists, else keep searching
                    if (tx['transactionDataHash'] == hash):
                        response.append(tx)
                        break
                else:
                    # Opps, no skipping of coinbases
                    ##if (tx['from'] != defAdr):
                    response.append(tx)
        return response


    def getTXForHash(self,hash):
        if (len(hash) != len(defHash)):
            return errMsg("Invalid Hash Len")
        response = self.getPendTXByHash(hash)
        # if a given hash is found already, no other exists, else keep searching
        if (len(hash) == 0) or (len(response) == 0):
            response.extend(self.getConfirmedTXByHash(hash))
        if (len(response) > 0):
            return setOK(response)

        return errMsg("No transactions found for: "+hash, 404)

