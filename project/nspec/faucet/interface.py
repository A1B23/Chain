from project.classes import c_faucetInterface
import project.nspec.wallet.interface as wall
from project.utils import errMsg


class faucetInterface:
    def nodeSpecificGETNow(self, url, linkInfo):
        urlID = url[1:5]
        if urlID == 'wall':
            if url.startswith("/wallet/list/keys/s"):
                return c_faucetInterface.getAllKeys(linkInfo)  # different from wallet!

        return wall.walletInterface.nodeSpecificGETNow(self,url, linkInfo)


    def nodeSpecificPOSTNow(self, url, linkInfo, json, request):
        if url == "/wallet/transfer":
            mes = c_faucetInterface.checkLimit(json)
            if len(mes) > 0:
                return errMsg(mes)
        return wall.walletInterface.nodeSpecificPOSTNow(self, url, linkInfo, json, request)
