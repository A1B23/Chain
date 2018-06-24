from project import app, render_template
from flask import Flask, jsonify, request
from project.utils import *
import json
from project.nspec.wallet import *
from project.pclass import c_peer

# put your distribution according to url
class walletInterface:
    def nodeSpecificGETNow(self,url,linkInfo):
        urlID = url[1:5]
        if (urlID == 'send'):
            return send()

        if (urlID == 'addr'):
            return setOK(linkInfo)
            #return send()
        # identify your url and then proceed
        #linkInfo is a json object containing the information from the URL
        response = {
            'NodeType': m_cfg['type'],
            'info': "This API is not yet implemented....",
            'requestedUrl': url,
            'linkInfo': linkInfo
        }
        ## put your logic here and create the reply as next line
        return jsonify(response), 400

    # this is the dummy function only, your functoin comes from the import!
    def nodeSpecificPOSTNow(self,url,linkInfo,json,request):
        # linkInfo is a json object containing the information from the URL

        if (url == "/"):
            return form_post(request)


        #json contains the json object submitted during the POST
        response = {
            'NodeType': m_cfg['type'],
            'info': "This API is not yet implemented...."
        }
        ## put your logic here and create the reply as next line
        return jsonify(response), 400