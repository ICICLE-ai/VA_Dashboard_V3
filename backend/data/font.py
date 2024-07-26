class showMessage:
    def __init__(self, messageType, messageIndent, message):
        if messageType == "title":
            self.color = '\033[38;2;96;108;56m'
        elif messageType == "content":
            self.color = '\033[38;2;40;54;24m'
        elif messageType == "explain":
            self.color = '\033[38;2;221;161;94m'
        else:
            self.color = '\033[38;2;188;108;37m'
        self.printMessage(self.color, messageIndent, message)

    def printMessage(self, color, indent, message):
        print(f"{color}{' '*indent}{message}{color}")