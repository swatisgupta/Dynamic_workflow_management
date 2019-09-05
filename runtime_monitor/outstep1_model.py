from mpi4py import MPI
import abc
import sys
import datetime as dt
from runtime_monitor import abstract_model

class outsteps1(abstract_model.model):
    def __init__(self, config):
        self.active_conns = None
        self.rmap = None
        self.stream_path = {}
        self.stream_config = None
        self.stream_eng = None
        self.urgent_update = False
        self.stream_cur_steps = {} 
        self.stream_expected_steptime = {} 
        self.stream_sum_steptime = {} 
        self.stream_step_var = {} 
        self.stream_last_timestep = {} 
        self.stream_ext = {} 
        self.update_model_conf(config, True)  
        self.name = "outsteps1"

    def update_curr_state(self):
        #print(self.active_conns)
        time_now = dt.datetime.now() 
        for node in self.active_conns.keys():
            print("Processing node ", node, "connections ", self.active_conns[node] )
            sys.stdout.flush()
            for stream in list(self.active_conns[node].keys()):
                adios_conc = self.active_conns[node][stream][0] 
                x_steps = adios_conc.read_var(self.stream_step_var[node][stream])
                if x_steps is None:
                    continue 
                print("x_steps :: ", x_steps[0])
                if x_steps[0] > self.stream_cur_steps[node][stream]:
                    cur_diff =  self.stream_expected_steptime[node][stream] 
                    if self.stream_last_timestep[node][stream] != 0:
                        cur_diff = time_now - self.stream_last_timestep[node][stream]
                        cur_diff = cur_diff.total_seconds()
                    self.stream_sum_steptime[node][stream] += cur_diff
                    self.stream_cur_steps[node][stream] = int(x_steps[0])
                    self.stream_last_timestep[node][stream] = time_now
                     
        #sys.stdout.flush()

    def update_model_conf(self, config, restart=False):
        self.active_conns = config.active_reader_objs
        self.r_map = config.local_res_map
        self.stream_config = config.reader_config
        print(config.reader_config, " next ", self.stream_config)
        ini_time = dt.datetime.now()
        for node in self.active_conns.keys():
            self.stream_cur_steps[node] = {}
            self.stream_expected_steptime[node] = {}
            self.stream_sum_steptime[node] = {} 
            self.stream_path[node] = {}
            self.stream_ext[node] = {}
            self.stream_step_var[node] = {}
            self.stream_last_timestep[node] = {}
            for stream in list(self.active_conns[node].keys()):
                self.stream_cur_steps[node][stream] = 0
                self.stream_sum_steptime[node][stream] = 0
                self.stream_path[node][stream] = stream[0 : stream.rfind('/')]
                self.stream_step_var[node][stream] = self.stream_config[node][stream][0].strip() 
                self.stream_expected_steptime[node][stream] = int(self.stream_config[node][stream][1].strip()) 
                self.stream_ext[node][stream] = self.stream_config[node][stream][2].strip() 
                self.stream_last_timestep[node][stream] = 0
       
    def get_curr_state(self):
        j_data = {}
        nodes = self.active_conns.keys()
        for node in nodes:
            print("Outsteps1: Preparing an update for node ", node)
            j_data[node] = {}
            j_data[node]['N_STEPS'] = {}
            j_data[node]['AVG_STEP_TIME'] = {} 
            streams = list(self.active_conns[node].keys())
            for stream in streams:
                str = stream.split('/')[1]
                print("Outsteps1: Preparing an update for node ", node, " stream ", str)
                j_data[node]['N_STEPS'][str] = self.stream_cur_steps[node][stream]
                if self.stream_cur_steps[node][stream] != 0 :
                    j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream]/self.stream_cur_steps[node][stream])  
                else:
                    j_data[node]['AVG_STEP_TIME'][str] = 0
        return j_data

    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update 
                                                                                                             
