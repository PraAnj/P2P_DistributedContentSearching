import socket

msgFromClient = "0036 REG 129.82.123.45 5001 1234abcd"
bytesToSend = str.encode(msgFromClient)
serverAddressPort   = ("192.168.1.2", 55555)
bufferSize          = 1024

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

msg = "Message from Server {}".format(msgFromServer[0])

print(msg)
