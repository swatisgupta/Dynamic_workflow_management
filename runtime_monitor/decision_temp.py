
#!/usr/bin/env python3

from mpi4py import MPI
import os
import threading
import socket as soc
import zmq
import datetime
import json
from datetime import datetime
import time 

iport = 8080
oport = 8085
starttime = None
recv_cond = threading.Condition()
stop_recv = False

current_models = []

def create_request(model_name, timestamp, req_type, msg={}):
    timestamp = list(divmod(timestamp.total_seconds(), 60)) 
    request = {}
    request["model"] = model_name
    request["timestamp"] = timestamp
    request["msg_type"] = req_type
    request["message"] = msg
    return json.dumps(request)

def receiver():
    address = soc.gethostbyname(soc.gethostname())
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket_str = "tcp://" + address + ":" + str(iport)
    socket.bind(socket_str) 
    #socket.setsockopt(zmq.SNDTIMEO, 1)
    #socket.setsockopt(zmq.RECVTIMEO, 1)
    keep_alive = True    
    while keep_alive == True:
        with recv_cond:
            if stop_recv == True:
                keep_alive = False
                continue
        message = socket.recv()
        socket.send_string("OK")
  
def sender():
    address = soc.gethostbyname(soc.gethostname())
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket_str = "tcp://" + address + ":" + str(oport)
    socket.connect(socket_str)
   
    keep_requesting = True 
    stop = False
    while keep_requesting == True:    
        request = create_request("memory", datetime.now() - starttime , "req:get_update")
        socket.send_string(request)
        message = socket.recv()
        message = message.decode("utf-8")
        print("Received message type 1", message)
        #time.sleep(1)
        if stop == True:
            request = create_request("memory", datetime.now() - starttime, "req:stop")
            socket.send_string(request)
            message = socket.recv()
            print("Received message type 2", message)
            with recv_cond:
                stop_recv = True
     
    
    
        

if __name__ == "__main__":
    appID = 10
    starttime = datetime.now()
    current_models = ["memory"]
    receiver_thread = threading.Thread(target=receiver)  
    receiver_thread.start()
    sender()
        
