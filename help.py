import string


def checkText(text):
    correct = string.ascii_letters + string.digits
    special = list("(~!@#$%^&*_-+=`|\(){}[]:;\"'<>,.?/)")
    for character in text:
        if ((character not in correct and character not in special) or character == " "):
            return False
    return True


def receive(clientSocket):
    while 1:
        data = clientSocket.recv(1024)
        receivedMessage = data.decode()
        receivedMessage = receivedMessage.strip()

        if receivedMessage == "no message since last visit":
            break
        elif receivedMessage == "that's all message since last visit":
            break
        elif receivedMessage == "sorry you are timeout":
            print(receivedMessage)
            exit()
        else:
            print(receivedMessage)


def wating_input(clientSocket):
    while 1:
        message = input(
            "===== Please type any messsage you want to send to server: =====\n")
        for word in message.split(" "):
            if not help.checkText(word):
                print("invalid format")
                continue
        clientSocket.sendall(message.encode())
        break
# if __name__ == "__main__":
#     print(checkText("kevin123~!@#\")——"))
