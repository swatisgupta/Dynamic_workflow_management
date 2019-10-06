
#!/usr/bin/env python3

from mpi4py import MPI
import os
from runtime_monitor import helper
from runtime_monitor.memory_model import memory
from runtime_monitor.outstep2_model import outsteps2
from runtime_monitor.outstep1_model import outsteps1
import threading
from datetime import datetime
import zmq
import numpy
import json
from queue import Queue
import sys


class Rmonitor():
    def __init__(self, mpicomm):
        self.model_objs = []
        self.config = None
        self.osocket = ""
        self.isocket = ""
        self.lsocket = ""
        self.msg_cond = threading.Condition()
        self.msg_queue = []
        #self.can_change = False
        #self.can_work = True
        self.stop_work = False
        self.stop_cntrl = False
        self.rank = 0
        self.mpi_comm = MPI.COMM_SELF
        self.starttime = None
        
        # Can setup other things before the thread starts
        self.mpi_comm = mpicomm
        self.config = helper.configuration(mpicomm)
        self.config.distribute_work()
        self.config_models()
        self.open_connections()
        self.starttime = datetime.now()
        self.osocket = self.config.protocol + "://" + self.config.oaddr + ":" + str(self.config.oport) 
        self.isocket = self.config.protocol + "://" + self.config.iaddr + ":" + str(self.config.iport)
        self.lsocket = self.config.protocol + "://" + self.config.iaddr + ":" + str(self.config.iport + 1)
        self.rank = self.config.rank
        self.mpi_comm = self.config.mpi_comm
 
    def config_models(self):
        mdl_str = self.config.perf_model
        print("Loading model: ", mdl_str) 
        self.__add_model(mdl_str)

    def remove_model(self, mdl_str):
        current_model_str = self.config.perf_model 
        if mdl_str == current_model_str:
            self.model_objs.remove(current_model_str)
            config.perf_model = ""

    def add_model(self, mdl_str):  
        current_model_str = self.config.perf_model 
        if mdl_str != current_model_str:
            self.__add_model(mdl_str)

    def __add_model(self, mdl_str):
        model = None
        if mdl_str == "memory":
            model = memory(self.config)
        elif mdl_str == "outsteps2":
            model = outsteps2(self.config)
        elif mdl_str == "outsteps1":
            model = outsteps1(self.config)
        else:
            return
        self.model_objs.append(model)
        self.config.perf_model = mdl_str
        print("added model:", self.config.perf_model)  

    def open_connections(self):
        self.config.open_connections()

    def send_req_or_res(self, socket, req_or_res):
        if self.rank == 0 :
            socket.send_string(req_or_res)
        self.mpi_comm.Barrier()

    def get_connect_msg(self, model_name, timestamp):
        request = {}
        if self.rank == 0 :
            request["model"] = model_name
            request["socket"] = self.config.iport
            request["timestamp"] = timestamp
            request["msg_type"] = "res:connect"
            request["message"] = self.isocket
        return request
 
    def get_update(self, model_name, timestamp, local_state, req_type):
        global_state = self.mpi_comm.gather(local_state, root=0)
        request = {}
        j_data = ""
        if self.rank == 0 : 
            request["model"] = model_name
            request["socket"] = self.config.iport
            request["timestamp"] = str(timestamp)
            request["msg_type"] = req_type
            request["message"] = global_state
            j_data = json.dumps(request)
        #self.mpi_comm.Barrier()
        return j_data
 
    def if_send_update(self, socket):
        #print("Sending critical update")
        timestamp = datetime.now() - self.starttime
        timestamp = list(divmod(timestamp.total_seconds(), 60))   
        for mdls in self.model_objs:
            action = numpy.zeros(1) 
            g_action = numpy.zeros(1) 
            action[0] = 1 if mdls.if_urgent_update() == True else 0
            g_action[0] = 0
            self.config.mpi_comm.Reduce(action, g_action, op=MPI.SUM)
            
            if g_action[0] > 0:
                print("Sending update for ", mdls.get_model_name()) 
                request = self.get_update(mdls.get_model_name(), timestamp, mdls.get_curr_state(), "req:action")
                self.send_req_or_res(socket, request)
                if self.rank == 0 :
                    message = socket.recv()
                    print("Received ack ", message)
                    sys.stdout.flush() 
            mdls.suggest_action = False
        #print("Done sending important updates")
        sys.stdout.flush() 
    
    def perform_iteration(self):
        sys.stdout.flush() 
        if self.config.begin_next_step():
            print("Reading stream!!")  
            for mdls in self.model_objs:
                mdls.update_curr_state()
            self.config.end_current_step()
            return True
        else:
            return False

    def close_connections(self):
        self.config.close_connections()

    def worker(self):
        context = None
        socket = None

        if self.rank == 0:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            print("Connecting to socket ", self.osocket) 
            socket.connect(self.osocket)
            timestamp = datetime.now() - self.starttime
            timestamp = list(divmod(timestamp.total_seconds(), 60))
            mdls = self.model_objs[-1] #s[request["model"]] 
            msg = get_connect_msg(mdls.name, timestamp)
            print("Sending message to : ", self.osocket)  
            socket.send_string(msg)
            res_msg = socket.recv()
            print("Send connection info : ", msg)  

        do_work = True

        while do_work == True:
            try: 
                if self.stop_work == True:
                    do_work = False
                    self.close_connections()
                    if self.rank == 0: 
                        socket.send_string("done")
                        msg = socket.recv()
                        print("Done!!")
                        sys.stdout.flush()
                else:
                    print("Worker: Next iteration ...")
                    sys.stdout.flush()  
                    if do_work == True: 
                        self.perform_iteration()
                        sys.stdout.flush()

                    message = None
                    with self.msg_cond:
                        print("Worker: checking msg queue ..len ", len(self.msg_queue)) 
                        while len(self.msg_queue) > 0:
                            message = self.msg_queue[0]
                            self.msg_queue.remove(message)
                            print("Worker: Got a message from queue ", message) 
                    if message is not None: 
                        response = self.process_request(message)
                        if response is not None:
                            print("Worker: sending a response...", response)
                            sys.stdout.flush()
                            self.send_req_or_res(socket, response)
                            if self.rank == 0 :
                                message = socket.recv()
                                print("Received ack ", message)
                                sys.stdout.flush() 
                        else:
                            print("Worker: not sending a response...", response)
                    self.if_send_update(socket)
            except Exception as e:
                print("Worker : Got an exception ..", e)    

    def controller(self):
        l_socket = None
        l_context = None
        g_context = None
        g_socket = None
        topic = "control_msg"
        if_stop = False

        l_context = zmq.Context()
        if self.rank == 0:  
            g_context = zmq.Context()
            g_socket = g_context.socket(zmq.REP)
            g_socket.bind(self.isocket)
            print("Listening on socket ", self.isocket)
            l_socket = l_context.socket(zmq.PUB)
            l_socket.bind(self.lsocket)
            
        else:  
            l_socket = l_context.socket(zmq.SUB)
            l_socket.connect(self.lsocket)     
            l_socket.setsockopt(zmq.SUBSCRIBE, topic)

        j_data = {}

        while if_stop == False:
           try:
               j_data = None
               message=""
               print("Controller : Waiting for new message ")
               sys.stdout.flush() 
               if self.rank == 0:     
                   j_data = g_socket.recv()
                   print("Got a request from ", self.isocket, " ", j_data) 
                   j_data1 = j_data.decode("utf-8")
                   message_bytes = topic + ' ' + j_data1
                   l_socket.send_string(message_bytes)
                   print("Publishing request to ", self.lsocket, " ", j_data) 
                   sys.stdout.flush()
                
               else:
                   message = l_socket.recv()
                   print("Got a request from ", l_socket, " ", message) 
                   sys.stdout.flush() 
                   msg = message.find('{')
                   j_data = message[msg:]

               response = "OK"
               self.send_req_or_res(g_socket, response)
               print("Send the ack response to ", g_socket, " ", response) 
               sys.stdout.flush()

               js_data = json.loads(j_data)
      
               with self.msg_cond:
                   self.msg_queue.append(js_data)
 
               if self.stop_cntrl == True:
                   print("Recieved stop request")
                   if_stop = True
           except Exception as e:
               print("Contoller : Got an exception ", e)    
 

    def process_request(self, request):
         response = None
         if request["msg_type"] == "req:get_update":
             print("Processing an update request...", request)
             timestamp = datetime.now() # - self.starttime
             #timestamp = list(divmod(timestamp.total_seconds(), 60))
             print(self.model_objs)   
             mdls = self.model_objs[-1] #s[request["model"]] 
             response = self.get_update(mdls.name, timestamp, mdls.get_curr_state(), "res:update")
         elif request["msg_type"] == "req:stop":
             print("Processing an update request...", request)
             sys.stdout.flush()
             self.stop_work = True
             self.stop_cntrl = True
         print("Send response", response)
         sys.stdout.flush()
         return response   
          
   
   

         
