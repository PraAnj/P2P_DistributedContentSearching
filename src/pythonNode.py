import random
import socket
import sys
import os
import threading
import shlex
import re
import flask
from flask import jsonify
import requests
import datetime
import hashlib
import string

myConnectedNodes = []
mySearchRequests = []
otherSearchRequests = []

noOfMsgsRecieved = 0
noOfMsgsAnswered = 0
noOfMsgsForwarded = 0

myFiles = []

ip_self = ''
port_self = 0
rest_port_self = 80

registrationSuccessCodes = ['0', '1', '2']
registrationErrorCodes = {
'commandError': '9999',
'alreadyRegistered': '9998',
'registeredToDifUser': '9997',
'BSFull': '9996'
}

class PeerThread(threading.Thread):
    def __init__(self, nodeSocket, peerAddress, data):
        threading.Thread.__init__(self)
        self.nodeSocket = nodeSocket
        self.peerAddress = peerAddress
        self.data = data
        # print ("New connection added: ", peerAddress)

    def processRequest(self, requestString):
        global myConnectedNodes
        global mySearchRequests
        global otherSearchRequests
        global ip_self
        global port_self
        global noOfMsgsRecieved
        global noOfMsgsAnswered

        # res = requestString.split()
        res = shlex.split(requestString)
        reqType = res[1]

        if reqType == 'JOIN':
            # Maximum number of nodes a node can join is 5
            # If already connected to 10 nodes decline the request
            if len(myConnectedNodes) > 10:
                print('Max number of nodes connected. Declining request')
                return '0016 JOINOK 9999'
            else :
                print("New node joined")
                myConnectedNodes.append((res[2], res[3]))
                print('My connected nodes: ', myConnectedNodes)
                return '0013 JOINOK 0'

        elif reqType == 'LEAVE':
            if len(myConnectedNodes) == 0:
                # No peers connected
                print('No peers connected')
                return '0013 LEAVEOK 0'
            elif 0 < len(myConnectedNodes) < 10:
                # Acceptable no of peers are connected
                print("A Node Leaved")
                myConnectedNodes.remove((res[2], res[3]))
                print('My connected nodes: ', myConnectedNodes)
                return '0013 LEAVEOK 0'
            else:
                # No of peer nodes are not acceptable
                print("Declining the leave request due to an error")
                return '0013 LEAVEOK 9999'

        elif reqType == 'SER':
            noOfMsgsRecieved = noOfMsgsRecieved + 1
            # print ('Search request received : ' + requestString)
            queryWithoutHops = requestString.rsplit(' ', 1)[0]

            # if this query is currently not processing
            if queryWithoutHops not in mySearchRequests and queryWithoutHops not in otherSearchRequests:
                query = res[4]
                hops = int(res[5])
                hops = hops + 1
                found, local, files, rest_ip, rest_port, hops = searchFile(res[2], int(res[3]), query, hops, False)

                noOfMsgsAnswered = noOfMsgsAnswered + 1

                if found: # reply to the peer
                    if local:
                        count = len(shlex.split(files))
                        return prefixLengthToRequest('SEROK '+ str(count) + ' ' + ip_self + ' ' + str(rest_port_self) +  ' ' + str(hops) + ' ' + files)
                    else: #Peer
                        return files
                else:
                    return '0010 ERROR'
            return '0010 ERROR'
        # Request Type cannot be identified
        return "Unrecognised request type"
        
    def run(self):
        global myConnectedNodes
        global mySearchRequests
        global otherSearchRequests        

        # print ("Connection from : ", self.peerAddress)
        msg = self.data.decode()        
        print("Message From Peer: ", msg)
        response = self.processRequest(msg)

        self.nodeSocket.sendto(bytes(response, 'UTF-8'), self.peerAddress)
        # print ("Peer at ", self.peerAddress , " disconnected...")


# Randomly pick files for the node    
def init_random_file_list():
    number_of_books = random.randrange(3, 6)
    file_names = open("../File Names.txt", "r").read().split('\n')
    
    count = 0
    while number_of_books > count:
        book = file_names[random.randrange(0, len(file_names))]

        if book not in myFiles: # To avoid duplicating files in the list
            count = count + 1   # To avoid creating file lists less than 3 when no of files is 3 and duplicate files found
            myFiles.append(book)
            
    print("My Files: ", myFiles)


def process_join_response_from_peers(msg):
    response = (msg[0]).decode('utf-8').split()

    # If 0 join response is successful
    # If 9999 join response not successful
    return response[2] == '0'


# Process the response for leave from peers
def process_leave_response_from_peers(msg):
    response = (msg[0]).decode('utf-8').split()
    if response[2] == '0':
        # Leave response is successful
        return True
    else:
        # Leave response is not successful
        return False


# Join with 2 peers obtained from BS
def acknowledge_2_peers(ip, port, name, serverResponse):
    global myConnectedNodes

    # Two random nodes recieved from BS
    if (len(serverResponse)> 5):
        print("Peer1: ",serverResponse[3], int(serverResponse[4]))

        # Send join request to first peer
        peer1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer1.connect((serverResponse[3], int(serverResponse[4])))

        peer1_join_req = "JOIN " + ip + " " + str(port)
        peer1_join_req = prefixLengthToRequest(peer1_join_req)
        peer1.send(peer1_join_req.encode('utf-8'))
        
        from_peer1 = peer1.recvfrom(2048)
        peer1.close()
        
        if (process_join_response_from_peers(from_peer1)) :
            print('Peer1 joined successfully')
            isSuccess = True
        else :
            print('Error occurred while joining Peer1')
            isSuccess = handle_errors_in_registration(ip, port, name) # If join request failed, unregister and register again with the same ip and port to get new 2 random nodes
        
        # If first node joined successfully, send the join request to second node
        if isSuccess :
            print("Peer2: ",serverResponse[5], int(serverResponse[6]))
            peer2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            peer2.connect((serverResponse[5], int(serverResponse[6])))

            peer2_join_req = "JOIN " + ip + " " + str(port)
            peer2_join_req = prefixLengthToRequest(peer2_join_req)
            peer2.send(peer2_join_req.encode('utf-8'))
            
            from_peer2 = peer2.recvfrom(2048)
            peer2.close()

            if (process_join_response_from_peers(from_peer2)) :
                print('Peer2 joined successfully')
                
                # If both nodes connected successfully add them to myConnectedNodes
                myConnectedNodes.extend([(serverResponse[3], serverResponse[4]), (serverResponse[5], serverResponse[6])])
                print('My connected nodes: ', myConnectedNodes)

                return True
            else :
                print('Error occurred while joining Peer2')
                isSuccess = handle_errors_in_registration(ip, port, name)

                if isSuccess :
                    myConnectedNodes.extend([(serverResponse[3], serverResponse[4]), (serverResponse[5], serverResponse[6])])
                    print('My connected nodes: ', myConnectedNodes)

                return isSuccess
    
    # One node recieved from BS
    elif (len(serverResponse)> 3):
        print("Peer: ",serverResponse[3], int(serverResponse[4]))
        peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer.connect((serverResponse[3], int(serverResponse[4])))

        peer_join_req = "JOIN " + ip + " " + str(port)
        peer_join_req = prefixLengthToRequest(peer_join_req)
        peer.send(peer_join_req.encode('utf-8'))

        from_peer = peer.recvfrom(2048)
        peer.close()

        if (process_join_response_from_peers(from_peer)) :
            print('Peer joined successfully')

            myConnectedNodes.append((serverResponse[3], serverResponse[4]))
            print('My connected nodes: ', myConnectedNodes)

            return True
        else :
            print('Error occurred while joining Peer')
            isSuccess = handle_errors_in_registration(ip, port, name)

            if isSuccess :
                myConnectedNodes.append((serverResponse[3], serverResponse[4]))
                print('My connected nodes: ', myConnectedNodes)
            return isSuccess


# LEAVE from peers obtained from BS
def leave_2_peers(ip, port, server_response):
    global myConnectedNodes
    print("Server Response for Leave from BS: ", server_response)

    # Server response should be containing 3 arguments
    if len(server_response) == 3:
        # Server response returns acceptable no of arguments
        # Sending leave requests for all the nodes connected
        for node_ip, node_port in myConnectedNodes:
            print("Peer: ", node_ip, node_port)
            peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            peer.connect((node_ip, int(node_port)))
    
            leave_request = "LEAVE " + ip + " " + str(port)
            leave_request = prefixLengthToRequest(leave_request)
            peer.send(leave_request.encode('utf-8'))

            from_peer = peer.recvfrom(2048)
            print("Response from peer for Leave Request: ", from_peer)
            peer.close()

            if process_leave_response_from_peers(from_peer):
                # Leave response is in the correct format
                print('Peer leaved successfully')
            else:
                # Leave response is not in the correct format
                print('Error occurred while leaving the peers')
                return False
        return True
    else:
        # Server response does not returns acceptable no of arguments
        print('Format error in the Error Response')
        return False


# Registration with BS and acknowledge peers
def register_with_bs(port, name):
    global ip_self

    # Send registration to BS
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSocket.connect((ip_bs, port_bs))

    ip_self = serverSocket.getsockname()[0]
    print('IP of the node: ', ip_self)

    reg_request = "REG " + ip_self + " " + str(port) + " " +  name
    reg_request = prefixLengthToRequest(reg_request)
    serverSocket.send(reg_request.encode('utf-8'))

    # Receive response from BS for registration
    from_server = serverSocket.recvfrom(2048)
    serverResponse = (from_server[0]).decode('utf-8').split()
    print('BS Response: ',serverResponse)
    serverSocket.close()
    
    if len(serverResponse) == 3 :
        if serverResponse[2] in registrationSuccessCodes:
            # first node of te netwrok registered
            return True
        else:
            # Registration response contains an error code
            if serverResponse[2] == registrationErrorCodes["commandError"] :
                print('Error in command. Please try again!')
                return False
            elif serverResponse[2] == registrationErrorCodes["BSFull"] :
                print('Bootstrap Server is full! Please try again later')
                return False
            else :
                # Already registered or given IP and port is used by another node. Therefore unregister and register again
                return handle_errors_in_registration(ip_self, port, name, True)
    else:
        # Registration response contains details of one / two random nodes in the network. Send join requests
        return acknowledge_2_peers(ip_self, port_self, name_self, serverResponse)


def handle_errors_in_registration(ip, port, name, isReg = False):
    global ip_self
    global port_self
    global name_self
    
    # Unregister first
    unregister_with_bs(ip_bs, port_bs, ip, port, name)

    if isReg :
        print('Given ip and port is already used by another node. Please try a different ip and port')
        # Get new IP and port from user
        port_self, name_self = get_user_arguements(True)
        isSuccess = register_with_bs(port_self, name_self)
    else :
        # Again register using same IP and port to get 2 new random nodes
        print('Getting 2 new random nodes ')
        isSuccess = register_with_bs(port, name)

    return isSuccess


# De-registration with BS and notify peers
def unregister_with_bs(bs_ip, bs_port, self_ip, self_port, self_name):
    print("Leaving the network.")
    # Send de-registration to BS
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.connect((bs_ip, bs_port))
    
    unreg_request = "UNREG " + self_ip + " " + str(self_port) + " " + self_name
    unreg_request = prefixLengthToRequest(unreg_request)
    server.send(unreg_request.encode('utf-8'))

    # Receive response from BS for registration
    from_server = server.recvfrom(2048)
    server_response = (from_server[0]).decode('utf-8').split()
    server.close()
    print("Server Response for unregistering with BS: ", server_response)

    if server_response[1] == 'UNROK' and server_response[2] == '0':
        # Received correct response from the BS
        print('Successfully received response from the BS')
        is_leaving_success = leave_2_peers(self_ip, self_port, server_response)
        return is_leaving_success
    else:
        # Received an incorrect response from the BS
        print('Error in leaving the network. Please try again!')
        return False


# Check whether local file contains the words in query
def check_query_against_local_file(main, sub_split):
    index = -1
    for word in sub_split:
        index = main.find(word, index + 1)
        if index == -1:
            return False
    return True

def isQueryMatch(search_string, input_string):
  raw_search_string = r"\b" + search_string + r"\b"
  match_output = re.search(raw_search_string, input_string, flags=re.IGNORECASE)
  return ( match_output is not None )


# Check whether file is available locally in file list
def get_matching_file_local(search_file):
    matched_file_list = []
    search_file = search_file.lower()
    search_file_words = search_file.split()
    for local_file in myFiles:
        if check_query_against_local_file(local_file.lower(), search_file_words) and local_file not in matched_file_list:
            matched_file_list.append(local_file)

    print("Matched Files List : ", matched_file_list)
    return matched_file_list

def addToRequestCache(ownRequest, request):
    uniqueQuery = request.rsplit(' ', 1)[0] #without hops
    if ownRequest:
        mySearchRequests.append(uniqueQuery)
    else:
        otherSearchRequests.append(uniqueQuery)

def removeFromRequestCache(ownRequest, request):
    uniqueQuery = request.rsplit(' ', 1)[0] #without hops
    if ownRequest:
        mySearchRequests.remove(uniqueQuery)
    else:
        otherSearchRequests.remove(uniqueQuery)

# Prefix command length as 4 characters before sending UDP msg
def prefixLengthToRequest(request):
    length = len(request) + 5
    lengthPrefix = f'{length:04}'
    print (lengthPrefix + ' ' + request)
    return lengthPrefix + ' ' + request

def searchFile(ip_self, port_self, query, hops, ownRequest):
    global noOfMsgsForwarded
    # print ('Searching file :' + query)

    file = get_matching_file_local(query) # Find in local files
    if file:
        result= ''
        for element in file:
            element = "\""+element+"\""
            result += str(element)
            result += ' '
        return (True, True, result.strip(), 'Local Machine', rest_port_self, str(hops))
    if not myConnectedNodes:
        return (False, False, "0010 ERROR", "", 0, "0")

    # flooding stops at 10 hops
    if hops > 10:
        return (False, False, "0010 ERROR", "", 0, "0")

    request = "SER " + ip_self + ' ' + str(port_self) + ' \"' +  query + '\" ' + str(hops)
    request = prefixLengthToRequest(request)

    addToRequestCache(ownRequest, request) # add to global request cache

    # Send search request to peers, handles in PeerThread event loop
    for peer in myConnectedNodes:
        ip_peer = peer[0]
        port_peer = peer[1]

        noOfMsgsForwarded = noOfMsgsForwarded + 1
        # print ('Searching on peer [' + ip_peer + ':' + str(port_peer)+']')
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.connect((ip_peer, int(port_peer)))
        server.send((request).encode('utf-8'))

        from_server = server.recvfrom(2048)
        responseString = (from_server[0]).decode('utf-8')
        serverResponse = shlex.split(responseString) #shlex.split preserve quotes
        server.close()

        if len(serverResponse) >= 2 and serverResponse[1] == 'SEROK':
            print(serverResponse)
            rest_ip = serverResponse[3]
            rest_port = serverResponse[4]
            removeFromRequestCache(ownRequest, request) #remove from cache
            if ownRequest:
                fileCount = int(serverResponse[2])
                result = ''
                for i in range(6, 6+fileCount):
                    fileName = "\""+serverResponse[i]+"\""
                    result += fileName
                    result += ' '
                return True, False, result.strip(), rest_ip, int(rest_port), serverResponse[5]  # i am the originator of this
            else:
                return True, False, responseString,  rest_ip, int(rest_port), serverResponse[5] # same peer response forwarded

    removeFromRequestCache(ownRequest, request) #remove from cache
    return (False, False, "0010 ERROR", "", 0, str(hops))

def init_udp_server_thread(host='127.0.0.1', port=1234):
    nodeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nodeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    nodeSocket.bind((host, port))

    print ("Listening peer requests on udp %s:%s" % (host, port))

    while True:
        data, peerAddress = nodeSocket.recvfrom(2048)    
        newThread = PeerThread(nodeSocket, peerAddress, data)
        newThread.start()

# Input size is in MBs
def getRandomData(filename, size):
    # generate random data to be downloaded
    data = ''.join([random.choice(string.ascii_letters) for i in range(size*1024*1024)])
    return data

def runRESTServerForDownloadRequests(rest_port_self):
    app = flask.Flask(__name__)
    # app.config["DEBUG"] = True

    @app.route('/download/<filename>', methods = ['GET'])
    def download(filename):
        datasize_MB = random.randint(2,10)
        data = getRandomData(filename, datasize_MB)
        hash_SHA = hashlib.sha256(data.encode('utf-8')).hexdigest()
        print('Data generated: hash = ' + hash_SHA + ', size = ' + str(datasize_MB) + 'MB')

        return jsonify(
            hash=hash_SHA,
            datasize=datasize_MB,
            data=data,
            filename=filename,
            ip=ip_self,
            udp_port=str(port_self)
            )

    @app.route('/', methods=['GET'])
    def home():
        return "<h1>File Download service</h1><p>Post a GET request as http://172.0.0.1:<rest_port_self>/download/filename.txt</p>"

    app.run(host='0.0.0.0', port=rest_port_self)

def downloadFileViaRESTCall(ip, port, filename):
    x = requests.get('http://' + ip + ':' + str(port) + '/download/' + filename)
    dictResponse = x.json()
    hash_SHA = hashlib.sha256(dictResponse['data'].encode('utf-8')).hexdigest()
    print(dictResponse['hash'] + ' is received from server')
    print(hash_SHA + ' is generated locally.')

    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    with open(os.path.join(__location__, filename.strip('\"')), 'w') as f:
        f.write(dictResponse['data'])
        print('Data downloaded: size = ' + str(dictResponse['datasize']) + 'MB')

def get_user_arguements(isRetry = False):
    global ip_bs
    global port_bs

    if not isRetry : 
        print("IP of BS:")
        ip_bs = input()
        print("Port of BS:")
        port_bs = int(input())

    print("Port of the new node:")
    port_self = int(input())
    print("Name of the new node")
    name_self = input()
    print("Port of the REST api")
    rest_port_self = int(input())
    
    return (port_self, name_self, rest_port_self)

# [TODO] Input validation, print usage if wrong
if len(sys.argv) < 6 :
    port_self, name_self, rest_port_self = get_user_arguements()

else:
    # BS details
    ip_bs = sys.argv[1]
    port_bs = int(sys.argv[2])

    # Self details
    port_self = int(sys.argv[3])
    name_self = sys.argv[4]
    rest_port_self = int(sys.argv[5])

# ip_self = socket.gethostbyname(socket.gethostname())
# print ('Host IP is: ' + ip_self)

if register_with_bs(port_self, name_self) :
    init_random_file_list()

    # Start flask REST api to handle download requests
    restApiThread = threading.Thread(target=runRESTServerForDownloadRequests, args=(rest_port_self,))
    restApiThread.start()

    # Event loop for peer connections (UDP server) runs on a different thread
    peerEventLoop = threading.Thread(target=init_udp_server_thread, args=(ip_self, port_self,))
    peerEventLoop.start()

    while True:
        query = input("1. Press X to leave the network.\n2. Press S to view the current status of the node.\n3. Press search query to search.\n")
        if query == 'X':
            # Executing unregistering process
            is_un_registered = unregister_with_bs(ip_bs, port_bs, ip_self, port_self, name_self)
            if is_un_registered:
                print("Leaved the BS and peers successfully")
                exit()
            else:
                print("Error Occurred while leaving the BS and peers. Please try again")
                # Retrying to leave the network again
                query = input("1. Press X to try again to leave the network.\n")
                if query == 'X':
                    is_un_registered = unregister_with_bs(ip_bs, port_bs, ip_self, port_self, name_self)
                    if is_un_registered:
                        print("Leaved the BS and peers successfully")
                        exit()
                    else:
                        print("Error Occurred while leaving the BS and peers. Tried twice hence exiting")
                        exit()

        elif query == 'S':
            print('IP : ', ip_self)
            print('Port : ', port_self)
            print('Available Files : ', myFiles)
            print('Connected Nodes : ', myConnectedNodes)
            print('Search Requests Initiated: ', mySearchRequests)
            print('Other Search Requests : ', otherSearchRequests)
            print('No of queries received : ', noOfMsgsRecieved)
            print('No of queries forwarded : ', noOfMsgsForwarded)
            print('No of queries answered : ', noOfMsgsAnswered)

        else:
            start_time = datetime.datetime.now()
            found, local, file, rest_ip, rest_port, hops = searchFile(ip_self, port_self, query, 1, True)
            end_time = datetime.datetime.now()
            if found:
                print ('Found file : ' + file + ' at ' + rest_ip + ":" + str(rest_port))
                if not local:
                    downloadFileViaRESTCall(rest_ip, rest_port, file)
            else:
                print ('File not found.')
            print ('Latency: ' + str(end_time - start_time))
            print('Hops : ' + hops)

# [TODO]Open REST Api to handle download requests

# Graceful termination, notify bs and peers