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
                     else:
                         print("Looking for..", self.inputfile + ".sst") 
                         if os.path.isfile(self.inputfile + ".sst"):
                             print("found file ", self.inputfile, ".sst")
                             found = 1
                             break
                     #time.sleep(1)
                     i += 1
                 print("Found ? ", found) 

                 if found == 0:
                    return self.is_open
                 else:
                     print("opening file ", self.inputfile)
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

         if self.is_open == False: 
             return self.is_step 

         try:
             self.cstep = next(self.conn)
             self.is_step = True 
             if self.current_step % 4 == 0: 
                self.get_var_attr_map()
             self.current_step += 1 # self.cstep.current_step()
         except ValueError as e:
             print(e)
             print("Unexpected error:", sys.exc_info()[0])
             self.is_step = False
         except Exception as e:
             print("Caught an exception...", e)
             self.is_step = False
         return self.is_step    
                      
     def read_var(self, var):
         data_var = None 
         if self.is_step == True:
             if var in self.cstep_avail_vars:
                  data_var = self.cstep.read(var)
         return data_var

     def end_step(self):
         if self.is_step == True:
             try: 
                 self.conn.end_step()
                 self.is_step = False
                 if self.eng_name == 'BPFile':
                     self.conn.close()
                     self.is_open = False
             except Exception as e:
                 print("Caught an exception...", e)
                 self.is_step = False
                

