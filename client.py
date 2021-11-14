"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
import os
import time
from socket import *
import sys
import help
from threading import Thread


class InputThread(Thread):
    def __init__(self, clientsocket):
        Thread.__init__(self)
        self.clientsocket = clientsocket

    def run(self):
        while 1:
            message = input(
                "===== Please type any messsage you want to send to server: =====\n")
            for word in message.split(" "):
                if not help.checkText(word):
                    print("invalid format")
                    continue
            self.clientsocket.sendall(message.encode())
            time.sleep(0.1)


class ReceiveServer(Thread):
    def __init__(self, clientsocket):
        Thread.__init__(self)
        self.clientsocket = clientsocket

    def run(self):
        while 1:
            try:
                data = clientSocket.recv(1024)
            except:
                print("sorry, you have timeout")
                os._exit(1)
            receivedMessage = data.decode()
            if receivedMessage == "no message since last visit":
                continue
            elif receivedMessage == "that's all message since last visit":
                continue

            print(receivedMessage + "\n")

            # parse the message received from server and take corresponding actions
            if receivedMessage == "":
                print("[recv] Message from server is empty!")
            elif receivedMessage == "successfully logout":
                clientSocket.close()
                os._exit(1)
            elif receivedMessage == "sorry you are timeout":
                clientSocket.close()
                os._exit(1)


# Server would be running on the same host as Client
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)

# User Authentication
while 1:
    userName = input("Username: ")
    if not help.checkText(userName):
        print("invalid userName")
    else:
        clientSocket.send(userName.encode())
        break

# receive the comfirmation message of the user name
userName = clientSocket.recv(1024).decode()
print(userName)
# get the password not, create a new password or check the password is done by server
passwordNote = clientSocket.recv(1024).decode()
# send the correct format password to server
while 1:
    password = input(passwordNote)
    if not help.checkText(password):
        print("invalid password format")
    else:
        clientSocket.send(password.encode())
        break

# get the response of the password
for i in range(3):
    response = clientSocket.recv(1024).decode()
    print(response)
    if (response == "welcome"):
        break
    else:
        if (i == 2):
            exit()
            # break
        password = input("password: ")
        clientSocket.send(password.encode())

# # get the offline message
# clientSocket.send("offline")
inputThread = InputThread(clientSocket)
receiveServer = ReceiveServer(clientSocket)
inputThread.start()
receiveServer.start()
