"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: Wei Song (Tutor for COMP3331/9331)
"""
import json
import random
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
noNewContent = True
threads = {}
usedPort = []

# TODO: initialise the userData.json


# acquire server host and port from command line parameter
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
usedPort.append(serverPort)
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
        'active_period': [],
        'clientAddress': None
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
        usedPort.append(clientAddress[1])
        self.clientSocket = clientSocket
        self.clientAlive = False

        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True

    def run(self):
        global onlineUser
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

        # check the user is online or not
        if userName in onlineUser:
            self.clientSocket.send("[error], this account is online".encode())
        else:
            self.clientSocket.send("[success]".encode())

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
                    data[userName]['clientAddress'] = clientAddress
                    threads[userName] = self
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
        self.showOfflineMessage(userName)
        timeoutCounter = TimeoutCounter(
            timeoutDur, self.clientSocket, userName)
        timeoutCounter.start()

        while self.clientAlive:
            self.clientSocket.settimeout(timeoutDur)
            # use recv() to receive message from the client
            # delete the duplicate
            try:
                data = self.clientSocket.recv(1024)
                message = data.decode()
                # global noNewContent
                # if not message.startswith("receive"):
                #     noNewContent = False
                messageWords = message.split(" ")
            except:
                if userName in onlineUser:
                    onlineUser.remove(userName)
                    self.addEndTime(userName, startTime)
                try:
                    self.clientSocket.send("sorry you are timeout".encode())
                except:
                    print("one client is timeout")
                    break

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
                if len(messageWords) < 3:
                    self.clientSocket.send(
                        "[error] message <user> <message>".encode)
                else:
                    resultMessage = ""
                    for i in range(2, len(messageWords)):
                        resultMessage = resultMessage + " " + messageWords[i]
                    if not self.isUserExist(messageWords[1]):
                        self.clientSocket.send("user not found".encode)
                    elif self.isHeBlocked(userName, messageWords[1]):
                        self.clientSocket.send(
                            f"you have been blocked by {messageWords[1]}".encode())
                    else:
                        if messageWords[1] not in onlineUser:
                            self.offlineMessage(
                                userName, messageWords[1], resultMessage)
                        else:
                            threads[messageWords[1]].messageWords(
                                f"[{userName}]: {resultMessage}")
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
                if len(messageWords) < 2:
                    self.clientSocket.send(
                        "[error] broadcast <message>".encode())
                else:
                    resultMessage = ""
                    for i in range(1, len(messageWords)):
                        resultMessage = resultMessage + " " + messageWords[i]
                    for user in self.whoelseList(userName):
                        threads[user].messageWords(
                            f"[{userName}] {resultMessage}")
                    self.clientSocket.send("broadcast successfully".encode())

            # elif messageWords[0] == "receive":
            #     print("==receive==")
            #     self.showOfflineMessage(userName)

            elif messageWords[0] == "whoelsesince":
                if len(messageWords) != 2:
                    self.clientSocket.send(
                        "[error] whoelsesince <time>".encode())
                else:
                    list = self.whoelsesince(userName, float(messageWords[1]))
                    self.clientSocket.send(f"[whoelsesince] {list}".encode())

            elif messageWords[0] == "startprivate":
                if len(messageWords) != 2:
                    self.clientSocket.send(
                        "[error] startprivate <user>".encode())
                else:
                    targetuser = messageWords[1]
                    # simple tell the user someone want to join
                    self.startprivate(targetuser, userName)
                    return

            elif messageWords[0] == "[responseY]":
                createSocketUser = messageWords[1]
                connectSocketUser = messageWords[2]
                host = messageWords[3]
                port = self.generatePort()
                self.noticeCreatePort(createSocketUser, port, host)
                self.noticeConnectPort(connectSocketUser, port, host)

            elif messageWords[0] == "[responseN]":
                threads[createSocketUser].messageWords(
                    "the user reject private connection")

            else:
                # if (not str(message).startswith("receive")):
                self.clientSocket.send(
                    "Sorry, I don't understand".encode())
                # print(message)
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
        whoelseList = set(whoelseList)
        whoelseList = list(whoelseList)
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

    def offlineMessage(self, userName, targetUser, message):
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            resultMessage = f"[offline] {userName} {message}"
            data[targetUser]['message'].append(resultMessage)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        f.close()
        return

    def showOfflineMessage(self, userName):
        time.sleep(0.1)
        with open(userDataLoc, 'r+') as f:
            data = json.load(f)
            if not data[userName]['message']:
                return
            else:
                # messageNotice = data[userName]['message']
                # print(messageNotice)
                for message in data[userName]['message']:
                    splitmessage = message.split(" ")
                    messageWord = ""
                    for i in range(2, len(splitmessage)):
                        messageWord = messageWord + splitmessage[i] + " "
                    self.clientSocket.send(
                        f"[offline] [{splitmessage[1]}]: {messageWord}\n".encode())
                    data[userName]['message'].remove(message)
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

    def startprivate(self, targetuser, userName):
        if not self.isUserExist(targetuser):
            self.clientSocket.send(
                "[error], user not exist".encode())
            return
        if self.isHeBlocked(userName, targetuser):
            self.clientSocket.send(
                f"[error], you have been blocked by {targetuser}".encode())
            return
        if targetuser not in onlineUser:
            self.clientSocket.send(
                "[error], user not online".encode())
            return
        # tell the targetClient, ask for agreement
        # send [private request]
        # TODO random a port number and create a socket then this socket will keep listening

        request = f" [private request] {userName} {self.clientAddress[0]} -> {targetuser}"
        threads[targetuser].messageWords(request)

    def generatePort(self):
        while 1:
            privateport = random.randint(2001, 12000)
            if privateport not in usedPort:
                return privateport

    def noticeCreatePort(self, userName, port, host):
        threads[userName].messageWords(f"[portCreate] {port} {host}")

    def noticeConnectPort(self, userName, port, host):
        threads[userName].messageWords(f"[portConnect] {port} {host}")

    def receiveWords(self):
        response = self.clientSocket.recv(1024).decode()
        return response

    def messageWords(self, message):
        self.clientSocket.send(message.encode())


class TimeoutCounter(Thread):
    def __init__(self, timeoutDur, clientSocket, userName):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.timeoutDur = timeoutDur
        self.userName = userName

    def run(self):
        startTime = time.time()
        timeout = False
        global noNewContent
        global onlineUser
        while not timeout:
            if noNewContent:
                now = time.time()
                if (now - startTime) > self.timeoutDur:
                    try:
                        self.clientSocket.send(
                            "sorry you are timeout".encode())
                        onlineUser.remove(self.userName)
                    except:
                        print("timeout")
                    timeout = True
                    time.sleep(0.1)
                    break
            else:
                noNewContent = True
                startTime = time.time()


print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")

while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()

# setup
# excuting the client command and notice new message
