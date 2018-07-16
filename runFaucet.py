from project.initArgs import main
from project.models import m_permittedGET, m_permittedPOST


if __name__ == "__main__":
    m_permittedGET.clear()
    m_permittedGET.extend([
        #TODO remove the ones not valid anymore
        "/cfg$",
        "/info$",
        #"/info",  # TODO need to bring up???
        "/debug$",
        "/transactions/pending",
        "/transactions/confirmed",
        "/transactions/[0-9a-f]+$",
        "/balances",
        #"/address/[0-9a-fA-F]+/transactions",
        #"/address/[0-9a-fA-F]+/balance",
        "/peers",
        "/listNodes",  # TODO test only
        "/address/[0-9a-zA-Z]+/balance$",
        "/wallet/list/wallet/[0-9a-zA-Z]+$",
        "/wallet/list/keys/s([pna]y)*/[0-9a-zA-Z]+/[0-9a-zA-Z]+$",
        "/wallet/list/balance/(address|name|publicKey)/[0-9a-zA-Z]+/[0-9a-zA-Z]+/[0-9a-zA-Z]+$",
        "/wallet/list/allbalance/[0-9a-zA-Z]+/[0-9a-zA-Z]+$",
        "/wallet/list/allkeybalance/[0-9a-zA-Z]+/[0-9a-zA-Z]+$",
        "/wallet/list/allbalances/[0-9a-zA-Z]+$",
        "/wallet/list/allTXs/[012345]/[0-9a-zA-Z]+$",
        "/wallet/list/allTX/[012345]/[0-9a-zA-Z]+/[0-9a-zA-Z]+$",
    ])

    m_permittedPOST.clear()
    m_permittedPOST.extend([
        "/peers/connect",  # TODO POST
        "/wallet/transfer$"
    ])


    main("Faucet")

