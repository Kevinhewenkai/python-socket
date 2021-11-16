"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
import os
import threading
import time
from socket import *
import sys
import random
import help
from threading import Thread

lock = threading.Lock()
privateMessage = False
privateChatSocket = {}
privateContact = []
existedPort = []
user = ""
host = ""
port = ""


class InputThread(Thread):
    def __init__(self, clientsocket):
        Thread.__init__(self)
        self.clientsocket = clientsocket

    def run(self):
        # global lock
        # with lock:
        #     clientSocket.send("broadcast join the chat\n".encode())
        while 1:
            message = input(
                "===== Please type any messsage you want to send to server: =====\n")
            for word in message.split(" "):
                if not help.checkText(word):
                    print("invalid format")
                    continue

            words = message.split(" ")
            # print(words)
            if words[0] == "private":
                print("if words[0] == 'private':")
                if len(words) < 3:
                    print("[error], private <user> <message> ")
                    continue
                targetuser = words[1]
                if targetuser not in privateContact:
                    print("[error] please startprivate first")
                outMessage = ""
                for i in range(2, len(words)):
                    outMessage = outMessage + " " + words[i]
                # find the corresponding socket
                print(privateChatSocket)
                targetSocket = privateChatSocket[targetuser]
                targetSocket.send(message.encode())
                print("send successfully")
                continue

            # receive the notice from the receive thread
            # give the server port number
            global privateMessage
            global user
            global port
            global host
            # TODO delete
            print(privateMessage)
            while (privateMessage):
                if ("yes") in message:
                    print("======here========")
                    self.clientsocket.send(
                        "[private response] yes".encode())
                    privateContact.append(user)
                    # TODO reached, delete
                    # create socket
                    # newSocket = socket(AF_INET, SOCK_STREAM)
                    # address = (host, int(port))
                    # newSocket.bind(address)
                    # privateChatSocket[user] = newSocket
                    # delete the duplicate
                    privateMessage = False
                elif ("no") in message:
                    self.clientsocket.send("[private response] no".encode())
                    privateMessage = False
                else:
                    message = input("====please type yes or no====")

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
            # get the first request
            # tell the input thread
            elif "[private request]" in receivedMessage:
                # reached
                print("========get the first request========")
                global privateMessage
                global user
                global host
                global port
                privateMessage = True
                messageWords = receivedMessage.split(" ")
                index = messageWords.index("request]")
                user = messageWords[index + 1]
                host = messageWords[index + 2]
                port = messageWords[index + 3]
            elif ("[successful response]") in receivedMessage:
                print("==========[successful response]======")
                messageWords = receivedMessage.split(" ")
                index = messageWords.index("response]:")
                name = messageWords[index + 1]
                host = messageWords[index + 2]
                port = messageWords[index + 3]
                newSocket = socket(AF_INET, SOCK_STREAM)
                address = (host, int(port))
                newSocket.connect(address)
                privateChatSocket[name] = newSocket
                privateContact.append(name)
                # delete the duplicate
                # privateChatAddress[privateUserName] = privateAddress
                # print(privateChatAddress)
            else:
                print(receivedMessage)


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

onlineCheck = clientSocket.recv(1024).decode()
print(f"online check: {onlineCheck}")
if ("[error]" in onlineCheck):
    exit()

# receive the comfirmation message of the user name
nameCheck = clientSocket.recv(1024).decode()
print(nameCheck)
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
with lock:
    clientSocket.send("broadcast join the chat\n".encode())
