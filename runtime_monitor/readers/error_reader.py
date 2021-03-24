import adios2
from mpi4py import MPI
import sys
import numpy as np
import re
from enum import Enum 
import time
import os
import datetime as dt

class error_reader():
 
     def __init__(self, infile, fformat):
         self.inputfile = infile     
         self.timestamp = None
         self.fileformat = fformat  
         self.filepointer = None
         self.status = "Running"
         self.error = 0 #None
         self.if_exists = False

     def open(self):
         try:
             found = 0
             if os.path.isfile(self.inputfile):
                 found = 1

             if found == 1:
                 self.if_exists = True
                 self.filepointer = open(self.inputfile, "r")
                 self.timestamp = dt.datetime.now()
         except Exception as ex:
             print("Got an exception!!", ex)
             self.if_exists = False
         return True #self.if_exists
     
     def get_reset(self):
         return self.reset 

     def set_reset(self, val):
         self.reset = val 

     def get_open_timestamp(self):
         return self.timestamp

     def close(self):
         if self.if_exists == True:
             try: 
                 self.filepointer.close()
                 self.filepointer = None
                 self.if_exists = False
             except:
                 self.if_exists = False

     def get_step_number(self):
         pass

     def advance_step(self, reopen = False):
         try:
             if reopen == True:
                self.close()

             self.open() 

             if self.if_exists == False: 
                self.status = "Running"
             else:
                self.status = "Terminated"
         except Exception as e:
             print("Caught an exception...", e)
         return True #self.if_exists    
                      
     def read_var(self, var_name):
         try:

             if self.status == "Terminated":
                 if self.fileformat == "slurm":
                    self.error = 0
                 elif  self.fileformat == "psub":
                    self.error = 0
                 else:
                    self.error = int(self.filepointer.read()) 
             else:
                 self.error = 0
         except Exception as e:
             self.error = 0
             print("Caught an exception...", e)

         return self.error

     def end_step(self):
         pass       

