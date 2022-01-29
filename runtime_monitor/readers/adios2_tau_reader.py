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
         self.conn = None
         self.cstep_avail_vars = None
         self.cstep_avail_attrs = None
         self.cstep_map_vars = {}
         self.cstep = None
         self.counters = {}
         self.event_timers = {}
         self.event_timers = {}
         self.comm_events = {}
         self.is_step = False
         self.is_first = False
         self.is_open = False  
         self.reset = False 
         self.current_step = 0
         self.adios = adios2.ADIOS(mpi_comm)
         self.ioReader = self.adios.DeclareIO("reader")
         self.ioReader.SetEngine(self.eng_name)
         self.start = {} 
         self.count = {}
         self.type = {}
 
     def open(self):
         if self.is_open == False:
             try:
                 ##print("[Rank ", self.my_rank, "] :","Looking for..", self.inputfile) 
                 i = 0
           
                 found = 0
                 while i < 1:
                     if self.eng_name == 'SST' and os.path.isfile(self.inputfile + ".sst"):
                         #print("[Rank ", self.my_rank, "] :","found file ", self.inputfile, ".sst", flush = True)
                         found = 1
                         break
                     elif self.eng_name != 'SST' and ( os.path.isfile(self.inputfile) or os.path.isdir(self.inputfile) ):
                         #print("[Rank ", self.my_rank, "] :","found file ", self.inputfile, flush = True)
                         found = 1
                         break
                     #time.sleep(1
                 ##print("[Rank ", self.my_rank, "] :","Found ? ", found) 
                 self.conn = self.ioReader.Open(self.inputfile, adios2.Mode.Read)
                 self.is_open = True
                 self.is_first = True
             except Exception as ex:
                 traceback.print_exc()
                 #print("[Rank ", self.my_rank, "] :","Got an exception!!", ex)
                 self.is_open = False
         return self.is_open

     def get_reset(self):
         return self.reset 

     def set_reset(self, val):
         self.reset = val 

     def close(self):
         #print("Closing stream", self.inputfile , flush = True) 
         if self.is_open == True:
             try: 
                 self.conn.Close()
                 self.is_open = False
                 self.reset = True
             except:
                 traceback.print_exc()
                 self.is_open = False

     def get_step_number(self):
         return self.ioReader.CurrentStep()


     def get_trace_map(self):
         self.cstep_avail_vars = self.ioReader.AvailableVariables() 
         #self.cstep.available_variables()
         self.cstep_avail_attrs = self.ioReader.AvailableAttributes() 
         #self.cstep.available_attributes() 
         self.count['counters'] = [] 
         self.start['counters'] = [] 
         self.count['timers']  = []
         self.start['timers'] = []
         for name, info in self.cstep_avail_vars.items():
             if name == "counter_values":
                 for key, value in info.items():
                     if key == "Shape":
                         self.count['counters'] = value.split(',')
                         self.count['counters'] = [ int(i) for i in self.count['counters']] 
                         self.start['counters'] = [0] * len(self.count['counters'])
                     if key == "Type":
                         self.type['counters'] = value
             if name == "event_timestamps":
                 for key, value in info.items():
                     if key == "Shape":
                         self.count['timers'] = value.split(',')
                         self.count['timers'] = [ int(i) for i in self.count['timers']] 
                         self.start['timers'] = [0] * len(self.count['timers'])
                     if key == "Type":
                         self.type['timers'] = value
                
         ##print("[Rank ", self.my_rank, "] :","START ",  self.start, " COUNT ", self.count)

         for name, info in self.cstep_avail_attrs.items():
             if bool("MetaData" in name):
                 continue 
             ##print("[Rank ", self.my_rank, "] :","attr_name: " + name)
             for key, value in info.items():
                 if key == "Value":
                     ##print("[Rank ", self.my_rank, "] :","\t" + key + ": " + value)
                     value = value.strip('\"')
                     value = value.split('[')[0].strip(' ')   
                     self.cstep_map_vars[value] = name.split()
                     ##print("[Rank ", self.my_rank, "] :",self.cstep_map_vars[value])
             ##print("[Rank ", self.my_rank, "] :","\n")         
         ##print("[Rank ", self.my_rank, "] :",self.cstep_map_vars)    

     def advance_step(self, reopen = False):
         #if (self.eng_name == "BPFile" or self.eng_name == "BP4") and self.open() == False:
         #    self.open()

         if reopen == True and self.is_open == False:
             self.open()
        
         if self.is_open == False:
             return self.is_step
         
         if self.is_step == True:
             self.end_step()  

         try:
             status = self.conn.BeginStep(adios2.StepMode.Read, 2.0)
             if status == adios2.StepStatus.OK:
                 self.is_step = True 
                 if self.tau_file_type == "trace":
                     self.get_trace_map() 
                     self.read_trace_data()
                 self.current_step += 1
                 #self.current_step = self.cstep.current_step()
                 #self.current_step = self.cstep.current_step()
                 #self.current_step = self.cstep.current_step()
             elif status == adios2.StepStatus.EndOfStream:
                 #print("[Rank ", self.my_rank, "] : End of stream!", flush = True)
                 #self.is_step = False
                 self.end_step()
                 self.close()
                 #if self.current_step % 4 == 0: 
         except ValueError as e:
             ##print("[Rank ", self.my_rank, "] :",e)
             traceback.print_exc()
             #print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             #self.is_step = False
             #try:
             self.end_step()
             #except:
             #    self.is_open = False

         except:
             traceback.print_exc()
             #print("[Rank ", self.my_rank, "] :","Unexpected error:", sys.exc_info()[0])
             #self.is_step = False
             self.end_step()
             #self.is_open = False
             #self.is_step = False
             #self.close()
         return self.is_step    

     def read_var(self, measure):
         var_data = {}
         if self.is_step == True: 
              if self.tau_file_type == "trace":
                  is_dat, data = self.get_trace_var(measure, self.blocks_to_read, [-1])
                  if is_dat:
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
                  ##print("[Rank ", self.my_rank, "] :","Getting measure", measure, flush = True) 
                  return self.get_trace_var(measure, procs, threads)
              elif self.tau_file_type == "profile":
                  return self.get_profile_var(measure, procs ) 
         return False, var_data

     def read_trace_data(self):
         if self.is_step == True:
             for b in self.blocks_to_read:
                 ##print("[Rank ", self.my_rank, "] :","Reading block...", b)
                 if self.eng_name == "BPFile" or self.eng_name == "BP4":
                     #self.event_timers[b] = self.cstep.read("event_timestamps", start = self.start['timers'], count = self.count['timers']) #, block_id = b)
                     #self.event_timers[b] = self.read_variable("event_timestamps", start = self.start['timers'], count = self.count['timers'], type = self.type['timers']) #, block_id = b)
                     #self.event_timers[b] = self.read_variable("event_timestamps", start=[] , count = [])  #= self.start['timers'], count = self.count['timers'], type = self.type['timers']) #, block_id = b)
                     #self.counters[b] = self.read_variable("counter_values", start = self.start['counters'], count = self.count['counters'], type = self.type['counters']) #, block_id = b)
                     self.counters[b] = self.read_variable("counter_values", start = self.start['counters'], count = []) #, block_id = b)
                 else: 
                     self.event_timers[b] = self.read_variable("event_timestamps", start = self.start['timers'], count = self.count['timers'], type = self.type['timers'])
                     self.counters[b] = self.read_variable("counter_values", start = self.start['counters'], count = self.count['counters'], type = self.type['counters'])
                 # TO DO: read events as well!!!

     """ 
     returns true if values are read. Output data is a map of Numpy array which is indexed by 
     process number. Function call data is a 4 column data with process, call, includesive and exculsive `times. 
     Otherwise, 6 column data is returned with process, max, Mean, Min, num events and sum square """ 
     def get_profile_var(self, measure, procs):
         var_data = {}
         try:
             #res_match = res_match.sort()
             ##print(res_match)
             for b in procs:
                 for mesr in [measure]:

                     vdata = self.read_variable( mesr + " / Mean")    
                     if vdata.ndim == 0 or len(vdata) == 0:
                         continue
                     #print(vdata)
                     if b not in var_data.keys():
                         var_data[b] = np.column_stack(vdata)
                     else:
                         var_data[b] = np.column_stack(var_data[b], vdata)
             #print(var_data)            
             if len(var_data) == 0:
                 return False, var_data
         except Exception as e:
             print("Caught an exception while processing metric", measure, "for procs", procs, "exception", e)
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

         if len(res_match) == 0 :
             return False, var_data
         #print("[Rank ", self.my_rank, "] :","Reading measure", measure, "matched" , self.cstep_map_vars[res_match[0]], flush=True)

         for mesr in res_match:
             for b in procs:
                 if self.cstep_map_vars[mesr][0] == "counter" and self.counters[b].size != 0:
                     ##print("[Rank ", self.my_rank, "] :","Reading measure", mesr, "from block", b , "from ", self.inputfile, flush=True) 
                     vdata = self.counters[b][self.counters[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 elif self.cstep_map_vars[mesr][0] == "timer" and self.event_timers[b].size != 0:
                     ##print("[Rank ", self.my_rank, "] :","Reading measure", mesr, "from block", b , "from ", self.inputfile, flush=True) 
                     ##print(self.event_timers[b], flush = True)
                     vdata = self.event_timers[b][self.event_timers[b][:,TraceID.VALUE.value] == int(self.cstep_map_vars[mesr][1])]           
                 else:
                     continue
                 #if vdata.shape[0] == 0:
                 #    continue

                 #print("Read ", vdata, flush = True)
                 vtdata = None

                 for t in threads:
                     ##print("Screenig thread ", t, flush = True)
                     if vtdata is None:
                         vtdata = vdata[vdata[:,TraceID.THREAD.value] == t]
                     else:
                         vtdata = np.concatenate((vdata[vdata[:,TraceID.THREAD.value] == t], vtdata ), axis=0)

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
                 #if vtdata.ndim == 0:
                 #    continue

                 if b not in var_data.keys():
                     var_data[b] = vtdata
                 else:
                     var_data[b] = np.concatenate((var_data[b], vtdata), axis=0)
         if len(var_data) == 0:
             return False, var_data                 
         return True, var_data              

     def read_variable(self, var_name, start=[], count=[], type = None):
         var_data = np.array([])
         try: 
             if self.is_step == True:
                 var = self.ioReader.InquireVariable(var_name)
                 if var is not None: #self.cstep_avail_vars:
                     #print(var_name, var) 
                     if len(count) == 0:
                         count = var.Shape()
                         print(count) #[0] = shape[0] -1
                         #count = tuple(shape)
                         #count[0] -= 1 #count = [ x -1 for x in count]
                         type = var.Type()
                         if len(count) != 0:
                             var.SetSelection([start, count]) 
                     print("Var type ...", type, flush = True)
                     print("Var count ...", count, flush = True)
                     print("Var start ...", start, flush = True)
                     if type == "int32_t":
                         if len(count) == 0:
                             var_data = np.zeros((1), dtype=np.int32)
                         else:
                             var_data = np.zeros(count, dtype=np.int32)
                     elif type == "int64_t":
                         if len(count) == 0:
                             var_data = np.zeros((1), dtype=np.int64)
                         else:
                             var_data = np.zeros(count, dtype=np.int64)
                     elif type == "float":  
                         if len(count) == 0:
                             var_data = np.zeros((1), dtype=np.float32)
                         else:
                             var_data = np.zeros(count, dtype=np.float32)
                     elif type == "double":  
                         if len(count) == 0:
                             var_data = np.zeros((1), dtype=np.float64)
                         else:
                             var_data = np.zeros(count, dtype=np.float64)
                     elif type == "uint64_t":
                         if len(count) == 0:
                             var_data = np.zeros((1), dtype=np.uint64)
                         else:
                             var_data = np.zeros(count, dtype=np.uint64)
                     else:
                         var_data = ""  
                     self.conn.Get(var, var_data, adios2.Mode.Sync)
                     #print("Data ", var_data)
         except Exception as e:
             print("Unexpected error ", e, " in reading variable ", var_name)   
         return var_data



     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.EndStep()
                 self.is_step = False
                 #if self.eng_name == 'BPFile' or self.eng_name == 'BP4':
                 #    self.conn.Close()
                 #    self.is_open = False
             except Exception as e:
                 print("Caught an exception...", e)
                 self.is_step = False
                

