from project import app
from argparse import ArgumentParser
from project.models import m_cfg
from project.pclass import c_peer
from threading import Thread
#from project.nspec.blockchain.blocknode import resetChain
import sys
from project.initArgs import init
from project.utils import isBCNode
from project.classes import c_blockchainNode
from project.nspec.blockchain.verify import initPendingTX
from time import sleep

def main():
    #m_cfg['type'] = "Miner"
    #m_cfg['type'] = "Wallet"
    m_cfg['type'] = "BCNode"
    parser = ArgumentParser()
    host, port = init(parser)

    # default for peers is exactly one, but if started up with more, more are supported
    # the argument sets the time how often the checks are made in seconds to verify if the peer still replies
    thread = Thread(target=c_peer.checkEveryXSecs, args=(m_cfg['peersCheck'],))
    thread.start()
    while (m_cfg['statusPeer']==True):
        sleep(1)
    c_blockchainNode.c_blockchainHandler.resetChain()
    thread = Thread(target=initPendingTX)
    thread.start()

    app.run(host=host, port=port,threaded=True)

if __name__ == "__main__":
    main()

