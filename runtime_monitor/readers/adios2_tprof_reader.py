import adios2
from mpi4py import MPI
import sys
import numpy as np
import re
from enum import Enum 
import math
import time
import os
import numpy_indexed as npi
import json
import pandas as pd
import datetime as dt

class TraceID(Enum):
    PROC = 1
    THREAD = 2
    MEASURE = 3
    VALUE = 4
    TIMESTAMP = 5

class adios2_tau_reader():
 
     def __init__(self, infile, eng, mpi_comm, blocks_to_read=0, tau_ftype = "trace"):
         self.inputfile = infile     
         self.eng = eng
         self.mpi_comm = mpi_comm
         self.blocks_to_read = blocks_to_read
         self.tau_file_type = tau_ftype
         self.size = 1
         self.conn = None
         self.cstep_avail_vars = None
         self.cstep_avail_attrs = None
         self.cstep_map_vars = {}
         self.cstep = None
         self.data_counters = {}
         self.event_counters = {}
         self.is_step = False
         self.is_open = False  
         self.current_step = 0

     def open(self):
         if self.is_open == False:
             try:
                 i = 0
                 found = 0
                 while i < 1:
                     print("Looking for..", self.inputfile) 
                     if os.path.isdir(self.inputfile):
                         print("found file ", self.inputfile)
                         found = 1
                         break
                     elif os.path.isfile(self.inputfile + ".sst"):
                         print("found file ", self.inputfile, ".sst")
                         found = 1
                         break
                     #time.sleep(1)
                     i += 1
                 print("Found ? ", found) 

                 if found == 0:
                    return self.is_open

                 self.conn = adios2.open(self.inputfile, "r", self.mpi_comm, self.eng)
                 print("File opened sucessfully!") 
                 self.is_open = True
             except Exception as ex:
                 print("Got an exception!!", ex)
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
         for name, info in self.cstep_avail_attrs.items():
             if bool("MetaData" in name):
                 continue 
             #print("attr_name: " + name)
             for key, value in info.items():
                 if key == "Value":
                     #print("\t" + key + ":" + value)
                     #value = value.strip('\"')
                     value = value.split('[')[0].strip(' ')   
                     self.cstep_map_vars[value] = name.split()
                     #print(self.cstep_map_vars[value])
             #print("\n")         
         #print(self.cstep_map_vars)    

     def advance_step(self):
         if (self.eng == "BPFile" or self.eng == "BP4") and self.open() == False:
             print("not advancing") 
             return False
         try:
             if self.eng == "BPFile" or self.eng == "BP4":
                 self.cstep = next(self.conn)
             else:
                 self.cstep = next(self.conn)
             #print("advancing...")
             self.is_step = True 
             if self.tau_file_type == "trace":
                 if self.current_step % 4 == 0: 
                     self.get_trace_map() # only reads counters for now
                 self.read_trace_data()
             self.current_step += 1 # self.cstep.current_step()
         except ValueError as e:
             print(e)
             print("Unexpected error:", sys.exc_info()[0])
             self.is_step = False

         except:
             #print("Unexpected error:", sys.exc_info()[0])
             #print("No more steps!!")
             self.is_step = False
         return self.is_step    
                      
     def read_var(self, measure, procs, threads=[0]):
         var_data = {}
         if self.is_step == True: 
              #print("Getting measure", measure) 
              if self.tau_file_type == "trace":
                  return self.get_trace_var(measure, procs, threads)
              else: 
                  return self.get_prof_data(measure, procs)
         return False, var_data

     def get_prof_data(self, variable, procs):
         var_data = {}
         if self.is_step == True:
             for b in self.blocks_to_read:
                 if b in procs:
                     #print("Reading block...", b)
                     if self.eng == "BPFile" or self.eng == "BP4":
                         var_data[b] = self.cstep.read(variable, block_id = b)
                     else:
                         var_data[b] = self.cstep.read(variable, block_id = b)
             return True, var_data 
         return False, var_data 

     def read_trace_data(self):
         if self.is_step == True:
             for b in self.blocks_to_read:
                 #print("Reading block...", b)
                 try:
                     if self.eng == "BPFile" or self.eng == "BP4":
                         self.data_counters[b] = self.cstep.read("counter_values", block_id = b)
                     else: 
                         self.data_counters[b] = self.cstep.read("counter_values", block_id = b)
                 except:
                     self.data_counters[b] = np.array([])
                 # TO DO: read events as well!!!

     # returns data as a map of np array . Map index is process number. Numpy array has columns (thread, value, timestamp)    
     def get_trace_var(self, measure, procs, threads):
         var_data = {}
         all_measures = self.cstep_map_vars.keys()
         res_match = [ x for x in all_measures if bool(measure in x)]   
         #print("Matched counter", res_match)
         if len(res_match) == 0 :
             return False, var_data

         for mesr in res_match:
             for b in procs:
                 #print("Reading block", b , "from ", self.inputfile) 
                 if self.cstep_map_vars[mesr][0] == "counter":
                     if self.data_counters[b].size == 0:
                         continue
                     vdata = self.data_counters[b][self.data_counters[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 elif self.cstep_map_vars[mesr][0] != "counter":
                     vdata = self.data_timers[b][self.data_timers[b][:,TraceID.MEASURE.value] == int(self.cstep_map_vars[mesr][1])]           
                 vtdata = vdata
                 #for t in threads:
                 #    if vtdata is None:
                 #        vtdata = vdata[vdata[:,TraceID.THREAD.value] == t]
                 #    else:
                 #        vtdata = np.concatenate((vdata[vdata[:,TraceID.THREAD.value] == t], vtdata ), axis=0)
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
                
def timestamp_to_date(unix_ts):
    ts_in_ms = [ j/1000000 for j in unix_ts]
    dateconv = np.vectorize(dt.datetime.fromtimestamp)
    date1 = dateconv(ts_in_ms)
    return date1.tolist()

if __name__ == "__main__":
   
   connections = {}
   connec_string = sys.argv[1]
   nprocs = int(sys.argv[2])
   machine = sys.argv[3]
   procpn = int(sys.argv[4])
   variable_data = {}
   variables = {}
   nnodes = math.ceil(nprocs / procpn)

   with open("measures.json") as f:
       variables = json.load(f)

   for proc in range(nprocs):
      filename = connec_string + "-" + str(proc) + ".bp"
      connections[proc] = adios2_tau_reader(filename, 'BP4', MPI.COMM_SELF, [0], "trace")
      print("opened file", filename, flush = True)

   for proc in range(nprocs):
       connections[proc].open()
   
   for var in variables: 
       variable_data[var] = {}
       for node in range(nnodes):
           variable_data[var][node] = np.array([])

   for proc in range(nprocs):
       while connections[proc].advance_step():
           for var in variables: 
               #for node in range(nnodes):
               #for proc in range(node * procpn, (node + 1) * procpn):
               varname = "\"" + var + "\"" 
               valid, var_value = connections[proc].read_var(varname, [0])
               if valid == False: 
                   continue
               if len(var_value) == 0:
                   continue
               node = math.floor(proc / procpn)
               #print("Node number ", node)
               if variable_data[var][node].size == 0:
                   #print("Reading variable ", varname,"  for node", node)    #print(variable_data[var][node]) 
                   #print("Adding", var_value)
                   variable_data[var][node] = var_value[0]
               else:
                   variable_data[var][node] = np.append(variable_data[var][node], var_value[0], axis = 0)
               #print(variable_data[var][node]) 
   final_data = {}  
   for var in variables: 
       final_data[var] = {}
       for node in range(nnodes):
           if variable_data[var][node].size != 0:                
               #variable_data[var][node] = npi.group_by(variable_data[var][node][:, 2]).sum(variable_data[var][node])
               #timestamps = [ pd.Timestamp.to_pydatetime(x) for x in df[ "Timestamp"] ]
               #df["Timestamp"] = timestamps
               #df = df.groupby("Timestamp")
               #variable_data[var][node] = df[["Timestamp", "Value"]] 
               #print(variable_data[var][node])
               variable_data[var][node] = npi.group_by(variable_data[var][node][:, 2]).sum(variable_data[var][node], 0)
               #variable_data[var][node]=np.array([variable_data[var][node][0], variable_data[var][node][1][:,1]])
               ts_col = np.transpose(variable_data[var][node][0]) 
               val_col = np.transpose(variable_data[var][node][1][:,1])
               data_tuples = {"Timestamp":ts_col, "Node_0" : val_col}
               pdf = pd.DataFrame(data_tuples)
               pdf.set_index("Timestamp")
               pdf.index = pd.to_datetime(pdf.index, unit='s')
               variable_data[var][node] = pdf.groupby(pd.Grouper(freq='1S')).sum()
               #break
       for node in range(nnodes):
           #print("Variable:",var , " Node: " , node, "\n", final_data[var])
           if len(final_data[var]) == 0:
               final_data[var] = variable_data[var][node] 
           elif len(variable_data[var][node]) != 0:
               #print("Variable:",var , " Node: " , node, "\n", final_data[var])
               node_index = "Node_" + str(node)
               final_data[var][node_index] = variable_data[var][node]["Node_0"]
               #np.insert(final_data[var], node + 1, variable_data[var][node][1,:], 0)
       filename = connec_string + ".xlsx"
       #final_data[var] = np.transpose(final_data[var])
       print(final_data[var]) 
       sheetname = var.replace(':', '')
       final_data[var].to_excel(filename, sheet_name=sheetname)

   for proc in range(nprocs):
       connections[proc].close()
