from mpi4py import MPI
import abc
         
class model(abc.ABC):

     def __init__(self, config):
         pass

     @abc.abstractmethod 
     def update_curr_state(self):
         pass

     @abc.abstractmethod 
     def update_model_conf(self, config):   
         pass

     @abc.abstractmethod 
     def get_curr_state(self):
         pass   

     @abc.abstractmethod 
     def get_model_name(self):
         pass   

     @abc.abstractmethod 
     def dump_curr_state(self):
         pass   

     @abc.abstractmethod 
     def if_urgent_update(self):
         pass   

