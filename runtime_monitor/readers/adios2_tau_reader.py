import adios2
from mpi4py import MPI
import sys, traceback
import numpy as np
import re
from enum import Enum 
import time
import os

class TraceID(Enum):
    PROC = 1
    THREAD = 2
    MEASURE = 3
    VALUE = 4
    TIMESTAMP = 5

class adios2_tau_reader():
 
     def __init__(self, infile, eng, mpi_comm, blocks_to_read=0, tau_ftype = "trace"):
         self.inputfile = infile     
         self.eng_name = eng
         self.mpi_comm = mpi_comm
         self.blocks_to_read = blocks_to_read
         self.tau_file_type = tau_ftype
         self.my_rank = MPI.COMM_WORLD.Get_rank()
         self.size = 1
         self.conn = None
         self.cstep_avail_vars = None
         self.cstep_avail_attrs = None
         self.cstep_map_vars = {}
         self.cstep = None
         self.data_counters = {}
         self.data_timers = {}
         self.event_counters = {}
         self.is_step = False
         self.is_open = False  
         self.current_step = 0
         self.start = None
         self.count = None
     def open(self):
         if self.is_open == False:
             try:
                 #print("[Rank ", self.my_rank, "] :","Looking for..", self.inputfile) 
                 i = 0
                 found = 0
                 while i < 1:
                     if os.path.isfile(self.inputfile) or os.path.isdir(self.inputfile):
                         print("[Rank ", self.my_rank, "] :","found file ", self.inputfile)
                         found = 1
                         break
                     elif os.path.isfile(self.inputfile + ".sst"):
                         print("[Rank ", self.my_rank, "] :","found file ", self.inputfile, ".sst")
                         found = 1
                         break
                     #time.sleep(1)
                 #print("[Rank ", self.my_rank, "] :","Found ? ", found) 
                 '''
                 if found == 0:
                    return self.is_open
                 '''
                 self.conn = adios2.open(self.inputfile, "r", self.mpi_comm, self.eng_name)
                 self.is_open = True
             except Exception as ex:
                 traceback.print_exc()
                 print("[Rank ", self.my_rank, "] :","Got an exception!!", ex)
                 self.is_open = False
         return self.is_open

     def close(self):
         if self.is_open == True:
             try: 
                 self.conn.close()
                 self.is_open = False
             except:
                 self.is_open = True

     def get_step_number(self):
         return self.cstep.current_step()

     def get_trace_map(self):
         self.cstep_avail_vars = self.cstep.available_variables()
         self.cstep_avail_attrs = self.cstep.available_attributes() 
         for name, info in self.cstep_avail_vars.items():
             if name == "counter_values":
                 for key, value in info.items():
                     if key == "Shape":
                         self.count = value.split(',')
                         self.count = [int(i) for i in self.count] 
                         self.start = [0] * len(self.count)
         print("[Rank ", self.my_rank, "] :","START ",  self.start, " COUNT ", self.count)

         for name, info in self.cstep_avail_attrs.items():
             if bool("MetaData" in name):
                 continue 
             #print("[Rank ", self.my_rank, "] :","attr_name: " + name)
             for key, value in info.items():
                 if key == "Value":
                     #print("[Rank ", self.my_rank, "] :","\t" + key + ": " + value)
                     value = value.strip('\"')
                     value = value.split('[')[0].strip(' ')   
                     self.cstep_map_vars[value] = name.split()
                     #print("[Rank ", self.my_rank, "] :",self.cstep_map_vars[value])
             #print("[Rank ", self.my_rank, "] :","\n")         
         #print("[Rank ", self.my_rank, "] :",self.cstep_map_vars)    

     def advance_step(self):
         if (self.eng_name == "BPFile" or self.eng_name == "BP4") and self.open() == False:
             return False
         try:
             if self.eng_name == "BPFile" or self.eng_name == "BP4":
                 self.cstep = next(self.conn)
             else:
                 self.cstep = next(self.conn)
             self.is_step = True
             print("[Rank ", self.my_rank, "] :","Read step ",self.cstep.current_step(), " for stream", self.inputfile) 
             if self.tau_file_type == "trace":
                 #if self.current_step % 4 == 0: 
                 self.get_trace_map() # only reads counters for now
                 self.read_trace_data()
             self.current_step = self.cstep.current_step()
         except ValueError as e:
             #print("[Rank ", self.my_rank, "] :",e)
             traceback.print_exc()
             print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             self.is_step = False
         except:
             traceback.print_exc()
             #print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             #print("[Rank ", self.my_rank, "] :","No more steps!!")
             self.is_step = False
         return self.is_step    
                      
     def read_var(self, measure, procs=[0], threads=[0]):
         var_data = {}
         if self.is_step == True: 
              if self.tau_file_type == "trace":
                  #print("[Rank ", self.my_rank, "] :","Getting measure", measure) 
                  return self.get_trace_var(measure, procs, threads)
         return False, var_data

     def read_trace_data(self):
         if self.is_step == True:
             for b in self.blocks_to_read:
                 #print("[Rank ", self.my_rank, "] :","Reading block...", b)
                 if self.eng_name == "BPFile" or  self.eng_name == "BP4":
                     self.data_counters[b] = self.cstep.read("counter_values", start = self.start, count = self.count) #, block_id = b)
                 else: 
                     self.data_counters[b] = self.cstep.read("counter_values", block_id = b)
                 # TO DO: read events as well!!!

     # returns data as a map of np array . Map index is process number. Numpy array has columns (thread, value, timestamp)    
     def get_trace_var(self, measure, procs, threads):
         var_data = {}
         all_measures = self.cstep_map_vars.keys()
         res_match = [ x for x in all_measures if bool(measure in x)]   

         if len(res_match) == 0 :
             return False, var_data

         for mesr in res_match:
             for b in procs:
                 print("[Rank ", self.my_rank, "] :","Reading measure", mesr, "from block", b , "from ", self.inputfile) 
                 if self.cstep_map_vars[mesr][0] == "counter":
                     vdata = self.data_counters[b][self.data_counters[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 else:
                     vdata = self.data_timers[b][self.data_timers[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 vtdata = None
                 for t in threads:
                     if vtdata is None:
                         vtdata = vdata[vdata[:,TraceID.THREAD.value] == t]
                     else:
                         vtdata = np.concatenate((vdata[vdata[:,TraceID.THREAD.value] == t], vtdata ), axis=0)
                 vtdata = vtdata[:, [TraceID.THREAD.value, TraceID.VALUE.value, TraceID.TIMESTAMP.value]]

                 if b not in var_data.keys():
                     var_data[b] = vtdata
                 else:
                     var_data[b] = np.concatenate((var_data[b], vtdata), axis=0)
         return True, var_data              

     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.end_step()
                 self.is_step = False
             except:
                 self.is_step = False
                

