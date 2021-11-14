"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
import json
from socket import *
from threading import Thread
import sys
import time
import threading

# the imformation lists is here
credentials = "credentials.txt"
userDataLoc = "userData.json"
'''
userInfor = {
    'message': [],
    'blackList': [],
    'active_period': []
}
'''
# lock = threading.Lock()
blockList = []
onlineUser = []

# TODO: initialise the userData.json


# acquire server host and port from command line parameter
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
blockTime = int(sys.argv[2])
timeoutDur = int(sys.argv[3])
serverAddress = (serverHost, serverPort)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

serverStartTime = time.time()

# initialise the userData.json
with open(userDataLoc, 'r+') as f:
    f.truncate(0)
    f.write("{}")
    f.close()

# add every user in the credential into json file
with open(credentials, 'r+') as cf:
    userInfor = {
        'message': [],
        'blackList': [],
        'active_period': []
    }
    lines = cf.readlines()
    for line in lines:
        name, userPassword = line.split(" ")
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            data[name] = userInfor
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    cf.close()

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""


class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False

        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True

    def run(self):
        # the client have checked the user name is valid
        userName = self.clientSocket.recv(1024).decode()

        # check the blockList first
        for i in range(len(blockList)):
            if userName == blockList[i][0]:
                self.clientSocket.send(
                    "Your account is blocked due to multiple login failures. Please try again later".encode())
                sleepTime = blockTime - (time.time() - blockList[i][1])
                if (sleepTime > 0):
                    time.sleep(sleepTime)

        # get the password if the user name is in credential file
        # else return None
        isNewUser = False
        password = self.process_userName(userName)
        if password == None:
            isNewUser = True
            self.clientSocket.send("create your password: ".encode())
        else:
            password = password.strip()
            isNewUser = False
            self.clientSocket.send("password: ".encode())

        # check the password
        i = 0
        startTime = None
        while 1:
            # get the password from the client
            clientPassword = self.clientSocket.recv(1024).decode().strip()
            if isNewUser:
                # add the new account to credentials
                file = open(credentials, "a")
                file.write(f"{userName} {clientPassword}" + "\n")
                self.clientSocket.send("welcome".encode())
                startTime = time.time()
                # add the user information into json file
                userInfor = {
                    'message': [],
                    'blackList': [],
                    'active_period': []
                }
                self.addUserData(userName, userInfor)
                break
            if clientPassword == password:
                self.clientSocket.send("welcome".encode())
                startTime = time.time()
                with open(userDataLoc, 'r+') as f:
                    # add the user information into json file
                    data = json.load(f)
                    newPeriod = {
                        'start': startTime,
                        'end': time.time()
                    }
                    data[userName]['active_period'].append(newPeriod)
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                f.close()
                break
            else:
                if (i % 3 != 2):
                    self.clientSocket.send(
                        "Invalid Password. Please try again".encode())
                else:
                    self.clientSocket.send(
                        "Invalid Password. Your account has been blocked. Please try again later".encode())
                    blockList.append((userName, time.time()))
                    self.clientAlive = False
                    time.sleep(blockTime)
            i += 1

        # now assume the client enter the correct password
        # the timeout start
        onlineUser.append(userName)
        message = ''

        while self.clientAlive:

            self.clientSocket.settimeout(timeoutDur)
            # use recv() to receive message from the client
            try:
                # self.showMessage(userName)
                data = self.clientSocket.recv(1024)
                message = data.decode()
                messageWords = message.split(" ")
            except:
                if userName in onlineUser:
                    onlineUser.remove(userName)
                    self.addEndTime(userName, startTime)
                self.clientSocket.send("sorry you are timeout".encode())

            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if message == '':
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break

            # handle message from the client
            if message == 'logout':
                self.clientAlive == False
                onlineUser.remove(userName)
                # add the end time to the json
                self.addEndTime(userName, startTime)
                self.clientSocket.send("successfully logout".encode())
                break

            # message
            elif messageWords[0] == "message":
                if len(messageWords) != 3:
                    self.clientSocket.send(
                        "[error] message <user> <message>".encode)
                else:
                    if not self.isUserExist(messageWords[1]):
                        self.clientSocket.send("user not found".encode)
                    elif self.isHeBlocked(userName, messageWords[1]):
                        self.clientSocket.send(
                            f"you have been blocked by {messageWords[1]}".encode())
                    else:
                        self.message(messageWords[1], messageWords[2])
                        self.clientSocket.send(
                            "message send successful".encode())

            elif messageWords[0] == "block":
                if len(messageWords) != 2:
                    self.clientSocket.send("[error] block <user>".encode)
                else:
                    if not self.isUserExist(messageWords[1]):
                        self.clientSocket.send("user not found".encode)
                    else:
                        self.block(messageWords[1], userName)
                        self.clientSocket.send(
                            f"[recv] block {messageWords[1]} successfuly".encode())

            elif messageWords[0] == "unblock":
                if len(messageWords) != 2:
                    self.clientSocket.send("[error] unblock <user>".encode)
                else:
                    if not self.isUserExist(messageWords[1]):
                        self.clientSocket.send("user not found".encode)
                    else:
                        self.unblock(messageWords[1], userName)
                        self.clientSocket.send(
                            f"[recv] unblock {messageWords[1]} successfuly".encode())

            elif messageWords[0] == "whoelse":
                if len(messageWords) != 1:
                    self.clientSocket.send("[error] whoelse".encode())
                else:
                    whoelseList = self.whoelseList(userName)
                    self.clientSocket.send(f"[whoelse] {whoelseList}".encode())

            elif messageWords[0] == "broadcast":
                if len(messageWords) != 2:
                    self.clientSocket.send(
                        "[error] broadcast <message>".encode())
                else:
                    for user in self.whoelseList(userName):
                        self.message(user, messageWords[1])
                    self.clientSocket.send("broadcast successfully".encode())

            elif messageWords[0] == "receive":
                self.showMessage(userName)

            elif messageWords[0] == "whoelsesince":
                if len(messageWords) != 2:
                    self.clientSocket.send(
                        "[error] whoelsesince <time>".encode())
                else:
                    list = self.whoelsesince(userName, float(messageWords[1]))
                    self.clientSocket.send(f"[whoelsesince] {list}".encode())

            else:
                self.clientSocket.send("Sorry, I don't unserstand".encode())
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """

    def whoelseList(self, userName):
        whoelseList = []
        for user in onlineUser:
            if user != userName and not self.isHeBlocked(userName, user):
                whoelseList.append(user)
        return whoelseList

    def process_userName(self, inUserName):
        file = open(credentials, "r")
        lines = file.readlines()

        for line in lines:
            userName, password = line.split(" ")
            if userName == inUserName:
                # send confirmation message
                self.clientSocket.send("find user name".encode())
                return password

        self.clientSocket.send("user name not found".encode())
        return None

    def listOnlineUser():
        print(onlineUser)

    def isUserExist(self, inUserName):
        file = open(credentials, "r")
        lines = file.readlines()

        for line in lines:
            userName, password = line.split(" ")
            if userName == inUserName:
                # send confirmation message
                return True

        return False

    def addUserData(self, userName, userInformation):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            data[userName] = userInformation
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()

    def message(self, targetUser, message):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            data[targetUser]['message'].append(message)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def showMessage(self, userName):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            if data[userName]['message'] == None:
                self.clientSocket.send("no message since last visit".encode())
            for message in data[userName]['message']:
                self.clientSocket.send(f"[Message]:{ message }".encode())
            self.clientSocket.send(
                "that's all message since last visit".encode())
            data[userName]['message'].clear()
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def addEndTime(self, userName, startTime):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            for period in data[userName]['active_period']:
                if period['start'] == startTime:
                    period['end'] = time.time()
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def block(self, targetUserName, userName):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            if self.isHeBlocked(targetUserName, userName):
                self.clientSocket.send(
                    f"{userName} has alreadly been blocked".encode())
                return
            data[userName]['blackList'].append(targetUserName)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def unblock(self, targetUserName, userName):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            if not self.isHeBlocked(targetUserName, userName):
                self.clientSocket.send(
                    f"{userName} has not been blocked".encode())
                return
            data[userName]['blackList'].remove(targetUserName)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def isHeBlocked(self, targetUserName, userName):
        with open(userDataLoc, 'r') as f:
            data = json.load(f)
            if targetUserName in data[userName]['blackList']:
                return True
        f.close()
        return False

    def listAllUser(self):
        list = []
        file = open(credentials, "r")
        lines = file.readlines()

        for line in lines:
            userName, password = line.split(" ")
            list.append(userName)
        file.close()
        return list

    def whoelsesince(self, targetUserName, pasttime):
        now = time.time()
        since = now - pasttime
        whoelsesinceList = []
        with open(userDataLoc, 'r') as f:
            data = json.load(f)
            if (serverStartTime > since):
                for user in self.listAllUser():
                    if data[user]['active_period']:
                        whoelsesinceList.append(user)
            else:
                for user in self.listAllUser():
                    if user != targetUserName and data[user]['active_period']:
                        for period in data[user]['active_period']:
                            if period['start'] < since and period['end'] > since:
                                whoelsesinceList.append(user)
        f.close()
        return whoelsesinceList


print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    # lock.acquire()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()

# setup
# excuting the client command and notice new message
