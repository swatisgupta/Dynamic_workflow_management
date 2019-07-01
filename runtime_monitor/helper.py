import json
from mpi4py import MPI
import argparse
import os
from adios2_reader import adios2_conn
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

    parser.add_argument("--adios2_conn_str", help=''' Space seperated list of adios2 connection strings. For example,
                                                              this could be a BPFile name or runtime SST file ''', action="append", nargs='+', required=True )
    parser.add_argument("--adios2_conn_eng", help = ''' Space seperated list of adios2 connection engines corresponding to adios2 connection strings. 
                                                               Posible values are SST|BPFile|InSituMPI|DataMan. Engines should be in same order as adios2_c_strs.
                                                               If this option is not provided all engines would be considered BPFile by default''', action="append", nargs='+')

    parser.add_argument("--rmap_file", help = '''Json file name that defines the mappings of nodes to adios2 connection strings and ranks.
                                                    \n Example: map.txt
                                                          { 
								  "node" : [ { "name" : "n0" , 
             								       "mapping" : [ {"c_str" : "abc.bp.sst", "ranks" : ["0","2","3","4"] }, 
                           								     {"c_str" : "xyz.bp.sst", "ranks" : ["1", "2"] } 
                         								   ]
             								     } ]
							  }
                                                               ''', required="True")

    args = parser.parse_args()

    if args.adios2_conn_eng is not None:
       if len(args.adios2_conn_eng) != len(args.adios2_conn_str):
           print("--adios2_conn_eng: adios2 engines should be defined for all adios2 connection strings") 
           exit    
       for i in args.adios2_conn_eng:
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

    # creates a mapping of a compute node(don't reuire actual names - used dummy names) to adios2 connections 
    # and the writer ranks of connection on the node for each connection
    def __compute_resource_mapping(self, args):
        with open(args.rmap_file) as json_file:
            data = json.load(json_file) 
            for nodes in data['node']:
                node = nodes['name']
                self.res_map[node] = {} 
                for nmap in nodes['mapping']:
                    c_str = nmap['c_str'] 
                    if c_str in args.adios2_conn_str[0]:   
                        self.res_map[node][c_str] = []
                        self.res_map[node][c_str] = list(map(int, nmap['ranks']))  
                        if c_str not in self.rev_map.keys():     
                           self.rev_map[c_str] = []
                        self.rev_map[c_str].append(node)
                        if c_str not in self.adios2_c_awranks.keys():     
                           self.adios2_c_awranks[c_str] = []
                        self.adios2_c_awranks[c_str].extend(list(map(int, nmap['ranks'])))
                    else: 
                        print("Connection string ", map['c_str'], " was not defined through --adios2_conn_str option")
                        exit

    
    # Assigns nodes to each mpi ranks in round robin manner  
    def distribute_work(self):
        all_nodes = list(self.res_map.keys()) 
        mpi_comm = MPI.COMM_SELF

        if self.tau_one_file == True:
            mpi_comm = self.mpi_comm

        i = self.rank
        #print(all_nodes)
        #print(self.rank, len(all_nodes))
        #print(self.res_map)
        while i < len(all_nodes):
            #print("Assigned node", all_nodes[i])
            self.local_res_map[all_nodes[i]] = self.res_map[all_nodes[i]]   
            c_strs = self.res_map[all_nodes[i]]
            for c_str in c_strs.keys(): 
                if c_str in self.procs_per_cstr.keys():
                     self.procs_per_cstr[c_str].append(c_strs[c_str])
                else:
                     self.procs_per_cstr[c_str] = c_strs[c_str]

                if self.tau_one_file == False:
                    self.blocks_to_read[c_str] = [0]
                else:
                    self.blocks_to_read[c_str] = self.procs_per_cstr[c_str]
            i = i + self.nprocs

        all_nd_cstrs = list(self.local_res_map.values())
        for n_cstrs in all_nd_cstrs:  
            for c_str in list(n_cstrs.keys()): 
                c_set = self.c_sub_set[c_str]
                for c_str1 in c_set:
                    #print(self.blocks_to_read[c_str])
                    adios2_obj = adios2_conn(c_str1,  self.adios2_c_engs[c_str], mpi_comm, self.blocks_to_read[c_str], self.tau_file_type)
                    self.adios2_c_objs[c_str].append(adios2_obj)
        #print(self.adios2_c_objs)   


    def __init__(self, mpi_comm):
        self.res_map = {} #mapping of each node to adios2 connections and ranks
        self.local_res_map = {} #mapping of each node to adios2 connections and ranks
        self.rev_map = {} #mapping of each adios2 connection to nodes
        self.hc_lib = 'papi'
        self.adios2_c_objs = {}
        self.adios2_c_engs = {}
        self.adios2_c_strs = []
        self.perf_models = {} #list of models to be computed
        self.cpu_model = ""  
        self.mpi_comm = MPI.COMM_SELF  
        self.adios2_c_awranks = {}
        self.blocks_to_read = {}
        self.procs_per_cstr = {}
        self.tau_one_file = False
        self.tau_file_type = "trace"
        self.nprocs = 1
        self.rank = 0
        self.c_sub_set = {}

        args = argument_parser()
        #print(args.bind_outaddr) 
        # for two-way communication with Savanna
        self.iport = int(args.bind_inport[0])
        self.oport = int(args.bind_outport[0])
        self.oaddr = args.bind_outaddr[0]
        self.protocol = "tcp"
        self.iaddr = socket.gethostbyname(socket.gethostname())

     
        self.hc_lib = args.hc_lib.lower()
        self.cpu_model = self.__get_cpuinfo_model()
        self.mpi_comm = mpi_comm
        self.tau_file_type = args.tau_file_type.lower()
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

        #TODO :: add logic for dividing work amongst multiple processes
        self.__compute_resource_mapping(args)
        self.__init_adios2_conn(args)


    # Opens adios2 connections
    def open_connections(self):
        for concs in self.adios2_c_objs.values():
            for conc in concs:
                conc.open() 

    
    # Calls beginstep on all active adios2 connections
    def begin_next_step(self):
        ret = False 
        for concs in self.adios2_c_objs.values():
            for conc in concs:
                if conc.advance_step() == True:
                    ret =  True
        return ret
  
    # Calls endstep on all active adios2 connections
    def end_current_step(self):
        for concs in self.adios2_c_objs.values():
            for conc in concs:
                conc.end_step() 
    
    # Initialize adios2 connections, set engines and 
    # identifies the incomming streams names to connect to.
    # For instance, If tau_one_file option is not set then each writes rank 
    # opens a seperate stream.   
    def __init_adios2_conn(self, args):
        j = 0
        self.adios2_c_strs = args.adios2_conn_str[0]        
        for c_str in self.adios2_c_strs:
            self.adios2_c_engs[c_str] = "" 
            c_set = [] 
            self.adios2_c_objs[c_str] = []

            if args.adios2_conn_eng is not None : 
                self.adios2_c_engs[c_str] = args.adios2_conn_eng[0][j]
            else:
                self.adios2_c_engs[c_str] = "BPFile"

            if self.tau_one_file is False:
                mpi_comm = MPI.COMM_SELF
                for rank in self.adios2_c_awranks[c_str]:
                    c_set.append(c_str.split('.')[0] + "-" + str(rank) + c_str[(c_str.find('.')):]) 
            else:
                c_set = [c_str]
            self.c_sub_set[c_str] = c_set
            #print("C_set for c_str ", c_set) 
            j = j + 1 

        
