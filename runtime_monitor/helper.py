import json
from mpi4py import MPI
import argparse
import os
import sys
from runtime_monitor.adios2_tau_reader import adios2_tau_reader
from runtime_monitor.adios2_generic_reader import adios2_generic_reader
import socket

def argument_parser():

    available_adios2_engines = ['SST', 'BPFile', 'InSituMPI', 'DataMan']

    parser = argparse.ArgumentParser()

    parser.add_argument("--bind_inport", help="Sets port to which to listen for incoming requests ", nargs=1, required=True)

    parser.add_argument("--bind_outaddr", help="Sets address to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--bind_outport", help="Sets port to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--hc_lib", help="Hardware counter library to be used for memory model. Possible values likwid | papi. Default is papi", nargs=1, default="papi") 

    parser.add_argument("--model", help=''' Enable models to compute. Possible values are : memory | outsteps1 | outsteps2. 
                                                  Model params for memory are [tau_one_file, tau_adios2_plugin_type].
                                                  Mode params for outstep1 are [steps_var, file_extention].
                                                  Model params for outstep2 are [start_step, output_frequency, alert_steps, ndigits_in_filename, file_extention].
                                              ''', nargs=1, default="outsteps2")
   
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
    #   if len(args.stream_engs[0]) != len(args.streams[0]):
    #       print("--stream_engs: adios2 engines should be defined for all adios2 connection strings") 
    #       exit    
    #   for i in args.stream_engs[0]:
    #       print("Engine under test ", i)
    #       if i in available_adios2_engines:
    #           continue
    #       else:
    #           print("Engine ", i, " is not currently used or is not supported in ADIOS2")
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

    # creates a mapping of a compute node(don't require actual names - used dummy names) to adios2 connections 
    # and the writer ranks of connection on the node for each connection
    def __compute_resource_mapping(self, args):
        with open(args.rmap_file) as json_file:
            data = json.load(json_file) 
            for nodes in data['node']:
                node = nodes['name']
                print(node)
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
        if self.perf_model == "memory":
            if int(params_list[0]) != 0 or int(params_list[0]) != 1:
                print("tau_one_file should be 0 or 1 for ", stream, ". Using defalt value 0")
                self.tau_one_file[node][stream] = 0  
            else:
                self.tau_one_file[node][stream] = int(params_list[0])
            if params_list[1] not in ["trace", "profile"] :
                print("tau_file_type should be trace or profile for ", stream, ". Using defalt value trace")
                self.tau_file_type[node][stream] = "trace" 
            else:
                self.tau_file_type[node][stream] = params_list[1]
        if self.perf_model == "outsteps2":
            if len(params_list) != 10:
                print("Insufficient model parameters for ",  stream) 
                exit
            if node not in self.reader_config.keys():
                self.reader_config[node] = {}
            self.reader_config[node][stream] = params_list 
        if self.perf_model == "outsteps1":
            if len(params_list) != 4:
                print("Insufficient model parameters for ",  stream) 
                exit
            if node not in self.reader_config.keys():
                self.reader_config[node] = {}
            self.reader_config[node][stream] = params_list 

    # Assigns nodes to each mpi ranks in round robin manner  
    def distribute_work(self):
        all_nodes = list(self.global_res_map.keys()) 
        mpi_comm = MPI.COMM_SELF
        
        #Messy to do collective operations with different runtime connections.   
        #This will require setting communicators based on assignements.    
        #if self.tau_one_file == True:
        #    mpi_comm = self.mpi_comm

        i = self.rank
        #print(all_nodes)
        #print(self.rank, len(all_nodes))
        while i < len(all_nodes):
            #print("Assigned node", all_nodes[i])
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

                if self.perf_model == "outsteps2" or (self.perf_model == "memory" and self.tau_one_file[asg_node][stream_nm] == False):
                    self.reader_blocks[asg_node][stream_nm] = [0]
                else:
                    self.reader_blocks[asg_node][stream_nm] = self.reader_procs[asg_node][stream_nm]

                conn_streams_set = self.actual_streams_map[asg_node][stream_nm]
                for stream_nm1 in conn_streams_set:
                    reader_obj = None 
                    #create  an adios2 object based on model
                    if "memory" == self.perf_model:
                        reader_obj = adios2_tau_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm], self.tau_file_type[asg_node][stream_nm])
                    elif "outsteps1" == self.perf_model:
                        reader_obj = adios2_generic_reader(stream_nm1,  self.stream_engs[asg_node][stream_nm], mpi_comm, self.reader_blocks[asg_node][stream_nm])
                    else:
                        reader_obj = stream_nm1

                    if asg_node not in self.active_reader_objs.keys():
                        self.active_reader_objs[asg_node] = {}
                    if stream_nm not in self.active_reader_objs[asg_node].keys():
                        self.active_reader_objs[asg_node][stream_nm] = []
                    self.active_reader_objs[asg_node][stream_nm].append(reader_obj)
            i = i + self.nprocs
        #print(self.active_reader_objs)   


    def __init__(self, mpi_comm):
        ''' Global resource map: maps each node to adios2 connections and ranks for all nodes'''
        self.global_res_map = {} 
        ''' Local resource map: maps each node to adios2 connections and ranks for nodes assigned to this process'''
        self.local_res_map = {} 
        ''' Global reverse resource map: maps adios2 connections to nodes and ranks for all adios2 connections'''
        self.global_rev_res_map = {} 
        #''' Local map: map to get adios2 writer for any adios2_tr_readerection on each node'''
        self.writer_proc_map = {}

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

        self.perf_model = "outsteps2" 
        self.cpu_model = self.__get_cpuinfo_model()
        print(self.cpu_model)
        self.mpi_comm = MPI.COMM_SELF  
        self.nprocs = 1
        self.rank = 0

        args = argument_parser()

        #print(args.bind_outaddr) 
        # for two-way communication with Savanna
        self.iport = int(args.bind_inport[0])
        self.oport = int(args.bind_outport[0])
        self.oaddr = args.bind_outaddr[0]
        self.protocol = "tcp"
        self.iaddr = socket.gethostbyname(socket.gethostname())

     
        self.mpi_comm = mpi_comm
        self.nprocs = mpi_comm.Get_size() 
        self.rank =  mpi_comm.Get_rank()

        print("args model", args.model)

        if args.model[0] == "memory":
            self.perf_model = "memory"
            if args.hc_lib not in ["papi", "likwid"]:
                print("Unsupported hardware counter library ", args.hc_lib, ". Possible values for hardware counter libraries are papi and likwid")
                exit          
        elif args.model[0] == "outsteps1":
            self.perf_model = "outsteps1"        
            print("Outsteps loaded") 

        self.__compute_resource_mapping(args)
        self.__init_streams__(args)


    # Opens all active (local) adios2 streams
    def open_connections(self):
        if self.perf_model == "outsteps2":
            return
        print("Model is ", self.perf_model)
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    print("Trying to open .....", conc )
                    conc.open() 
            if self.perf_model == "outsteps1":
               return

    # Close all active (local) adios2 streams
    def close_connections(self):
        if self.perf_model == "outsteps2":
            return

        #print(self.active_reader_objs.items())
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    conc.close() 
            if self.perf_model == "outsteps1":
               return

    
    # Calls beginstep on all active (local) adios2 streams
    def begin_next_step(self):
        if self.perf_model == "outsteps2":
            return True
        print("Next iteration begins..")
        sys.stdout.flush() 
        ret = False 
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    print("Reading step from..", conc.inputfile)
                    ret_tmp = conc.advance_step()
                    if ret_tmp == True:
                        ret =  True
                    print("Read step fro m..", conc.inputfile, " ... ret ", ret_tmp)
            if self.perf_model == "outsteps1":
               return ret
        return ret
  

    # Calls endstep on all active (local) adios2 streams
    def end_current_step(self):
        if self.perf_model == "outsteps2":
            return True
        for nodes in self.active_reader_objs.keys():
            for streams in self.active_reader_objs[nodes].keys():
                for conc in self.active_reader_objs[nodes][streams]:
                    conc.end_step() 
            if self.perf_model == "outsteps1":
               return
    

    # Initialize adios2 connections, set engines and 
    # identifies the incomming streams names to connect to.
    # For instance, If tau_one_file option is not set then each writes rank 
    # opens a seperate stream.   
    def __init_streams__(self, args):
        #if self.perf_model == "outsteps2":
        #    return 

        j = 0
        for node in self.stream_nm.keys():
            conn_streams_set = [] 
            self.actual_streams_map[node] = {}
            for stream_nm in self.stream_nm[node]:
                if self.perf_model == "memory" and self.tau_one_file[node][stream_nm] is False:
                    self.mpi_comm = MPI.COMM_SELF
                    for rank in self.global_res_map[node][stream_nm]:
                        str_split = stream_nm.split('.bp')
                        conn_streams_set.append(str_split[0] + "-" + str(rank) + ".bp")
                        print(str_split[0] + "-" + str(rank) + ".bp")   
                else:
                    conn_streams_set = [stream_nm]
                self.actual_streams_map[node][stream_nm] = conn_streams_set
                j = j + 1 

       
