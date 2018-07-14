from project.initArgs import main
from project.models import m_permittedGET, m_permittedPOST

if __name__ == "__main__":
    m_permittedGET.clear()
    m_permittedGET.extend([
        "/cfg$",
        "/info$",
        "/debug$",
        "/peers",
        "/viewGX$",
        "/listNodes$"  # TODO test only
    ])

    m_permittedPOST.clear()
    m_permittedPOST.extend([
        "/genFaucet$",  # TODO POST
        "/useTX$",  # TODO POST
        "/genTX$",  # TODO POST
        "/genGX$",
        "/updGX$",
        "/setID$"
    ])
    main("Genesis")

