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
"""CD Chat client program"""
import logging
import sys
import selectors
import fcntl
import os
import socket

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""
    _host_port = 12341
    _host = 'localhost'

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel    = selectors.DefaultSelector()
        self.name   = name #client name
        self.channel = None # last joined channel
    #end

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        #connect and register events
        self.sock.connect((self._host,self._host_port))
        self.sel.register(self.sock, selectors.EVENT_READ, self.recv_message)
        CDProto.send_msg(self.sock, CDProto.register(self.name)) # register msg

        #stdin flags and register
        # events happen on enter press
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.send_message)
    #end
    def recv_message (self, conn: socket, mask):
        data = None
        try:
            data = CDProto.recv_msg(conn)
        except CDProtoBadFormat as e:
            sys.stdout.write(" A msg was receivied which does not use proper protocol\n\
                    Closing connection to server\
                    Sorry")
            conn.close()
            self.sel.unregister(conn)
            self.sel.unregister(sys.stdin)
            sys.exit(0) # Wasn't our fault so program terminates with success

        if data:
            if hasattr(data, 'channel'):
                sys.stdout.write("\rChannel   {:>60}\n".format(data.channel))
                sys.stdout.write("\rReceived: {:>60}\r".format(data.message ))
            else:
                sys.stdout.write("\rReceived: {:>60}\r".format(data.message)  )
            #logging.debug('Received %s',data.message)
            logging.debug('Received(CDProto) %s',data)
        else:
            conn.close()
            self.sel.unregister(conn)
            self.sel.unregister(sys.stdin)
            sys.exit(0)

        sys.stdout.flush() #needed to prettify output
    #end

    #                       sys.stdin, mask
    def send_message( self, stdin,    mask):
        data =  stdin.read()
        if "/join" in data:
            # if /join is used without specifing a channel returns to default one aka #general
            self.channel = data.replace("/join","").strip()
            sys.stdout.write("Joining channel: {:^}".format(self.channel))
            join_msg = CDProto.join(self.channel)
            CDProto.send_msg(self.sock, join_msg)

            logging.debug('Sent: %s', join_msg )# store msg sent
        elif "exit" == data or "/exit" == data:
            self.sel.unregister(self.sock)
            self.sel.unregister(sys.stdin)
            self.sock.close()
            sys.exit(0)
            logging.debug('Exit')# store the fact that user issued command exit
        else:
            std_msg = CDProto.message(data.strip(), self.channel )
            CDProto.send_msg(self.sock, std_msg)
            logging.debug('Sent: %s', std_msg.message )# store msg sent

    #end

    def loop (self):
        """Loop indefinetely."""
        sys.stdout.write("\rType something and hit enter: ")
        sys.stdout.flush()
        while True:
            event = self.sel.select()
            for k, mask in event:
                callback = k.data
                callback(k.fileobj, mask)
            #done
            sys.stdout.write("\nType something and hit enter: ")
            sys.stdout.flush()
        #done
    #end
