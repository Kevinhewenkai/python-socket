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
user1 = ""
user2 = ""
host = ""
port = ""


class InputThread(Thread):
    def __init__(self, clientsocket, userName):
        Thread.__init__(self)
        self.clientsocket = clientsocket
        self.username = userName

    def run(self):
        global lock
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
                try:
                    targetSocket = privateChatSocket[targetuser]
                    print(targetSocket)
                    with lock:
                        targetSocket.send(
                            f"[{self.username}][private] {outMessage}".encode())
                    print("send successfully")
                except:
                    print("[error] don't have p2p connection")
                continue
            elif words[0] == "stopprivate":
                if len(words) < 2:
                    print("[error], stopprivate <user>")
                    continue
                targetuser = words[1]
                if targetuser not in privateContact:
                    print(f"[error], no p2p with {targetuser}")
                else:
                    privateChatSocket.pop(targetuser, None)
                    privateContact.remove(targetuser)
                    print("[stop private] success")

                # receive the notice from the receive thread
                # give the server port number
            global privateMessage
            global user1
            global user2
            while (privateMessage):
                if ("yes") in message:
                    with lock:
                        self.clientsocket.send(
                            f"[responseY] {user1} {user2} {host}".encode())
                        time.sleep(0.1)
                    # privateContact.append(user1)
                    privateMessage = False
                elif ("no") in message:
                    with lock:
                        self.clientsocket.send("[responseN]".encode())
                        time.sleep(0.1)
                    privateMessage = False
                else:
                    message = input("====please type yes or no====\n")
                    time.sleep(0.1)
            with lock:
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
                print("========input yes or no========")
                global privateMessage
                privateMessage = True
                global user1
                global user2
                global host
                # global port
                messageWords = receivedMessage.split(" ")
                index = messageWords.index("request]")
                user1 = messageWords[index + 1]
                host = messageWords[index + 2]
                user2 = messageWords[index + 4]
            elif "[portCreate]" in receivedMessage:
                messageWords = receivedMessage.split(" ")
                index = messageWords.index("[portCreate]")
                privateport = messageWords[index + 1]
                privatehost = messageWords[index + 2]
                targetUserName = messageWords[index + 3]
                privateContact.append(targetUserName)
                # TODO
                privateSocket = socket(AF_INET, SOCK_STREAM)
                address = (privatehost, int(privateport))
                # print(address)
                privateSocket.bind(address)
                privateSocket.listen(1)
                csocket, clientAddress = privateSocket.accept()
                privateChatSocket[targetUserName] = csocket
                # while 1:
                #     data = csocket.recv(1024).decode()
                #     print(data)
                newThread = PrivateReceiveServer(csocket)
                newThread.start()
            elif "[portConnect]" in receivedMessage:
                time.sleep(0.1)
                messageWords = receivedMessage.split(" ")
                index = messageWords.index("[portConnect]")
                privateport = messageWords[index + 1]
                privatehost = messageWords[index + 2]
                targetUserName = messageWords[index + 3]
                privateContact.append(targetUserName)
                privateSocket = socket(AF_INET, SOCK_STREAM)
                address = (privatehost, int(privateport))
                # print(address)
                privateSocket.connect(address)
                privateChatSocket[targetUserName] = privateSocket
                # while 1:
                #     data = privateSocket.recv(1024).decode()
                #     print(data)
                newThread = PrivateReceiveServer(privateSocket)
                newThread.start()
            elif "[block]" in receivedMessage:
                os._exit(1)
                # privateChatAddress[privateUserName] = priva
                # delete the duplicate
                # print(privateChatAddress)
            # else:
                # print(receivedMessage)


class PrivateReceiveServer(Thread):
    def __init__(self, privateSocket):
        Thread.__init__(self)
        self.privateSocket = privateSocket

    def run(self):
        while 1:
            try:
                data = self.privateSocket.recv(1024).decode()
                print(data)
            except:
                print("the source socket is timeout")
                break


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
print(f"{onlineCheck}")
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
inputThread = InputThread(clientSocket, userName)
receiveServer = ReceiveServer(clientSocket)
inputThread.start()
receiveServer.start()
with lock:
    clientSocket.send("broadcast join the chat\n".encode())
