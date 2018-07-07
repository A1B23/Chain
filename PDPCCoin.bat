echo off
rem ########### This is a test batch to start a wallet, a miner, and at least one blockchain node
rem ########### each one opens a separate DOS window and the window is identified by the type and IP
rem ########### Comment out your test part or start a node in a different IP address than here and debug in your PyCharm
rem ########### You can also start all here and if you need to debug, just kill one respective window and lauch in IDE with same IP

rem !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
rem !!!!!!!!!!Please set here the path to your python.exe !!!!!!!! 
rem !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
set myPyPath="C:/Users/ISS User/AppData/Local/Programs/Python/Python36-32/python.exe" 

rem ###### These are the parameters used int he batch to configure nodes and IP addresses and also peers
rem we can start the node with network ID: 
rem netID=0 is online test net Academy genesisblock
rem netID=1 is NAPCoin 
rem netID and chainID should not be parallel, chainID (being more complex) overrides netID
rem alternatively, set the chainID, which is the genesis blockhash
rem by default all assume to be connected to 1 peer, so need to specify if more peers are needed --minPeers and --maxPeers
set netID=1
color 8F

rem    0 = Black       8 = Gray
rem    1 = Blue        9 = Light Blue
rem    2 = Green       A = Light Green
rem    3 = Aqua        B = Light Aqua
rem    4 = Red         C = Light Red
rem    5 = Purple      D = Light Purple
rem    6 = Yellow      E = Light Yellow
rem    7 = White       F = Bright White

rem ######################## Wallet hard coded parameters
set typeDir=Wallet
set col=1F
set port=5555
set delay=Y
set asDebug=N
echo %typeDir% start...
rem #### make the port to reflect the peer it connects to, so 5x = 5 wallet and x connected node 
set nodeIPnum=52
start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runWallet.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 2 --port %port% --canTrack %delay% --asDebug %asDebug%"
set nodeIPnum=54
start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runWallet.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 4 --port %port% --canTrack %delay% --asDebug %asDebug%"

rem ######################## BlockChain node template, can launch many nodes by simply changing the IP-ending
set typeDir=Blockchain
set nodeIPnum=2
set minPeers=2
set maxPeers=3
set col=2B
echo %typeDir% start at IP 127.0.0.%nodeIPnum%
start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runBC.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 4 --port %port% --minPeers %minPeers% --maxPeers %maxPeers% --canTrack %delay% --asDebug %asDebug%"

set asDebug=Y
set nodeIPnum=4
echo %typeDir% start at IP 127.0.0.%nodeIPnum%
start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runBC.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 2,5 --port %port% --minPeers %minPeers% --maxPeers %maxPeers% --canTrack %delay% --asDebug %asDebug%"
set asDebug=N

rem ###################### Miner hard coded parameters 
set typeDir=Miner
rem we keep the sam address as blockchain above!
set col=5B
set mode=y
set minPeers=1
set maxPeers=1
set nodeIPnum=32
rem start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runMiner.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 2 --minPeers %minPeers% --maxPeers %maxPeers% --canTrack %delay% -mod %mode% --asDebug %asDebug%"
set nodeIPnum=34
start cmd.exe /K "color %col% & title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runMiner.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 4 --minPeers %minPeers% --maxPeers %maxPeers% --canTrack %delay% -mod %mode% --asDebug %asDebug%"

rem ##################### test new node added
rem pause
set typeDir=Blockchain
set nodeIPnum=5
set minPeers=2
set maxPeers=3
set col=2B
echo %typeDir% start at IP 127.0.0.%nodeIPnum%
start cmd.exe /K "color %col% &title=%typeDir%-127.0.0.%nodeIPnum% & %myPyPath% runBC.py --host 127.0.0.%nodeIPnum% --netID %netID% --connect 2 --port %port% --minPeers %minPeers% --maxPeers %maxPeers% --canTrack %delay% --asDebug %asDebug%"
