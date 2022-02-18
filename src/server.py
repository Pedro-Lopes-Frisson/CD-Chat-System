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
"""CD Chat server program."""
import logging
import selectors
import sys
import socket

from .protocol import ( CDProto, CDProtoBadFormat , RegisterMessage, TextMessage,JoinMessage, Message)

logging.basicConfig( filename="server.log",  level=logging.DEBUG  )


class Server:
    """Chat Server process."""
    _host_port = 12341
    _host = 'localhost'
    def __init__( self ):

        self.servant = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create socket

        self.servant.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # set socketoptions to make SO Reuse address

        self.servant.bind( ( self._host, self._host_port ) ) # binds it to default port

        #self.servant.setblocking( False )                   # sets listener socket to nonblocking  this is useless  since listen is used according to docs
        self.servant.listen(10)                              # makes socket listen for connects

        self.sel = selectors.DefaultSelector(  )             # creates default selector
        self.sel.register( self.servant,  selectors.EVENT_READ,  self.accept ) # clients who connect to server socket trigger this

        self.channels = { "#general" : set(  ) } # initializes data strucutre to store channels and conns set is used so there is no duplicates
        self.usernames = { }                     # dict     usename:socket
    #end

    #                   self.servant
    def accept( self,  socket_c: socket,  mask ):
        """ Accepts clients """
        conn, addr = socket_c.accept(  )
        logging.debug( 'accepted Conn from : %s', addr )
        conn.setblocking( False )
        self.sel.register( conn,  selectors.EVENT_READ, self.parse_message ) # Registers those socket with read events
    #end

    def parse_message( self, conn,  mask ):
        """ Receives messages and takes actions """
        data = None
        try:
            data = CDProto.recv_msg(conn)
        except CDProtoBadFormat as e:
            logging.debug('Message was received but does not respect the protocol!!! %s', e.original_msg) # logs bad messages with CDProtoBadFormat property
            #logging.debug('Message was received but does not respect the protocol ')

        if data:
            if isinstance(data, RegisterMessage): # register user to a conn and adds the new socket to the #general chat (which is the default one)
                self.usernames[conn] = data.user
                self.channels["#general"].add( conn )

            if isinstance(data, JoinMessage):
                # **UNUSED** Check if this connection is currently assign to other chat channel
                #for key in self.channels.keys():               |
                    #connset = self.channels[key]               | Code to remove conn from a certain channel
                    #if conn in connset:                        |
                        #connset.remove(conn)                   |

                # Create another channel to store connections only if it doesn't exist
                if data.channel not in self.channels.keys():
                    self.channels[data.channel] = set( )

                # adds socket to said channel
                self.channels[data.channel].add( conn )

                #Done, properly sends messages to the right channel
            if isinstance(data, TextMessage):
                """ Sends message to every client of the specified or to default channel"""
                if hasattr(data, 'channel'):
                    for connection in self.channels[data.channel]:
                        # makes sure that messages aren't sent to the sender as well
                        if not conn == connection:
                            CDProto.send_msg(connection,data)

                else:  # there is no  channel specified
                    for connection in self.channels["#general"]:
                        # makes sure that messages aren't sent to the sender as well
                        if not conn == connection:
                            CDProto.send_msg(connection,data)

            logging.debug('Received bites %d from %s \t %s',len(data), conn.getpeername(),data) # logs message

        else: # data was None Socket was closed or bad format if there was a bad format then it will show in the log file
            # remove conn from the associated channel
            for channel in self.channels.keys():
                if conn in self.channels[channel]:
                    logging.debug('Nothing was received from %s currently associated with channel : %s with the username : %s', conn.getpeername(),channel, self.usernames[conn])
                    self.channels[channel].remove(conn)
            self.sel.unregister(conn)
            conn.close()

    #end
    def close_server(self):
        """Closes all connection and is own socket"""
        logging.debug('Closing Server')
        for channel in self.channels.keys():
            conns = self.channels[channel]
            for c in conns:
                logging.debug('Closing : %s : %s',channel,c)
                self.sel.unregister(c)
                c.close()
            #done
        #done

        self.sel.unregister(self.servant)
        self.servant.close()              # might not free socket immediatly see docs
        logging.debug('Server Closed')

    def loop( self ):
        """Loop indefinetely."""
        logging.debug('EVENT s')
        while True:
            event = self.sel.select()
            logging.debug('EVENT %s', str(event))
            for k,  mask in event:
                callback = k.data # function passed as argument when registering a socket (third one)
                callback( k.fileobj, mask ) # calls function
            #done
        #done
    #end
