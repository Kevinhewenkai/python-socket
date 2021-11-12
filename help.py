import string


def checkText(text):
    correct = string.ascii_letters + string.digits
    special = list("(~!@#$%^&*_-+=`|\(){}[]:;\"'<>,.?/)")
    for character in text:
        if ((character not in correct and character not in special) or character == " "):
            return False
    return True

# if __name__ == "__main__":
#     print(checkText("kevin123~!@#\")——"))
