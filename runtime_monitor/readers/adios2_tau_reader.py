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
 
     def __init__(self, infile, eng, mpi_comm, blocks_to_read = [0], tau_ftype = "trace"):
         self.inputfile = infile     
         self.eng_name = eng
         self.mpi_comm = mpi_comm
         self.blocks_to_read = blocks_to_read
         self.tau_file_type = tau_ftype
         self.my_rank = MPI.COMM_WORLD.Get_rank()
         self.conn = None
         self.cstep_avail_vars = None
         self.cstep_avail_attrs = None
         self.cstep_map_vars = {}
         self.cstep = None
         self.counters = {}
         self.event_times = {}
         self.comm_events = {}
         self.is_step = False
         self.is_open = False  
         self.reset = False 
         self.current_step = 0
         self.start = {} 
         self.count = {}
        
     def open(self):
         if self.is_open == False:
             try:
                 #print("[Rank ", self.my_rank, "] :","Looking for..", self.inputfile) 
                 i = 0
                 found = 0
                 # Wait until file exists..
                 while i < 1:
                     if os.path.isfile(self.inputfile) or os.path.isdir(self.inputfile):
                         #print("[Rank ", self.my_rank, "] :","found file ", self.inputfile)
                         found = 1
                         break
                     elif os.path.isfile(self.inputfile + ".sst"):
                         #print("[Rank ", self.my_rank, "] :","found file ", self.inputfile, ".sst")
                         found = 1
                         break
                     #time.sleep(1)
                 #print("[Rank ", self.my_rank, "] :","Found ? ", found) 
                 self.conn = adios2.open(self.inputfile, "r", self.mpi_comm, self.eng_name)
                 self.is_open = True
             except Exception as ex:
                 traceback.print_exc()
                 #print("[Rank ", self.my_rank, "] :","Got an exception!!", ex)
                 self.is_open = False
         return self.is_open

     def get_reset(self):
         return self.reset 

     def close(self):
         if self.is_open == True:
             try: 
                 self.conn.close()
                 self.is_open = False
             except:
                 self.is_open = True

     def get_step_number(self):
         return self.cstep.current_step()

     def get_profile_map(self):
         self.cstep_avail_vars = self.cstep.available_variables()
         self.cstep_avail_attrs = self.cstep.available_attributes() 
         for name, info in self.cstep_avail_vars.items():
             self.cstep_map_vars[name] = name
         for name, info in self.cstep_avail_attrs.items():
             self.cstep_map_vars[name] = name

     def get_trace_map(self):
         self.cstep_avail_vars = self.cstep.available_variables()
         self.cstep_avail_attrs = self.cstep.available_attributes() 
         for name, info in self.cstep_avail_vars.items():
             if name == "counter_values":
                 for key, value in info.items():
                     if key == "Shape":
                         self.count['counters'] = value.split(',')
                         self.count['counters'] = [int(i) for i in self.count['counters']] 
                         self.start['counters'] = [0] * len(self.count['counters'])
             if name == "event_timestamps":
                 for key, value in info.items():
                     if key == "Shape":
                         self.count['timers'] = value.split(',')
                         self.count['timers'] = [int(i) for i in self.count['timers']] 
                         self.start['timers'] = [0] * len(self.count['timers'])
                
         #print("[Rank ", self.my_rank, "] :","START ",  self.start, " COUNT ", self.count)

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
         self.reset = False
         if self.is_open == False:
             if self.open() == False:
                 return False
             else:
                 self.reset = True
         try:
             if self.eng_name == "BPFile" or self.eng_name == "BP4":
                 self.cstep = next(self.conn)
             else:
                 self.cstep = next(self.conn)
             self.is_step = True
             #print("[Rank ", self.my_rank, "] :","Read step ",self.cstep.current_step(), " for stream", self.inputfile) 
             if self.tau_file_type == "trace":
                 self.get_trace_map() 
                 self.read_trace_data()
             else:
                 self.get_profile_map() 
             self.current_step = self.cstep.current_step()
         except ValueError as e:
             #print("[Rank ", self.my_rank, "] :",e)
             traceback.print_exc()
             print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             self.is_step = False
         except:
             #traceback.print_exc()
             #print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             print("[Rank ", self.my_rank, "] :","No more steps!!")
             self.is_step = False
         return self.is_step    

     def read_var(self, measure):
         var_data = {}
         if self.is_step == True: 
              if self.tau_file_type == "trace":
                  #all processess and threads 
                  is_dat, data = self.get_trace_var(measure, self.blocks_to_read, [ ])
                  if is_dat:
                      #Only return value and timestamp 
                      data = data[:,[2, 3]]
                      return True, data
              elif self.tau_file_type == "profile":
                  #all processess and threads 
                  return self.get_profile_var(measure, self.blocks_to_read )
         return False, var_data

     def read_var(self, measure, procs, threads=[]):
         var_data = {}
         if self.is_step == True: 
              if self.tau_file_type == "trace":
                  #print("[Rank ", self.my_rank, "] :","Getting measure", measure, flush = True) 
                  return self.get_trace_var(measure, procs, threads)
              elif self.tau_file_type == "profile":
                  return self.get_profile_var(measure, procs )
         return False, var_data

     def read_trace_data(self):
         if self.is_step == True:
             for b in self.blocks_to_read:
                 #print("[Rank ", self.my_rank, "] :","Reading block...", b)
                 if self.eng_name == "BPFile" or  self.eng_name == "BP4":
                     self.event_times[b] = self.cstep.read("event_timestamps", start = self.start['timers'], count = self.count['timers']) #, block_id = b)
                     self.counters[b] = self.cstep.read("counter_values", start = self.start['counters'], count = self.count['counters']) #, block_id = b)
                 else: 
                     self.event_times[b] = self.cstep.read("event_timestamps", block_id = b)
                     self.counters[b] = self.cstep.read("counter_values", block_id = b)
                 # TO DO: read events as well!!!

     """ returns true if values are read. Output data is a map of Numpy array which is indexed by 
      process number. Function call data is a 4 column data with process, call, includesive and exculsive times. Otherwise, 6 column data is returned with process, max, Mean, Min, num events and sum square """ 
     def get_profile_var(self, measure, procs):
         var_data = {}
         all_measures = self.cstep_map_vars.keys()
         res_match = [ x for x in all_measures if bool(measure in x)]   

         if len(res_match) == 0:
             return False, var_data
  
         #res_match = res_match.sort()
         #print(res_match)
         for b in procs:
             for mesr in res_match:
                 vdata = self.cstep.read( mesr, block_id = b)    
                 if vdata.ndim == 0:
                     continue
                 #print(vdata)
                 if b not in var_data.keys():
                     var_data[b] = np.column_stack((np.array([b]), vdata))
                 else:
                     var_data[b] = np.column_stack((var_data[b], vdata))
         if len(var_data) == 0:
             return False, var_data
         return True, var_data                 


     """
       returns true if data is found. Output data is a map of Numpy array which is indexed by 
       process number. If counter_values are read, numpy array will have the following columns (process, thread, value, timestamp). Else if event_timestamps are read, numpy array will have the following columns (process, thread, entry(0)/exit(1), timestamp)
     """  
     def get_trace_var(self, measure, procs, threads):
         var_data = {}
         all_measures = self.cstep_map_vars.keys()
         res_match = [ x for x in all_measures if bool(measure in x)]   
         #print("[Rank ", self.my_rank, "] :","Reading measure", measure, "matched" , self.cstep_map_vars[res_match[0]])
         if len(res_match) == 0 :
             return False, var_data

         for mesr in res_match:
             for b in procs:
                 #print("[Rank ", self.my_rank, "] :","Reading measure", mesr, "from block", b , "from ", self.inputfile) 
                 if self.cstep_map_vars[mesr][0] == "counter":
                     vdata = self.counters[b][self.counters[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 else:
                     vdata = self.event_times[b][self.event_times[b][:,TraceID.VALUE.value] == int(self.cstep_map_vars[mesr][1])]           
                 #print("Read ", vdata, flush = True)
                 vtdata = None

                 for t in threads:
                     #print("Screening thread ", t, flush = True)
                     if vtdata is None:
                         vtdata = vdata[ vdata[:,TraceID.THREAD.value] == int(t) ]
                     else:
                         vtdata = np.concatenate((vdata[vdata[:,TraceID.THREAD.value] == int(t)], vtdata ), axis=0)

                 if self.cstep_map_vars[mesr][0] == "counter":
                     if vtdata is None:
                         vtdata = vdata[:, [TraceID.PROC.value, TraceID.THREAD.value, TraceID.VALUE.value, TraceID.TIMESTAMP.value]]
                     else:
                         vtdata = vtdata[:, [TraceID.PROC.value, TraceID.THREAD.value, TraceID.VALUE.value, TraceID.TIMESTAMP.value]]
                 else:                  
                     if vtdata is None:
                         vtdata = vdata[:, [TraceID.PROC.value, TraceID.THREAD.value, TraceID.MEASURE.value, TraceID.TIMESTAMP.value]]
                     else:
                         vtdata = vtdata[:, [TraceID.PROC.value, TraceID.THREAD.value, TraceID.MEASURE.value, TraceID.TIMESTAMP.value]]
                 #print("Read ", var_data, flush = True)
                 if b not in var_data.keys():
                     var_data[b] = vtdata
                 else:
                     var_data[b] = np.concatenate((var_data[b], vtdata), axis=0)
         if len(var_data) == 0:
             return False, var_data                 
         return True, var_data              

     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.end_step()
                 self.is_step = False
             except:
                 self.is_step = False
                

