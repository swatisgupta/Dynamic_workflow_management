from mpi4py import MPI
import abc
import os
import glob
import re
import sys
import datetime as dt
from enum import Enum
from runtime_monitor import abstract_model

class Granularity(Enum):
        NTASK = 1
        TASK = 2
        NWORKFLOW = 3
        WORKFLOW = 3


class error(abstract_model.model):
    def __init__(self, config):
        self.name = "error" #config.name
        self.rmap = None
        self.active_conns = None
        self.prep_module = None 
        self.reduce_module = {}
        self.reduce_op = {}
        self.procs_per_conns = None
        self.active_path = {}
        self.active_config = None
        self.pre_process = None
        self.res = {} 
        self.error = {} 
        self.urgent_update = False
        
        self.update_model_conf(config, True)  

    def dump_curr_state(self):
        return

    def update_curr_state(self):
        for node in self.active_conns.keys():
            sys.stdout.flush()
            for active_nm in list(self.active_conns[node].keys()):
                new_active = active_nm.strip() 
                print("Processing active", new_active, "active")
                sys.stdout.flush()
                print(self.active_conns[node][active_nm])
                self.error[node][active_nm] = self.active_conns[node][active_nm][0].read_var("")

    
    def update_model_conf(self, config, restart=False):
        self.active_conns = config.active_reader_objs
        self.r_map = config.local_res_map
        self.procs_per_conns = config.reader_blocks
        self.error = {}
        """
        self.pre_process = config.pre_process
        self.reduce = config.reduce_op
      
        if self.pre_process[0] == "custom":
            self.prep_module = __import__(self.prep_module[1], fromlist=["preprocess"])

        for gran in self.reduce_op:
            if self.reduce_op[gran][0] == "custom":
                self.reduce_module[gran] = __import__(self.self.reduce_module[gran][1], fromlist=["reduce_.%s" % (gran)])
        """
        self.active_config = config.reader_config
        ini_time = dt.datetime.now()
        nodes = self.active_conns.keys()
        for node in nodes:
            self.res[node] = {}
            self.error[node] = {}
            for active_nm in list(self.active_conns[node].keys()):
                self.res[node][active_nm] = None 
                self.error[node][active_nm] = "0" 
            
 
    def get_curr_state(self):
        j_data = {}
        nodes = self.active_conns.keys()
        for node in nodes:
            #j_data[self.name] = {}
            #j_data[self.name][node] = {}
            j_data[node] = {}
            j_data[node]['TASK_STATUS'] = {}
            actives = list(self.active_conns[node].keys())
            for active in actives:
                r_str = active.split('/')[1] 
                j_data[node]['TASK_STATUS'][r_str] = self.error[node][active]
                """
                j_data[self.name][node][active] = {}
                j_data[self.name][node][active][Granularity.NTASK] = self.error[node][active]
                j_data[self.name][node][active][Granularity.TASK] = self.error[node][active]
                j_data[self.name][node][active][Granularity.NWORKFLOW] = self.error[node][active]
                j_data[self.name][node][active][Granularity.WORKFLOW] = self.error[node][active]
                """
            break
        return j_data
    

    def get_model_name(self):
        return self.name
    """
    def join_sensor(self, sensor, join_condition):
        sensor_output = sensor.get_curr_state()
        name = sensor_output.keys()[0]
        
        for node in sensor_output[name]:
            for actives in sensor_output[name][node]:
                  for granl in join_condition["granularity"]:
    """                                        

    def if_urgent_update(self):
        return self.urgent_update 
                                                                                                             
