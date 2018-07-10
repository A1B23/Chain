from project.initArgs import main
from project.models import m_permittedGET

if __name__ == "__main__":
    m_permittedGET.clear()
    m_permittedGET.extend([
        "/cfg$",
        "/info$",
        "/debug$",
        "/load/[0-9a-fA-F]+$",
        "/save/[0-9a-fA-F]+$",
        "/debug/reset-chain",
        "/blocks$",
        "/blocks/[0-9]+$",
        "/transactions/pending",
        "/transactions/confirmed",
        "/transactions/[0-9a-f]+$",
        "/balances",
        "/address/[0-9a-f]+/transactions",
        "/address/[0-9a-f]+/balance",
        "/peers",
        "/listNodes",  # TODO test only
        "/mining/get-mining-job/[0-9a-f]+$"
    ])
    main("BCNode")

