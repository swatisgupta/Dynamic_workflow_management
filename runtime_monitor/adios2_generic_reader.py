import adios2
from mpi4py import MPI
import sys
import numpy as np
import re
from enum import Enum 
import time
import os

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

     def open(self):
         if self.is_open == False:
             try:
                 i = 0
                 found = 0
                 while i < 1:
                     print("Looking for..", self.inputfile) 
                     if os.path.isfile(self.inputfile):
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

                 self.conn = adios2.open(self.inputfile, "r", self.mpi_comm, self.eng_name)
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

     def get_var_attr_map(self):
         self.cstep_avail_vars = self.cstep.available_variables()
         self.cstep_avail_attrs = self.cstep.available_attributes() 
         for name, info in self.cstep_avail_attrs.items():
             if bool("MetaData" in name):
                 continue 
             for key, value in info.items():
                 if key == "Value":
                     print("\t" + key + ": " + value)
                     value = value.strip('\"')
                     value = value.split('[')[0].strip(' ')   
                     self.cstep_map_vars[value] = name.split()
                     #print(self.cstep_map_vars[value])
             #print("\n")         
         #print(self.cstep_map_vars)    

     def advance_step(self):
         #if self.open() == False:
         #    return False
         try:
             self.cstep = next(self.conn)
             self.is_step = True 
             if self.current_step % 4 == 0: 
                self.get_var_attr_map()
             self.read_data()
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
                      
     def read_data(self):
         if self.is_step == True:
             for var in self.cstep_avail_vars:
             	 for b in self.blocks_to_read:
                     self.data_var[var][b] = self.cstep.read("counter_values", block_id = b)

     # returns data as a map of np array . Map index is process number. Numpy array has columns (thread, value, timestamp)    
     def read_var(self, measure, procs, threads=[0]):
         var_data = {}

         if self.is_step == False:
             return False, var_data
 
         all_measures = self.cstep_map_vars.keys()
         res_match = [ x for x in all_measures if bool(measure in x)]   

         if len(res_match) == 0 :
             return False, var_data

         for mesr in res_match:
             for b in procs:
                 var_data[b] = self.data_var[var][b]
         return True, var_data              


     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.end_step()
                 self.is_step = False
             except:
                 self.is_step = False
                

