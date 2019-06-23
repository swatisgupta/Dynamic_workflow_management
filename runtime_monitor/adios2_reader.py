import adios2
from mpi4py import MPI
import sys
import numpy as np
import re

class adios2_conn(object):
     inputfile = ""
     eng_name = "BPFile"
     mpi_comm = MPI.COMM_SELF
     size = 1
     conn = None
     cstep_avail_vars = None
     cstep_avail_attrs = None
     cstep_map_vars = {}
     cstep = None
     data_counters = {}
     event_counters = {}
     is_step = False
     tau_file_type = "trace"     
     blocks_to_read = []
     is_open = False
 
     def __init__(self, infile, eng, mpi_comm, blocks_to_read=0, tau_ftype = "trace"):
         self.inputfile = infile     
         self.eng_name = eng
         self.mpi_comm = mpi_comm
         self.blocks_to_read = blocks_to_read
         tau_file_type = tau_ftype

     def open(self):
         if self.is_open == False:
             self.conn = adios2.open(self.inputfile, "r", self.mpi_comm, self.eng_name)
             self.is_open = True
         return self.is_open

     def get_trace_map(self):
         self.cstep_avail_vars = self.cstep.available_variables()
         self.cstep_avail_attrs = self.cstep.available_attributes() 
         for name, info in self.cstep_avail_attrs.items():
             if bool("MetaData" in name):
                 continue 
             #print("attr_name: " + name)
             for key, value in info.items():
                 if key == "Value":
                     #print("\t" + key + ": " + value)
                     value = value.strip('\"')
                     value = value.split('[')[0].strip(' ')   
                     self.cstep_map_vars[value] = name.split()
                     #print(self.cstep_map_vars[value])
             #print("\n")         
         #print(self.cstep_map_vars)    

     def advance_step(self):
         try:
             self.cstep = next(self.conn)
             self.is_step = True 
             if self.tau_file_type == "trace":
                 if self.cstep.current_step() == 0: 
                     self.get_trace_map()
                 self.read_trace_data()
         except ValueError as e:
             print(e)
             print("Unexpected error:", sys.exc_info()[0])
             self.is_step = False
         except:
             #print("Unexpected error:", sys.exc_info()[0])
             print("No more steps!!")
             self.is_step = False
         return self.is_step    
                      
     def read_var(self, measure, procs):
         var_data = {}
         if self.is_step == True: 
              if self.tau_file_type == "trace":
                  print("Getting measure", measure) 
                  return self.get_trace_var(measure, procs)
         return False, var_data

     def read_trace_data(self):
         if self.is_step == True:
             for b in self.blocks_to_read:
                 #print("Reading block...", b)
                 self.data_counters[b] = self.cstep.read("counter_values", block_id = b)
                 #self.data_timers[b] = self.cstep.read("event_timestamps", b)
         
     def get_trace_var(self, measure, procs):
         var_data = {}
         all_measures = self.cstep_map_vars.keys()
         #print(all_measures)         
         #search_str = measure + "*"
         #m_cond = re.compile(search_str)
         #res_match = list(filter(m_cond.match, all_measures))
         res_match = [ x for x in all_measures if bool(measure in x)]   

         #print(res_match)
         if len(res_match) == 0 :
             return False, var_data

         #print(res_match) 
         for mesr in res_match:
             for b in procs:
                 print("Reading block", b , "from ", self.inputfile) 
                 if self.cstep_map_vars[mesr][0] == "counter":
                     #print(self.data_counters)
                     vdata = self.data_counters[b][self.data_counters[b][:,3] == int(self.cstep_map_vars[mesr][1])]           
                 else:
                     vdata = self.data_timers[b][self.data_timers[b][:,3] == int(self.cstep_map_vars[mesr][1])]           
                 if b not in var_data.keys():
                     var_data[b] = vdata
                 else:
                     var_data[b] = np.concatenate((var_data[b], vdata), axis=0)
         return True, var_data              

     def end_step(self):
         if self.is_step == True:
             self.conn.end_step()
             self.is_step = False


