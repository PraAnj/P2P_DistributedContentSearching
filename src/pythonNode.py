import socket, threading
import sys
import random

myConnectedNodes = []
mySearchRequests = []
otherSearchRequests = []
myFiles = []

class PeerThread(threading.Thread):
    def __init__(self, peerAddress, data):
        threading.Thread.__init__(self)
        self.peerAddress = peerAddress
        self.data = data
        print ("New connection added: ", peerAddress)

    def processRequest(self, requestString):
        global myConnectedNodes
        global mySearchRequests
        global otherSearchRequests

        res = requestString.split()
        reqType = res[1]
        
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

        print ("Connection from : ", peerAddress)

        msg = self.data.decode()        
        print ("Message From Peer: ", msg)
        response = self.processRequest(msg)

        nodeSocket.sendto(bytes(response,'UTF-8'), peerAddress)
        print ("Peer at ", peerAddress , " disconnected...")

ip = sys.argv[1]
port = sys.argv[2]
name = sys.argv[3]

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.connect((ip, 55555))
server.send(("0033 REG " + ip + " " + port + " " +  name).encode('utf-8'))

from_server = server.recvfrom(2048)
serverResponse = (from_server[0]).decode('utf-8').split()
server.close()

numberOfBooks = random.randrange(3,6)
fileNames = open("../File Names.txt", "r").read().split('\n')

for x in range(numberOfBooks):
    myFiles.append(fileNames[random.randrange(0,len(fileNames))])
  
print("My Files: ", myFiles)

if (len(serverResponse)> 5):
    print("Peer1: ",serverResponse[3], int(serverResponse[4]))
    peer1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    peer1.connect((serverResponse[3], int(serverResponse[4])))
    peer1.send(("0033 JOIN " + ip + " " + port).encode('utf-8'))
    
    from_peer1 = peer1.recvfrom(2048)
    print ("From Peer1: ", (from_peer1[0]).decode('utf-8'))
    peer1.close()

    print("Peer2: ",serverResponse[5], int(serverResponse[6]))
    peer2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    peer2.connect((serverResponse[5], int(serverResponse[6])))
    peer2.send(("0033 JOIN " + ip + " " + port).encode('utf-8'))
    
    from_peer2 = peer2.recvfrom(2048)
    print ("From Peer2: ", (from_peer2[0]).decode('utf-8'))
    peer2.close()
elif (len(serverResponse)> 3):
    print("Peer: ",serverResponse[3], int(serverResponse[4]))
    peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    peer.connect((serverResponse[3], int(serverResponse[4])))
    peer.send(("0033 JOIN " + ip + " " + port).encode('utf-8'))

    from_peer = peer.recvfrom(2048)
    print ("From Peer: ", (from_peer[0]).decode('utf-8'))
    peer.close()

nodeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
nodeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
nodeSocket.bind((ip, int(port)))

print("Waiting for a request..")

while True:
    data, peerAddress = nodeSocket.recvfrom(2048)    
    newThread = PeerThread(peerAddress, data)
    newThread.start()
