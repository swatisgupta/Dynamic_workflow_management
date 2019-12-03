import adios2
from mpi4py import MPI
import sys
import numpy as np
import re
from enum import Enum 
import time
import os
import datetime as dt

class adios2_generic_reader():
 
     def __init__(self, infile, eng, mpi_comm, blocks_to_read=0):
         self.inputfile = infile     
         self.eng_name = eng
         self.mpi_comm = mpi_comm
         self.blocks_to_read = blocks_to_read
         self.size = 1
         self.conn = None
         self.cstep_avail_vars = None
         self.cstep_avail_attrs = None
         self.cstep_map_vars = {}
         self.cstep = None
         self.is_step = False
         self.is_open = False  
         self.current_step = 0
         self.adios = adios2.ADIOS(mpi_comm)
         self.ioReader = self.adios.DeclareIO("reader")
         self.reset = False
         self.timestamp = None

  
     def open(self):
         if self.is_open == False:
             try:
                 i = 0
                 found = 0
                 while i < 1:
                     #print("Looking for..", self.inputfile) 
                     if os.path.isfile(self.inputfile):
                         #print("found file ", self.inputfile)
                         found = 1
                         break
                     else:
                         #print("Looking for..", self.inputfile + ".sst") 
                         if os.path.isfile(self.inputfile + ".sst"):
                             #print("found file ", self.inputfile, ".sst")
                             found = 1
                             break
                     #time.sleep(1)
                     i += 1
                 #print("Found ? ", found) 

                 if found == 0:
                    return self.is_open
                 else:
                     self.ioReader.SetEngine(self.eng_name)
                     self.conn = self.ioReader.Open(self.inputfile, adios2.Mode.Read)
                     #print("opened file ", self.inputfile, flush = True)
                     self.is_open = True
                     self.timestamp = dt.datetime.now()
             except Exception as ex:
                 print("Got an exception!!", ex)
                 self.is_open = False
         return self.is_open
     
     def get_reset(self):
         return self.reset 

     def get_open_timestamp(self):
         return self.timestamp

     def close(self):
         if self.is_open == True:
             try: 
                 self.conn.Close()
                 self.is_open = False
             except:
                 self.is_open = False

     def get_step_number(self):
         return self.current_step

     def get_var_attr_map(self):
         self.cstep_avail_vars = self.ioReader.AvailableVariables()
         self.cstep_avail_attrs = self.ioReader.AvailableAttributes() 
         #for name, info in self.cstep_avail_attrs.items():
         #    if bool("MetaData" in name):
         #        continue 
         #    for key, value in info.items():
         #        if key == "Value":
         #            print("\t" + key + ": " + value)
         #            value = value.strip('\"')
         #            value = value.split('[')[0].strip(' ')   
         #            self.cstep_map_vars[value] = name.split()
                     #print(self.cstep_map_vars[value])
             #print("\n")         
         #print(self.cstep_map_vars)    

     def advance_step(self):
         self.is_step = False 

         if self.eng_name == "BPFile" or  self.is_open == False:
             self.open()
             self.reset = True
         else:
             self.reset = False
 
         if self.is_open == False: 
             return self.is_step 

         try:
             status = self.conn.BeginStep(adios2.StepMode.Read, 2.0)
             #status = self.conn.BeginStep()
             if status == adios2.StepStatus.OK:
                 self.is_step = True 
                 if self.current_step == 0: 
                     self.get_var_attr_map()
                 self.current_step += 1
             elif status == adios2.StepStatus.EndOfStream:
                  self.close()
         except ValueError as e:
             print(e)
             print("Unexpected error:", sys.exc_info()[0])
             self.is_step = False
             self.close()
         except Exception as e:
             print("Caught an exception...", e)
             self.is_step = False
             self.close()
         return self.is_step    
                      
     def read_var(self, var_name):
         var_data = None 
         if self.is_step == True:
             var = self.ioReader.InquireVariable(var_name)
             if var is not None: #self.cstep_avail_vars:
                 count = tuple(var.Count())
                 type = var.Type()
                 #print("Var type ...", type, flush = True)
                 #print("Var count ...", count, flush = True)
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
                 else:
                     var_data = "" 
                 self.conn.Get(var, var_data)
         return var_data

     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.EndStep()
                 self.is_step = False
                 if self.eng_name == 'BPFile':
                     self.conn.Close()
                     self.is_open = False
             except Exception as e:
                 print("Caught an exception...", e)
                 self.is_step = False
                

