import socket, threading
import sys
import random

myConnectedNodes = []
mySearchRequests = []
otherSearchRequests = []
myFiles = []

class PeerThread(threading.Thread):
    def __init__(self, nodeSocket, peerAddress, data):
        threading.Thread.__init__(self)
        self.nodeSocket = nodeSocket
        self.peerAddress = peerAddress
        self.data = data
        print ("New connection added: ", peerAddress)

    def processRequest(self, requestString):
        global myConnectedNodes
        global mySearchRequests
        global otherSearchRequests

        res = requestString.split()
        reqType = res[1]
        
        print(requestString)

        if reqType == 'JOIN':
          print("New node joined")
          myConnectedNodes.append((res[2], res[3]))
          print(myConnectedNodes)
          return "0"
        return "9999"        
        
    def run(self):
        global myConnectedNodes
        global mySearchRequests
        global otherSearchRequests        

        print ("Connection from : ", self.peerAddress)

        msg = self.data.decode()        
        print ("Message From Peer: ", msg)
        response = self.processRequest(msg)

        self.nodeSocket.sendto(bytes(response,'UTF-8'), self.peerAddress)
        print ("Peer at ", self.peerAddress , " disconnected...")

# Randomly pick files for the node
def init_random_file_list():
    numberOfBooks = random.randrange(3,6)
    fileNames = open("../File Names.txt", "r").read().split('\n')
    for x in range(numberOfBooks):
        myFiles.append(fileNames[random.randrange(0,len(fileNames))])
    print("My Files: ", myFiles)

# Join with 2 peers obtained from BS
def acknowledge_2_peers(ip, port, serverResponse):
    if (len(serverResponse)> 5):
        print("Peer1: ",serverResponse[3], int(serverResponse[4]))
        peer1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer1.connect((serverResponse[3], int(serverResponse[4])))
        peer1.send(("0033 JOIN " + ip + " " + str(port)).encode('utf-8'))
        
        from_peer1 = peer1.recvfrom(2048)
        print ("From Peer1: ", (from_peer1[0]).decode('utf-8'))
        peer1.close()

        print("Peer2: ",serverResponse[5], int(serverResponse[6]))
        peer2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer2.connect((serverResponse[5], int(serverResponse[6])))
        peer2.send(("0033 JOIN " + ip + " " + str(port)).encode('utf-8'))
        
        from_peer2 = peer2.recvfrom(2048)
        print ("From Peer2: ", (from_peer2[0]).decode('utf-8'))
        peer2.close()
    elif (len(serverResponse)> 3):
        print("Peer: ",serverResponse[3], int(serverResponse[4]))
        peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer.connect((serverResponse[3], int(serverResponse[4])))
        peer.send(("0033 JOIN " + ip + " " + str(port)).encode('utf-8'))

        from_peer = peer.recvfrom(2048)
        print ("From Peer: ", (from_peer[0]).decode('utf-8'))
        peer.close()

# Registration with BS and acknowledge peers
def register_with_bs(ip_bs, port_bs, ip_self, port_self, name_self):
    # Send registration to BS
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.connect((ip_bs, port_bs))
    server.send(("0033 REG " + ip_self + " " + str(port_self) + " " +  name_self).encode('utf-8'))

    # Receive response from BS for registration
    from_server = server.recvfrom(2048)
    serverResponse = (from_server[0]).decode('utf-8').split()
    server.close()

    acknowledge_2_peers(ip_self, port_self, serverResponse)

def init_udp_server_thread(host='127.0.0.1', port=1234):
    nodeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nodeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    nodeSocket.bind((host, port))

    print ("Listening peer requests on udp %s:%s" % (host, port))

    while True:
        data, peerAddress = nodeSocket.recvfrom(2048)    
        newThread = PeerThread(nodeSocket, peerAddress, data)
        newThread.start()

# BS details
ip_bs = sys.argv[1]
port_bs = int(sys.argv[2])

# Self details
ip_self = sys.argv[3] # can this be picked programatically
port_self = int(sys.argv[4])
name_self = sys.argv[5]

# [TODO] Input validation, print usage if wrong

# Join peers happen inside this
register_with_bs(ip_bs, port_bs, ip_self, port_self, name_self)

init_random_file_list()

# Open UDP server to listen to peers
init_udp_server_thread(ip_self, port_self)

# [TODO]Open REST Api to handle download requests

# Graceful termination, notify bs and peers