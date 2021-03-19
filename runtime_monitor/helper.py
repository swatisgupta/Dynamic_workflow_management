import json
from mpi4py import MPI
import argparse
import os
import sys
from runtime_monitor.readers.adios2_tau_reader import adios2_tau_reader
from runtime_monitor.readers.adios2_generic_reader import adios2_generic_reader
from runtime_monitor.readers.error_reader import error_reader
import socket
import logging
import time

LOG_FILENAME = 'rmonitor.log'
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

def argument_parser():

    available_adios2_engines = ['SST', 'BPFile', 'InSituMPI', 'DataMan']

    parser = argparse.ArgumentParser()

    parser.add_argument("--bind_inport", help="Sets port to which to listen for incoming requests ", nargs=1, required=True)

    parser.add_argument("--bind_outaddr", help="Sets address to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--bind_outport", help="Sets port to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--hc_lib", help="Hardware counter library to be used for memory model. Possible values likwid | papi. Default is papi", nargs=1, default="papi")
    parser.add_argument("--model", help=''' Enable models to compute. Possible values are : memory | pace | heartbeat. 
                                                  Model params for memory are [tau_one_file, tau_adios2_plugin_type].
                                                  Mode params for pace are [steps_var, file_extention].
                                                  Model params for hearbeat are [start_step, output_frequency, alert_steps, ndigits_in_filename, file_extention].
                                      c        ''', nargs=1, default="heartbeat")
   
    parser.add_argument("--rmap_file", help = '''Json file name that defines the mappings of nodes to adios2 connection strings and ranks.
                                                    \n Example: map.txt
                                                          { 
								  "node" : [ { "name" : "n0" , 
             								       "mapping" : [ {"stream_nm" : "abc.bp.sst", "ranks" : ["0","2","3","4"], "stream_eng" : "SST", "model_params" : [] },  
                           								     {"stream_nm" : "xyz.bp.sst", "ranks" : ["1", "2"], "stream_eng" : "SST", "model_params" : [] } 
                         								   ]
             								     } ]
							  }
                                                               ''', required="True")

    args = parser.parse_args()

    #if args.stream_engs is not None:
    #   if len(args.stream_engs[0]): != len(args.streams[0]):
    #       self.logger.debug("[Rank %d]: --stream_engs: adios2 engines should be defined for all adios2 connection strings", self.wrank): 
    #       exit    
    #   for i in args.stream_engs[0]:
    #       self.logger.debug("[Rank %d] : Engine under test %d", self.wrank, i ):
    #       if i in available_adios2_engines:
    #           continue
    #       else:
    #           self.logger.debug("[Rank %d] : Engine %d is not currently used or is not supported in ADIOS2", self.wrank, i):
    #           exit    
 
    return args


class configuration():
     
    # CPU model info to configure architecture specific settings if needed by any model 
    def __get_cpuinfo_model(self):
        stream = os.popen("lscpu")
        for line in stream.readlines():
            key_words = line.split(':')
            if key_words[0] == 'Model name':  
               return key_words[1].strip()
        return ""

    # creates a mapping of a compute node(don't require actual names - used dummy names): to adios2 connections 
    # and the writer ranks of connection on the node for each connection
    def __compute_resource_mapping(self, args):
        with open(args.rmap_file) as json_file:
            data = json.load(json_file) 
            for nodes in data['node']:
                node = nodes['name']
                self.logger.debug("[Rank %d ]: node %s", self.wrank, node)
                self.global_res_map[node] = {} 
                self.stream_nm[node] = [] 
                self.stream_engs[node] = {} 
                for nmap in nodes['mapping']:
                    stream_nm = nmap['stream_nm']
                    self.global_res_map[node][stream_nm] = []
                    self.global_res_map[node][stream_nm] = list(map(int, nmap['ranks']))  
                    self.stream_nm[node].append(stream_nm)
                    self.stream_engs[node][stream_nm] = nmap['stream_eng']
                    self.validate_model_params(node, stream_nm, nmap['model_params'])
                    if stream_nm not in self.global_rev_res_map.keys():     
                        self.global_rev_res_map[stream_nm] = {}
                    if node not in self.global_rev_res_map[stream_nm].keys():     
                        self.global_rev_res_map[stream_nm][node] = []
                        self.global_rev_res_map[stream_nm][node] = list(map(int, nmap['ranks']))

    def __update_resource_mapping(self, data):             
        for nodes in data['node']:
            node = nodes['name']
            self.logger.debug("[Rank %d ]: node %s", self.wrank, node)
            self.global_res_map[node] = {}  
            self.stream_nm[node] = []  
            self.stream_engs[node] = {}  
            for nmap in nodes['mapping']:
                stream_nm = nmap['stream_nm']
                self.global_res_map[node][stream_nm] = []
                self.global_res_map[node][stream_nm] = list(map(int, nmap['ranks']))  
                self.stream_nm[node].append(stream_nm)
                self.stream_engs[node][stream_nm] = nmap['stream_eng']
                self.validate_model_params(node, stream_nm, nmap['model_params'])
                if stream_nm not in self.global_rev_res_map.keys():    
                    self.global_rev_res_map[stream_nm] = {}
                if node not in self.global_rev_res_map[stream_nm].keys():    
                    self.global_rev_res_map[stream_nm][node] = []
                    self.global_rev_res_map[stream_nm][node] = list(map(int, nmap['ranks']))        


    def validate_model_params(self, node, stream, params_list):
        if node not in self.tau_one_file.keys():
            self.tau_one_file[node] ={} 
            self.tau_file_type[node] ={} 
        if stream not in self.tau_one_file[node].keys():
            self.tau_one_file[node][stream] ={} 
            self.tau_file_type[node][stream] ={} 

        if self.perf_model == "memory":
            if int(params_list[0].strip()) != 0 or int(params_list[0].strip()) != 1:
                self.logger.debug("[Rank %d ] : tau_one_file should be 0 or 1 for %s .Params provided are %s . Using defalt value 0", self.wrank, stream, int(params_list[0].strip()))
                self.tau_one_file[node][stream] = 0  
            else:
                self.tau_one_file[node][stream] = 1 #int(params_list[0].strip():)
            if params_list[1] not in ["trace", "profile"] :
                self.logger.debug("[Rank %s ] : tau_file_type should be trace or profile for %s. Using defalt value trace", self.wrank, stream)
                self.tau_file_type[node][stream] = "adios2" 
            else:
                self.tau_file_type[node][stream] = params_list[1]

        if self.perf_model == "heartbeat":
            if len(params_list) != 10:
                self.logger.debug("[Rank %d] : Insufficient model parameters for %s", self.wrank,  stream) 
                exit
            if node not in self.reader_config.keys():
                self.reader_config[node] = {}
            self.reader_config[node][stream] = params_list 

        if self.perf_model == "pace":
            if len(params_list) != 4:
                self.logger.debug("[Rank %d] : Insufficient model parameters for %s", self.wrank, stream) 
                exit
            if node not in self.reader_config.keys():
                self.reader_config[node] = {}
            self.reader_config[node][stream] = params_list 
 
        if self.perf_model == "error":
            if len(params_list) != 2:
                self.logger.debug("[Rank %d] : Insufficient model parameters for %s", self.wrank, stream) 
                exit
            if node not in self.reader_config.keys():
                self.reader_config[node] = {}
            self.reader_config[node][stream] = params_list 
            self.tau_file_type[node][stream] = 0 

    # Assigns nodes to each mpi ranks in round robin manner  
    def distribute_work(self):
        all_nodes = list(self.global_res_map.keys()) 
        mpi_comm = MPI.COMM_SELF
        
        #Messy to do collective operations with different runtime connections.   
        #This will require setting communicators based on assignements.    
        #if self.tau_one_file == True:
        #    mpi_comm = self.mpi_comm

        i = self.rank
        #self.logger.debug("[Rank ", self.wrank, "] :",all_nodes):
        self.logger.debug("[Rank %d] myrank %d len %d:", self.wrank, self.rank, len(all_nodes))
        while i < len(all_nodes):
            self.logger.debug("[Rank %d ] : Assigned node for i = %d node %s", self.wrank, i, all_nodes[i])
            asg_node = all_nodes[i]  
            self.local_res_map[asg_node] = self.global_res_map[asg_node]   
            stream_map = self.global_res_map[asg_node]
            for stream_nm in stream_map.keys(): 
                if asg_node not in  self.reader_procs.keys():
                     self.reader_procs[asg_node] = {}
                if stream_nm in self.reader_procs[asg_node].keys():
                     self.reader_procs[asg_node][stream_nm].append(stream_map[stream_nm])
                else:
                     self.reader_procs[asg_node][stream_nm] = stream_map[stream_nm]
                
                if asg_node not in  self.reader_blocks.keys():
                     self.reader_blocks[asg_node] = {}

                if self.perf_model == "heartbeat" or self.tau_one_file[asg_node][stream_nm] == 0:
                    self.reader_blocks[asg_node][stream_nm] = [0]
                else:
                    self.reader_blocks[asg_node][stream_nm] = self.reader_procs[asg_node][stream_nm]

                conn_streams_set = self.actual_streams_map[asg_node][stream_nm]
                self.logger.debug("[Rank %d] : Stream : %s Node %s connections: %s", self.wrank, stream_nm, asg_node, conn_streams_set) # self.active_reader_objs)   
                for stream_nm1 in conn_streams_set:
                    reader_obj = None 
                    #create  an adios2 object based on model
                    if "memory" == self.perf_model:
                        reader_obj = adios2_tau_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm], 0) #self.tau_file_type[asg_node][stream_nm])
                    if "error" == self.perf_model:
                        reader_obj = error_reader(stream_nm1, "text" ) #self.tau_file_type[asg_node][stream_nm])
                    elif "pace" == self.perf_model:
                        if  self.tau_file_type[asg_node][stream_nm] == "trace" or  self.tau_file_type[asg_node][stream_nm] == "trace":
                            reader_obj = adios2_tau_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm], self.tau_file_type[asg_node][stream_nm])
                        else:
                            reader_obj = adios2_generic_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm])
                    else:
                        reader_obj = stream_nm1

                    if asg_node not in self.active_reader_objs.keys():
                        self.active_reader_objs[asg_node] = {}
                    if stream_nm not in self.active_reader_objs[asg_node].keys():
                        self.active_reader_objs[asg_node][stream_nm] = []
                    self.active_reader_objs[asg_node][stream_nm].append(reader_obj)
            i = i + self.nprocs
        self.logger.debug("[Rank %d ] : %s", self.wrank, self.active_reader_objs)   

    # Assigns nodes to each mpi ranks in round robin manner  
    def redistribute_work(self):
        all_nodes = list(self.global_res_map.keys())
        mpi_comm = MPI.COMM_SELF

        i = self.rank
        self.logger.debug("[Rank %d] myrank %d len %d:", self.wrank, self.rank, len(all_nodes))
        while i < len(all_nodes):
            self.logger.debug("[Rank %d ] : Assigned node for i = %d node %s", self.wrank, i, all_nodes[i])
            asg_node = all_nodes[i]
            self.local_res_map[asg_node] = self.global_res_map[asg_node]
            stream_map = self.global_res_map[asg_node]
            
            for stream_nm in stream_map.keys():
                if asg_node not in  self.reader_procs.keys():
                     self.reader_procs[asg_node] = {}
                if stream_nm in self.reader_procs[asg_node].keys():
                     self.reader_procs[asg_node][stream_nm].append(stream_map[stream_nm])
                else:
                     self.reader_procs[asg_node][stream_nm] = stream_map[stream_nm]

                if asg_node not in  self.reader_blocks.keys():
                     self.reader_blocks[asg_node] = {}

                if self.perf_model == "heartbeat" or self.perf_model == "heartbeat" or self.tau_one_file[asg_node][stream_nm] == 0:
                    self.reader_blocks[asg_node][stream_nm] = [0]
                else:
                    self.reader_blocks[asg_node][stream_nm] = self.reader_procs[asg_node][stream_nm]

                conn_streams_set = self.actual_streams_map[asg_node][stream_nm]
                self.logger.debug("[Rank %d] : Stream : %s Node %s connections: %s", self.wrank, stream_nm, asg_node, conn_streams_set) # self.active_reader_objs)   

                if asg_node not in  self.active_reader_objs.keys():
                     self.active_reader_objs[asg_node] = {}

                #stream_names = []
                if stream_nm in self.active_reader_objs[asg_node].keys():
                    reader_objs = self.active_reader_objs[asg_node][stream_nm].copy()
    
                    if reader_objs == None:
                        break    

                    for robj in reader_objs:
                        sname = None
                        if "heartbeat" != self.perf_model or "error" != self.perf_model:
                            sname = robj.inputfile  #create  an adios2 object based on model
                        else:
                            sname = robj  #create  an adios2 object based on model
                        if sname not in conn_streams_set:
                            self.active_reader_objs[asg_node][stream_nm].remove(robj)
                        else:
                            conn_streams_set.remove(sname)
                    #stream_names.append(sname) 

                #conn_streams_set = [ item for item in conn_streams_set if item not in stream_names] 

                for stream_nm1 in conn_streams_set:
                    reader_obj = None

                    if "memory" == self.perf_model:
                        reader_obj = adios2_tau_reader(stream_nm1, self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm], 0) #self.tau_file_type[asg_node][stream_nm])
                    elif "pace" == self.perf_model:
                        if  self.tau_file_type[asg_node][stream_nm] == "trace" or  self.tau_file_type[asg_node][stream_nm] == "profile":
                            reader_obj = adios2_tau_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm], self.tau_file_type[asg_node][stream_nm])
                        else:
                            reader_obj = adios2_generic_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm])
                    else:
                        reader_obj = stream_nm1

                    if asg_node not in self.active_reader_objs.keys():
                        self.active_reader_objs[asg_node] = {}
                    if stream_nm not in self.active_reader_objs[asg_node].keys():
                        self.active_reader_objs[asg_node][stream_nm] = []

                    self.active_reader_objs[asg_node][stream_nm].append(reader_obj)

            streams_nm_new = stream_map.keys()
            streams_nm_org = list(self.active_reader_objs[asg_node].keys())
            streams_nm = streams_nm_org.copy()
            for stream in streams_nm:
                if stream not in streams_nm_new:
                    self.active_reader_objs[asg_node].pop(stream)      
                        
                     
            i = i + self.nprocs

        self.logger.debug("[Rank %d ] : %s", self.wrank, self.active_reader_objs)



    def distribute_work_by_app(self):
        all_streams = set( val for dict in self.global_res_map for val in dict.values()) #list(self.global_res_map.keys()) 
        mpi_comm = MPI.COMM_SELF
    
        #Messy to do collective operations with different runtime connections.   
        #This will require setting communicators based on assignements.    
        #if self.tau_one_file == True:
        #    mpi_comm = self.mpi_comm

        total_streams = len(all_streams)
        #self.logger.debug("[Rank ", self.wrank, "] :",all_nodes):
        self.logger.debug("[Rank %d]: %d %d", self.wrank, self.rank, len(all_streams))

        for i in range(total_streams):
            if self.rank != i % self.nprocs:
                continue  

            self.logger.debug("[Rank %d ] : Assigned stream for %d is i= %d or stream %s", self.wrank, self.rank, i, all_streams[i])
            asg_node = "1" 
            #self.local_res_map[asg_node] = self.global_res_map[asg_node]   
            for node in self.global_res_map.keys(): 
                stream_map = self.global_res_map[node]
                if asg_stream in stream_map.keys(): 
                    if asg_node not in  self.reader_procs.keys():
                        self.reader_procs[asg_node] = {}
                    if asg_stream in self.reader_procs[asg_node].keys():
                        self.reader_procs[asg_node][asg_stream].append(stream_map[asg_stream])
                    else:
                        self.reader_procs[asg_node][asg_stream] = stream_map[asg_stream]
    
                if asg_node not in  self.reader_blocks.keys():
                    self.reader_blocks[asg_node] = {}

                if self.perf_model == "heartbeat" or (self.perf_model == "memory" and self.tau_one_file[asg_node][asg_stream] == 0) or self.perf_model == "error": 
                    self.reader_blocks[asg_node][asg_stream] = [0] 
                else:
                    self.reader_blocks[asg_node][asg_stream] = self.reader_procs[asg_node][asg_stream]

                conn_streams_set = self.actual_streams_map[node][asg_stream]
                self.logger.debug("[Rank %d] : Stream : %s Node : %s connections:%s ", self.wrank, asg_stream, asg_node, conn_streams_set) # self.active_reader_objs)   
                for asg_stream1 in conn_streams_set:
                    reader_obj = None 
                    #create  an adios2 object based on model
                    if "memory" == self.perf_model:
                        reader_obj = adios2_tau_reader(asg_stream1,  self.stream_engs[node][asg_stream], mpi_comm, self.reader_blocks[node][asg_stream], self.tau_file_type[node][asg_stream])
                    elif "pace" == self.perf_model:
                        if  self.tau_file_type[node][asg_stream] == "trace" or  self.tau_file_type[node][asg_stream] == "profile":
                            reader_obj = adios2_tau_reader(asg_stream1,  self.stream_engs[node][asg_stream], mpi_comm, self.reader_blocks[node][asg_stream], self.tau_file_type[node][asg_stream])
                        else:
                            reader_obj = adios2_generic_reader(asg_stream1,  self.stream_engs[node][asg_stream], mpi_comm, self.reader_blocks[node][asg_stream])
                    else:
                        reader_obj = asg_stream1

                    if asg_node not in self.active_reader_objs.keys():
                        self.active_reader_objs[asg_node] = {}
                    if asg_stream not in self.active_reader_objs[asg_node].keys():
                        self.active_reader_objs[asg_node][asg_stream] = []
                    self.active_reader_objs[asg_node][asg_stream].append(reader_obj)
            i = i + self.nprocs
        self.logger.debug("[Rank %d] : %s", self.wrank, self.active_reader_objs)   

    def __init__(self, mpi_comm):
        ''' Global resource map: maps each node to adios2 connections and ranks for all nodes'''
        self.global_res_map = {} 
        ''' Local resource map: maps each node to adios2 connections and ranks for nodes assigned to this process'''
        self.local_res_map = {} 
        ''' Global reverse resource map: maps adios2 connections to nodes and ranks for all adios2 connections'''
        self.global_rev_res_map = {} 
        #''' Local map: map to get adios2 writer for any adios2_tr_readerection on each node'''
        self.writer_proc_map = {}
        self.logger = logging.getLogger('rmonitor')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(LOG_FILENAME)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.hc_lib = "papi" 
        self.active_reader_objs = {}
        self.stream_engs = {}
        self.stream_nm = {} 
        self.reader_blocks = {}
        self.reader_procs = {}
        self.reader_config= {}
        self.actual_streams_map = {}
        self.tau_one_file = {}
        self.tau_file_type = {}

        self.perf_model = "heartbeat" 
        self.cpu_model = self.__get_cpuinfo_model()
        #self.logger.debug("[Rank ", self.wrank, "] :",self.cpu_model):
        self.mpi_comm = MPI.COMM_SELF  
        self.nprocs = 1
        self.rank = 0

        args = argument_parser()
        self.mpi_comm = mpi_comm
        self.nprocs = MPI.COMM_WORLD.Get_size() 
        self.wrank = MPI.COMM_WORLD.Get_rank() 
        self.rank =  mpi_comm.Get_rank()

        #self.logger.debug("[Rank ", self.wrank, "] :",args.bind_outaddr): 
        # for two-way communication with Savanna
        self.iport = int(args.bind_inport[0])
        self.oport = int(args.bind_outport[0])
        self.oaddr = args.bind_outaddr[0]
        self.protocol = "tcp"
        self.iaddr = None
        if self.rank == 0:
            self.iaddr = socket.gethostbyname(socket.gethostname())

        self.iaddr = self.mpi_comm.bcast(self.iaddr, root=0)      

        #self.logger.debug("[Rank ", self.wrank, "] :","args model", args.model):

        if args.model[0] == "memory":
            self.perf_model = "memory"
            if args.hc_lib[0] not in ["papi", "likwid"]:
                self.logger.debug("[Rank %d] : Unsupported hardware counter library %s. Possible values for hardware counter libraries are papi and likwid", self.wrank, args.hc_lib)
                exit
            self.hc_lib = args.hc_lib[0]          
        elif args.model[0] == "pace":
            self.perf_model = "pace"        
            self.logger.debug("[Rank %d] : Pace loaded", self.wrank) 
        elif args.model[0] == "error":
            self.perf_model = "error"        
            self.logger.debug("[Rank %d] : Pace loaded", self.wrank) 

        self.__compute_resource_mapping(args)
        self.__init_streams__(args)


    # Opens all active (local): adios2 streams
    def open_connections(self):
        if self.perf_model == "heartbeat":
            return
        self.logger.debug("[Rank %d] : Model is %s", self.wrank, self.perf_model)
        #time.sleep(2)
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    self.logger.debug("[Rank %d] : Trying to open %s.....", self.wrank, conc )
                    conc.open() 
            if self.perf_model == "pace":
               return

    # Close all active (local): adios2 streams
    def close_connections(self):
        if self.perf_model == "heartbeat":
            return

        #self.logger.debug("[Rank ", self.wrank, "] :",self.active_reader_objs.items():)
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    conc.close() 
            if self.perf_model == "pace":
               return

    
    # Calls beginstep on all active (local): adios2 streams
    def begin_next_step(self, reconnect):
        if self.perf_model == "heartbeat":
            return True, False
        self.logger.debug("[Rank %d] : Next iteration begins..", self.wrank)
        sys.stdout.flush() 
        retAny = False
        ret = True
        stream_nm = None
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                stream_nm = streams
                for conc in self.active_reader_objs[nodes][streams]:
                    #self.logger.debug("[Rank ", self.wrank, "] :","Reading step from..", conc.inputfile):
                    ret_tmp = conc.advance_step(reconnect)
                    if ret_tmp == True:
                        retAny =  True
                    else: 
                        ret =  False
                    #self.logger.debug("[Rank ", self.wrank, "] :","Read step fro m..", conc.inputfile, " ... ret ", ret_tmp):
            if stream_nm != None and self.tau_one_file[nodes][stream_nm] == 0:
             #self.perf_model == "pace":
               return ret, retAny
        return ret, retAny
  

    # Calls endstep on all active (local): adios2 streams
    def end_current_step(self):
        if self.perf_model == "heartbeat" or self.perf_model == "error":
            return True
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    conc.end_step() 
            if self.perf_model == "pace":
               return
    

    # Initialize adios2 connections, set engines and 
    # identifies the incomming streams names to connect to.
    # For instance, If tau_one_file option is not set then each writes rank 
    # opens a seperate stream.   
    def __init_streams__(self, args):
        #if self.perf_model == "heartbeat":
        #    return 
        for node in self.stream_nm.keys():
            conn_streams_set = [] 
            self.actual_streams_map[node] = {}
            for stream_nm in self.stream_nm[node]:
                conn_streams_set = [] 
                if self.tau_one_file[node][stream_nm] == 0:
                    self.mpi_comm = MPI.COMM_SELF
                    for rank in self.global_res_map[node][stream_nm]:
                        str_split = stream_nm.split('.bp')
                        conn_streams_set.append(str_split[0] + "-" + str(rank) + ".bp")
                        #self.logger.debug("[Rank ", self.wrank, "] :",str_split[0] + "-" + str(rank): + ".bp")   
                else:
                    conn_streams_set = [stream_nm]
                self.actual_streams_map[node][stream_nm] = conn_streams_set
 
    def __reset_streams__(self):   
        for node in self.stream_nm.keys():
            conn_streams_set = [] 
            if node not in self.actual_streams_map.keys():
                self.actual_streams_map[node] = {}
            for stream_nm in self.stream_nm[node]:
                conn_streams_set = [] 
                if self.tau_one_file[node][stream_nm] == 0:
                    self.mpi_comm = MPI.COMM_SELF
                    for rank in self.global_res_map[node][stream_nm]:
                        str_split = stream_nm.split('.bp')
                        conn_streams_set.append(str_split[0] + "-" + str(rank) + ".bp")
                        #self.logger.debug("[Rank ", self.wrank, "] :",str_split[0] + "-" + str(rank): + ".bp")   
                else:
                    conn_streams_set = [stream_nm]
                self.actual_streams_map[node][stream_nm] = conn_streams_set

    def reset_configurations(self, rmap):
        self.__update_resource_mapping(rmap)
        self.__reset_streams__()
        self.redistribute_work()
        
