from project.initArgs import main
from project.models import m_permittedGET

if __name__ == "__main__":
    m_permittedGET.clear()
    m_permittedGET.extend([
        "/cfg$",
        "/info$",
        "/debug$",
        "/debug/reset-chain",
        "/blocks$",
        "/blocks/[0-9]+$",
        "/transactions/pending",
        "/transactions/confirmed",
        "/transactions/[0-9a-fA-F]+$",
        "/balances",
        "/address/[0-9a-fA-F]+/transactions",
        "/address/[0-9a-fA-F]+/balance",
        "/peers",
        "/listNodes",  # TODO test only
        "/mining/get-mining-job/[0-9a-fA-F]+$"
    ])
    main("BCNode")

