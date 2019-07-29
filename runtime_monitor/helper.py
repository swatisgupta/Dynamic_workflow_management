import json
from mpi4py import MPI
import argparse
import os
from runtime_monitor.adios2_reader import adios2_tr_reader
import socket

def argument_parser():

    available_adios2_engines = ['SST', 'BPFile', 'InSituMPI', 'DataMan']

    parser = argparse.ArgumentParser()

    parser.add_argument("--bind_inport", help="Sets port to which to listen for incoming requests ", nargs=1, required=True)

    parser.add_argument("--bind_outaddr", help="Sets address to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--bind_outport", help="Sets port to bind to for outgoing connections", nargs=1, required=True)

    parser.add_argument("--tau_one_file", help="Sets true if a separate tau file is written for each MPI rank", default="False", action="store_true")

    parser.add_argument("--tau_file_type", help="Specify the TAU file type. Options include trace|profile", nargs=1, default="trace")

    parser.add_argument("--hc_lib", "-hc", help= ''' Specify the library is used for collecting hardware counters. 
                                                     Posible values are : papi | likwid ''', default="papi")

    parser.add_argument("--memory", "-M", help="Enable model for measuring memory bandwidth and capacity pressure", default="False", action="store_true")

    #parser.add_argument("--mpi", "-m", help="Enable model for measuring MPI performance", default="False", action="store_true")

    #parser.add_argument("--adios2", "-a", help="Enable model for measuring ADIOS2 performance", default="False", action="store_true")

    parser.add_argument("--adios2_streams", help=''' Space seperated list of adios2 connection strings. For example,
                                                              this could be a BPFile name or runtime SST file ''', action="append", nargs='+', required=True )
    parser.add_argument("--adios2_stream_engs", help = ''' Space seperated list of adios2 connection engines corresponding to adios2 connection strings. 
                                                               Posible values are SST|BPFile|InSituMPI|DataMan. Engines should be in same order as adios2_stream_nm.
                                                               If this option is not provided all engines would be considered BPFile by default''', action="append", nargs='+')

    parser.add_argument("--rmap_file", help = '''Json file name that defines the mappings of nodes to adios2 connection strings and ranks.
                                                    \n Example: map.txt
                                                          { 
								  "node" : [ { "name" : "n0" , 
             								       "mapping" : [ {"stream_nm" : "abc.bp.sst", "ranks" : ["0","2","3","4"] }, 
                           								     {"stream_nm" : "xyz.bp.sst", "ranks" : ["1", "2"] } 
                         								   ]
             								     } ]
							  }
                                                               ''', required="True")

    args = parser.parse_args()

    if args.adios2_stream_engs is not None:
       if len(args.adios2_stream_engs[0]) != len(args.adios2_streams[0]):
           print("--adios2_stream_engs: adios2 engines should be defined for all adios2 connection strings") 
           exit    
       for i in args.adios2_stream_engs[0]:
           print("Engine under test ", i)
           if i in available_adios2_engines:
               continue
           else:
               print("Engine ", i, " is not currently used or is not supported in ADIOS2")
               exit    

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
                for nmap in nodes['mapping']:
                    stream_nm = nmap['stream_nm']
                    print("Looking for ", stream_nm, " in ADIOS2 streams : ", args.adios2_streams[0]) 
                    if stream_nm in args.adios2_streams[0]:   
                        self.global_res_map[node][stream_nm] = []
                        self.global_res_map[node][stream_nm] = list(map(int, nmap['ranks']))  
                        if stream_nm not in self.global_rev_res_map.keys():     
                           self.global_rev_res_map[stream_nm] = {}
                        if node not in self.global_rev_res_map[stream_nm].keys():     
                           self.global_rev_res_map[stream_nm][node] = []
                           self.global_rev_res_map[stream_nm][node] = list(map(int, nmap['ranks']))
                    else: 
                        print("Connection string ", map['stream_nm'], " was not defined through --adios2_streams option")
                        exit

    
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
                if asg_node not in  self.adios2_reader_procs.keys():
                     self.adios2_reader_procs[asg_node] = {}
                if stream_nm in self.adios2_reader_procs[asg_node].keys():
                     self.adios2_reader_procs[asg_node][stream_nm].append(stream_map[stream_nm])
                else:
                     self.adios2_reader_procs[asg_node][stream_nm] = stream_map[stream_nm]
                
                if asg_node not in  self.adios2_reader_blocks.keys():
                     self.adios2_reader_blocks[asg_node] = {}

                if self.tau_one_file == False:
                    self.adios2_reader_blocks[asg_node][stream_nm] = [0]
                else:
                    self.adios2_reader_blocks[asg_node][stream_nm] = self.adios2_reader_procs[asg_node][stream_nm]

                conn_streams_set = self.actual_streams_map[asg_node][stream_nm]
                for stream_nm1 in conn_streams_set:
                    #print(self.adios2_reader_blocks[stream_nm])
                    adios2_obj = adios2_tr_reader(stream_nm1,  self.adios2_stream_engs[stream_nm], mpi_comm, self.adios2_reader_blocks[asg_node][stream_nm], self.tau_file_type)
                    if asg_node not in self.adios2_active_reader_objs.keys():
                        self.adios2_active_reader_objs[asg_node] = {}
                    if stream_nm not in self.adios2_active_reader_objs[asg_node].keys():
                        self.adios2_active_reader_objs[asg_node][stream_nm] = []
                    self.adios2_active_reader_objs[asg_node][stream_nm].append(adios2_obj)
            i = i + self.nprocs
        #print(self.adios2_active_reader_objs)   


    def __init__(self, mpi_comm):
        ''' Global resource map: maps each node to adios2 connections and ranks for all nodes'''
        self.global_res_map = {} 
        ''' Local resource map: maps each node to adios2 connections and ranks for nodes assigned to this process'''
        self.local_res_map = {} 
        ''' Global reverse resource map: maps adios2 connections to nodes and ranks for all adios2 connections'''
        self.global_rev_res_map = {} 
        ''' Local map: map to get adios2 writer for any adios2_tr_readerection on each node'''
        self.writer_proc_map = {}

        self.hc_lib = 'papi'
        self.adios2_active_reader_objs = {}
        self.adios2_stream_engs = {}
        self.adios2_stream_nm = []
        self.adios2_reader_blocks = {}
        self.adios2_reader_procs = {}
        self.actual_streams_map = {}
        self.tau_one_file = False
        self.tau_file_type = "trace"

        self.perf_models = {} #list of models to be computed
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

     
        self.tau_file_type = args.tau_file_type[0].lower()
        print(args.hc_lib[0])
        self.hc_lib = args.hc_lib[0].lower()

        self.mpi_comm = mpi_comm
        self.nprocs = mpi_comm.Get_size() 
        self.rank =  mpi_comm.Get_rank()

        if args.tau_one_file == True:
            self.tau_one_file = True

        if args.memory == True:
            self.perf_models["memory"] = []         

        #if args.adios2 == True:
        #    print("Adios2 performance modelling has yet to be added \n")
        #    self.perf_models.append("adios2")     
    
        #if args.mpi == True:
        #    print("MPI performance modelling has yet to be added \n")
        #    self.perf_models.append("mpi") 

        self.__compute_resource_mapping(args)
        self.__init_adios2_streams__(args)


    # Opens all active (local) adios2 streams
    def open_connections(self):
        #print(self.adios2_active_reader_objs.items())
        for nodes in self.adios2_active_reader_objs.keys():
            for streams in self.adios2_active_reader_objs[nodes].keys():
                for conc in self.adios2_active_reader_objs[nodes][streams]:
                    conc.open() 

    
    # Calls beginstep on all active (local) adios2 streams
    def begin_next_step(self):
        ret = False 
        for nodes in self.adios2_active_reader_objs.keys():
            for streams in self.adios2_active_reader_objs[nodes].keys():
                for conc in self.adios2_active_reader_objs[nodes][streams]:
                    if conc.advance_step() == True:
                        ret =  True
        return ret
  

    # Calls endstep on all active (local) adios2 streams
    def end_current_step(self):
        for nodes in self.adios2_active_reader_objs.keys():
            for streams in self.adios2_active_reader_objs[nodes].keys():
                for conc in self.adios2_active_reader_objs[nodes][streams]:
                    conc.end_step() 
    

    # Initialize adios2 connections, set engines and 
    # identifies the incomming streams names to connect to.
    # For instance, If tau_one_file option is not set then each writes rank 
    # opens a seperate stream.   
    def __init_adios2_streams__(self, args):
        j = 0
        self.adios2_stream_nm = args.adios2_streams[0]        
        for stream_nm in self.adios2_stream_nm:
            self.adios2_stream_engs[stream_nm] = "" 
            conn_streams_set = [] 

            if args.adios2_stream_engs is not None : 
                self.adios2_stream_engs[stream_nm] = args.adios2_stream_engs[0][j]
            else:
                self.adios2_stream_engs[stream_nm] = "BPFile"

            for node in self.global_rev_res_map[stream_nm].keys():
                print("rev:", node)    
                if self.tau_one_file is False:
                    self.mpi_comm = MPI.COMM_SELF
                    for rank in self.global_rev_res_map[stream_nm][node]:
                        conn_streams_set.append(stream_nm.split('.')[0] + "-" + str(rank) + stream_nm[(stream_nm.find('.')):]) 
                else:
                    conn_streams_set = [stream_nm]
                if node not in self.actual_streams_map.keys():
                    self.actual_streams_map[node] = {}
                self.actual_streams_map[node][stream_nm] = conn_streams_set
                j = j + 1 

        
