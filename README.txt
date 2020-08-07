Git repo link
****************
https://github.com/PraAnj/P2P_DistributedContentSearching


How to run java bootstrap server (We used java version)
************************************
1. Go to src/BootstrapServer/java
2. javac BootstrapServer.java
3. java BootstrapServer


Installations required
************************************
1. Install flask and requests modules (pip install flask, pip install requests)


How to join the network from python node
***************************************
1. Go to src
2. You can run the python script in both ways mentioned below.

Method 1
    "cd src "
    "python pythonNode.py <ip_bs> <port_bs> <usd_port_self> <name_self> <restapi_port>"
    ex: python pythonNode.py 192.168.1.5 55555 8081 node1 81

Method 2
    "cd src "
    "python pythonNode.py"
    Then enter values according to the instructions.

To Exit from the network
**************************
1. Give X as the input to exit the network

To search a file
*********************
1. Type a word in the name of the file you need to find.

To print node status
*************************
1. Give S to print node details
