#  ██████╗ ███████╗██████╗ ██████╗  ██████╗ ██╗      ██████╗ ██████╗ ███████╗███████╗
#  ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔═══██╗██║     ██╔═══██╗██╔══██╗██╔════╝██╔════╝
#  ██████╔╝█████╗  ██║  ██║██████╔╝██║   ██║██║     ██║   ██║██████╔╝█████╗  ███████╗
#  ██╔═══╝ ██╔══╝  ██║  ██║██╔══██╗██║   ██║██║     ██║   ██║██╔═══╝ ██╔══╝  ╚════██║
#  ██║     ███████╗██████╔╝██║  ██║╚██████╔╝███████╗╚██████╔╝██║     ███████╗███████║
#  ╚═╝     ╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚══════╝╚══════╝
#
#   █████╗ ███████╗ █████╗ ██████╗ ███████╗
#  ██╔══██╗╚════██║██╔══██╗╚════██╗╚════██║
#  ╚██████║    ██╔╝╚█████╔╝ █████╔╝    ██╔╝
#   ╚═══██║   ██╔╝ ██╔══██╗██╔═══╝    ██╔╝
#   █████╔╝   ██║  ╚█████╔╝███████╗   ██║
#   ╚════╝    ╚═╝   ╚════╝ ╚══════╝   ╚═╝
#
"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self,command: str = None):
        self.command = command


class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self,channel: str = None):
        super().__init__("join")
        if channel == '' or channel ==  None:
            self.channel = "#general"
        else:
            self.channel = channel
    #end


    def __repr__( self ) -> str:
        return json.dumps(self.__dict__)

    def __len__ ( self ) -> int:
        return len(str(self))


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self,user: str = "student"):
        super().__init__("register")
        self.user = user
    #end
    def __repr__( self ) -> str:
        return json.dumps(self.__dict__)

    def __len__ ( self ) -> int:
        return len(str(self))



class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self,channel: str = None, msg : str = "Hello World!" ):
        super().__init__("message")
        self.message = msg
        if channel: # if set
            self.channel = channel
        self.ts = int(datetime.timestamp(datetime.now()))
        #fi
    #end
    def __repr__( self ) -> str:
        return json.dumps(self.__dict__)

    def __len__ ( self ) -> int:
        return len(str(self))

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(channel,message)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        msg_bytes = bytearray(str(msg),'utf-8')
        total_len = len(msg_bytes)
        print(total_len)
        if total_len <= 65535:
            msg_bytes_and_len = len(msg_bytes).to_bytes(2, byteorder='big') + msg_bytes
            connection.sendall(msg_bytes_and_len)
        else:
            print("Message to big\n Nothing was Sent")


    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        a = connection.recv(2)
        msg_length = int.from_bytes( a, byteorder='big')
        msg = bytearray()
        while msg_length != 0:
            data = connection.recv(min(msg_length,2048))
            msg_length = msg_length - len(data)
            msg = msg + data
        #done
        msg = msg.decode("utf-8")
        try:
            j = json.loads(msg)
            if j["command"] ==  "join":
                return JoinMessage(j["channel"])
            #fi
            if j["command"] ==  "register":
                return RegisterMessage(j["user"])
            #fi
            if j["command"] ==  "message":
                if "channel" in j.keys():
                    return TextMessage(j["channel"], j["message"])
                else:
                    return TextMessage(None, j["message"])
        except ValueError as e:
            print(msg)
            raise CDProtoBadFormat(msg)
        return None


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.encode('utf-8').decode("utf-8")
