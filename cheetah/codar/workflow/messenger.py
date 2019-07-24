import socket
import sys

class messengerInterface(Object):
     def __init__(self, conn_dic): 
         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.ip_address =
         self.port =  
         self.server_address = (ip_address, port)
         print(sys.stderr, "connecting to %s port %s" + server_address)
         sock.connect(server_address)
         self.connections = connections


     def __send_msg(self, connection_no, msg):
         
