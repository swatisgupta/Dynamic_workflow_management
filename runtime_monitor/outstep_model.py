from mpi4py import MPI
import abc

class outsteps(abstract_model.model):

     def __init__(self, config):
         self._alert_steps = 10
         self.adios2_active_conns = None
         self.rmap = None
         self.blocks_to_read = None
         self._cur_steps = -1
         self.urgent_update = False
 
     def update_curr_state(self):
             

     def update_model_conf(self, config):
         self.adios2_active_conns = config.adios2_active_reader_objs
         self.r_map = config.local_res_map
         self.blocks_to_read = config.adios2_reader_blocks
         ini_time = dt.datetime.now()
        
       
     def get_curr_state(self):
         return self._curr_steps

     def get_model_name(self):
         return "outsteps"

     def if_urgent_update(self):
         return self.urgent_update 
~                                                                                                             
