from project.utils import setOK,errMsg
from project.classes import c_genesisInterface
from project.models import m_info

# put your distribution according to url
class genesisInterface:
    def nodeSpecificGETNow(self, url, linkInfo):
        urlID = url[1:5]
        if url == "/viewGX":
            return c_genesisInterface.viewGX()

            #return send()
        # identify your url and then proceed
        #linkInfo is a json object containing the information from the URL
        response = {
            'NodeType': m_info['type'],
            'info': "This API is not yet implemented....",
            'requestedUrl': url,
            'linkInfo': linkInfo
        }
        ## put your logic here and create the reply as next line
        return errMsg(response)

    # this is the dummy function only, your functoin comes from the import!
    def nodeSpecificPOSTNow(self, url, linkInfo, json, request):
        # linkInfo is a json object containing the information from the URL

        if url == "/genFaucet":
            return c_genesisInterface.genFaucet(json)
        elif url == "/useTX":
            return c_genesisInterface.useTX(json)
        elif url == "/genTX":
            return c_genesisInterface.genTX(json)
        elif url == "/genGX":
            return c_genesisInterface.genGX(json)
        elif url == "/updGX":
            return c_genesisInterface.updGX(json)
        elif url == "/viewGX":
            return c_genesisInterface.viewGX(json)
        elif url == "/setID":
            return c_genesisInterface.setID(json)


        #json contains the json object submitted during the POST
        response = {
            'NodeType': m_info['type'],
            'info': "This API is not (yet) implemented...."
        }
        ## put your logic here and create the reply as next line
        return errMsg(response)