from project import app
from argparse import ArgumentParser
from project.models import m_cfg
from threading import Thread
import sys
from project.initArgs import init
from project.utils import isBCNode
from project.classes import c_blockchainNode
from project.controller import *
from project.pclass import c_peer

def main():
    parser = ArgumentParser()
    host,port = init(parser)
    #m_cfg['type'] = "Miner"
    m_cfg['type'] = "Wallet"
    #m_cfg['type'] = "BCNode"
    # default for peers is exactly one, but if started up with more, more are supported
    # the argument sets the time how often the checks are made in seconds to verify if the peer still replies
    thread = Thread(target=c_peer.checkEveryXSecs, args=(m_cfg['peersCheck'],))
    thread.start()

    app.run(host=host, port=port,threaded=False)

if __name__ == "__main__":
    main()