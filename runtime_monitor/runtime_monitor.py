
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

class Rmonitor():
    model_objs = []
    config = None
    osocket = ""
    isocket = ""
    lsocket = ""
    cntrl_cond = threading.Condition() 
    work_cond = threading.Condition() 
    can_change = False
    can_work = True
    stop_work = False

    rank = 0
    mpi_comm = MPI.COMM_SELF
    starttime = None

    def __init__(self, mpicomm):
        
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
        rank = self.config.rank
        mpi_comm = self.config.mpi_comm
 
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

    def send_ack(self, socket, ack_type):
        if self.rank == 0 :
            socket.send_string(ack_type)
        self.mpi_comm.Barrier()
         
    def send_update(self, socket, model_name, timestamp, local_state, req_type):
        global_state = self.mpi_comm.gather(local_state, root=0)
        request = {}
        if self.rank == 0 : 
            request["model"] = model_name
            request["timestamp"] = timestamp
            request["msg_type"] = req_type
            request["message"] = global_state
            j_data = json.dumps(request)
            socket.send_string(j_data)
        self.mpi_comm.Barrier()

    def if_send_update(self, socket):
        timestamp = datetime.now() - self.starttime
        timestamp = list(divmod(timestamp.total_seconds(), 60))   
        for mdls in self.model_objs:
            action = numpy.zeros(1) 
            g_action = numpy.zeros(1) 
            action[0] = 1 if mdls.suggest_action else 0
            g_action[0] = 0
            self.config.mpi_comm.Reduce(action, g_action, op=MPI.SUM)
            if g_action[0] > 0:
                print("sending update for ", mdls.name) 
                #self.send_update(socket, mdls.name, timestamp, mdls.get_curr_state(), "req:action")
                message = socket.recv()
            mdls.suggest_action == False
        print("Done with updates") 
    
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
            with self.work_cond:
                if self.stop_work == True:
                    do_work = False
                else :
                    while not self.can_work:
                        self.work_cond.wait()
                if do_work == True: 
                    self.perform_iteration() 
                    self.if_send_update(socket)
                #self.can_work = False
                with self.cntrl_cond:
                   self.can_change = True
                   self.cntrl_cond.notify() 

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
           print(j_data)        
           if request["msg_type"] == "req:get_update":
               timestamp = datetime.now() - self.starttime
               timestamp = list(divmod(timestamp.total_seconds(), 60))   
               with self.work_cond:
                   self.can_work = False
                
               with self.cntrl_cond:
                   while not self.can_change:
                       self.cntrl_cond.wait()
                   mdls = self.config.perf_models[request["model"]] 
                   self.send_update(g_socket, mdls.name, timestamp, mdls.get_curr_state(), "req:action")
                   self.can_change = False
                   with self.work_cond:
                       self.can_work = True
                       self.work_cond.notify()

           elif request["msg_type"] == "req:stop":
               if_stop = True
               with self.work_cond:
                   self.can_work = True
                   self.stop_work = True
                   self.work_cond.notify()
               self.send_ack(g_socket, "OK")
           else:
               # Change model or change mapping
               self.send_ack(g_socket, "OK")
               continue
          
if __name__ == "__main__":
    appID = 10
    
    mpi_comm = MPI.COMM_WORLD.Split(appID, MPI.COMM_WORLD.Get_rank()) 
    r_monitor = Rmonitor(mpi_comm)

    worker_thread = threading.Thread(target=r_monitor.worker)
    worker_thread.start()
    r_monitor.controller()
    worker_thread.join()
   
   

         
