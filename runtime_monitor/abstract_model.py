from mpi4py import MPI
import abc
         
class model(abc.ABC):
     suggest_action = False
     name = "abstract"

     @abc.abstractmethod 
     def __init__(self, config):
         pass 

     @abc.abstractmethod 
     def update_curr_state(self):
         pass

     @abc.abstractmethod 
     def refresh_model_conf(self, config):   
         pass

     @abc.abstractmethod 
     def get_curr_state(self):
         pass   



