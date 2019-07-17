
#!/usr/bin/env python3

from mpi4py import MPI
import os
import helper
from memory_model import memory
import threading
from datetime import datetime
import zmq
import numpy
import json
import queue
import sys

cntrl_q = queue.Queue(maxsize=1)
resp_q = queue.Queue(maxsize=1)

class Rmonitor():
    def __init__(self, mpicomm):
        self.model_objs = []
        self.config = None
        self.osocket = ""
        self.isocket = ""
        self.lsocket = ""
        #self.cntrl_cond = threading.Condition() 
        #self.work_cond = threading.Condition() 
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
        model_strs = list(self.config.perf_models.keys())
        for mdl_str in model_strs:
            print("Loading model: ", mdl_str) 
            self.__add_model(mdl_str)

    def remove_models(self, mdl_strs):
        current_model_strs = list(self.config.perf_models.keys()) 
        for mdl in mdl_strs:
            if mdl in current_model_strs:
               model = self.config.perf_models[mdl_str] 
               self.model_objs.remove(model)
               del config.perf_models[mdl_str] 

    def add_models(self, mdl_strs):  
        current_model_strs = list(self.config.perf_models.keys()) 
        for mdl in mdl_strs:
            if mdl not in current_model_strs:
                self.__add_model(mdl)

    def __add_model(self, mdl_str):
        model = None
        if mdl_str == "memory":
            model = memory(self.config)
        else:
            return
        self.model_objs.append(model)
        self.config.perf_models[mdl_str] = model
        
    def open_connections(self):
        self.config.open_connections()

    def send_req_or_res(self, socket, req_or_res):
        if self.rank == 0 :
            socket.send_string(req_or_res)
        self.mpi_comm.Barrier()
         
    def get_update(self, model_name, timestamp, local_state, req_type):
        global_state = self.mpi_comm.gather(local_state, root=0)
        request = {}
        if self.rank == 0 : 
            request["model"] = model_name
            request["timestamp"] = timestamp
            request["msg_type"] = req_type
            request["message"] = global_state
            j_data = json.dumps(request)
        self.mpi_comm.Barrier()
        return j_data
 
    def if_send_update(self, socket):
        timestamp = datetime.now() - self.starttime
        timestamp = list(divmod(timestamp.total_seconds(), 60))   
        for mdls in self.model_objs:
            action = numpy.zeros(1) 
            g_action = numpy.zeros(1) 
            action[0] = 1 if mdls.if_urgent_update() == True else 0
            g_action[0] = 0
            self.config.mpi_comm.Reduce(action, g_action, op=MPI.SUM)
            
            if g_action[0] > 0:
                print("sending update for ", mdls.get_model_name()) 
                request = self.get_update(mdls.get_model_name(), timestamp, mdls.get_curr_state(), "req:action")
                self.send_req_or_res(socket, request)
                message = socket.recv()
            mdls.suggest_action = False
        #print("Done with updates") 
    
    def perform_iteration(self): 
        if (self.config.begin_next_step()): 
            for mdls in self.model_objs:
                mdls.update_curr_state()
                self.config.end_current_step()
            return True
        return False

 
    def worker(self):
        context = None
        socket = None
        if self.rank == 0:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            print("Connecting to socket ", self.osocket) 
            socket.connect(self.osocket)
        do_work = True

        while do_work == True:
            if self.stop_work == True:
                do_work = False
                if self.rank == 0: 
                    socket.send_string("done")
                    msg = socket.recv()
                    print("Done!!")
            else :
                if do_work == True: 
                    self.perform_iteration() 
                    self.if_send_update(socket)
                if cntrl_q.empty() == False:
                    message = cntrl_q.get(block=False)
                    self.process_request(message)
                    cntrl_q.task_done()

    def controller(self):
        l_socket = None
        l_context = None
        g_context = None
        g_socket = None
        topic = "control_msg"

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

        if_stop = False
        j_data = {}

        while if_stop == False:
           j_data = None
           message=""

           if self.rank == 0:     
               j_data = g_socket.recv()
               j_data = j_data.decode("utf-8")
               message_bytes = topic + ' ' + j_data
               l_socket.send_string(message_bytes)
           else:
               message = l_socket.recv()
               msg = message.find('{')
               j_data = message[msg:]

           request = json.loads(j_data)
           cntrl_q.put(request)
           response = resp_q.get()
           self.send_req_or_res(g_socket, response)
           if self.stop_cntrl == True:
               print("Recieved stop request")
               if_stop = True
 
    def process_request(self, request):
         if request["msg_type"] == "req:get_update":
             timestamp = datetime.now() - self.starttime
             timestamp = list(divmod(timestamp.total_seconds(), 60))   
             mdls = self.config.perf_models[request["model"]] 
             response = self.get_update(mdls.name, timestamp, mdls.get_curr_state(), "res:update")
         elif request["msg_type"] == "req:stop":
             self.stop_work = True
             self.stop_cntrl = True
             response = "OK"
         else:
             # Change model or change mapping
             response = "OK"
         resp_q.put(response)
          
if __name__ == "__main__":
    appID = 10
    mpi_comm = MPI.COMM_WORLD.Split(appID, MPI.COMM_WORLD.Get_rank()) 
    print(MPI.COMM_WORLD.Get_rank())
    sys.stdout.flush()
    r_monitor = Rmonitor(mpi_comm)
    worker_thread = threading.Thread(target=r_monitor.worker)
    worker_thread.start()
    r_monitor.controller()
    worker_thread.join()
   
   

         
