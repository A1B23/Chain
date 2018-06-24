from project.initArgs import main
from project.models import m_permittedGET

if __name__ == "__main__":
    m_permittedGET.clear()
    m_permittedGET.extend([
        "/cfg$",
        "/debug$",
        "/debug/reset-chain",
        "/peers",
        "/listNodes",  # TODO test only
        "/mining/get-mining-job/[0-9a-fA-F]+$"
    ])
    main("Miner")
