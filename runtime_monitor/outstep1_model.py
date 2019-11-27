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
        self.stream_read_steps = {} 
        self.stream_write_steps = {} 
        self.stream_connect_steps = {} 
        self.stream_process_steps = {} 
        self.stream_expected_steptime = {} 
        self.stream_sum_steptime = {} 
        self.stream_step_var = {} 
        self.stream_last_timestep = {} 
        self.stream_n_steps = {} 
        self.stream_ext = {} 
        self.restart_steps = {} 
        self.restart = {} 
        self.update_model_conf(config, True)  
        self.name = "outsteps1"

    def update_curr_state(self):
        #print(self.active_conns)
        for node in self.active_conns.keys():
            print("Processing node ", node, "connections ", self.active_conns[node] )
            sys.stdout.flush()
            for stream in list(self.active_conns[node].keys()):
                adios_conc = self.active_conns[node][stream][0] 
                if adios_conc.get_reset() == True :
                    self.stream_sum_steptime[node][stream] = 0
                    self.stream_cur_steps[node][stream] = 0
                    self.stream_last_timestep[node][stream] = adios_conc.get_open_timestamp()
                    self.stream_n_steps[node][stream] = 0 
                    self.restart[node][stream] = True
  
                x_steps = adios_conc.read_var(self.stream_step_var[node][stream])

                if x_steps is None:
                    continue 

                if self.stream_n_steps[node][stream] == 0:
                    self.stream_sum_steptime[node][stream] = 0
                 
                x_read = adios_conc.read_var("read")
                x_write = adios_conc.read_var("write")
                x_connect = adios_conc.read_var("connect")
                x_process = adios_conc.read_var("process")
                x_total = x_read + x_write + x_connect + x_process 
                time_now = dt.datetime.now() 

                print("x_steps :: ", x_steps)


                if x_steps[0] > self.stream_cur_steps[node][stream]:
                    #cur_diff =  x_steps[0] * self.stream_expected_steptime[node][stream] 
                    if self.restart[node][stream] == True:
                        self.restart_steps[node][stream].append(int(x_steps[0]))
                        self.restart[node][stream] = False          
                    if self.stream_last_timestep[node][stream] == 0:
                        self.stream_last_timestep[node][stream] = adios_conc.get_open_timestamp()
                        self.stream_sum_steptime[node][stream] = 0
                    cur_diff = time_now - self.stream_last_timestep[node][stream] #adios_conc.get_open_timestamp() 
                    cur_diff = cur_diff.total_seconds()
                    self.stream_sum_steptime[node][stream] += x_total #cur_diff
                    self.stream_cur_steps[node][stream] = int(x_steps[0])
                    self.stream_n_steps[node][stream] += 1
                    self.stream_read_steps[node][stream] = float(x_read[0])
                    self.stream_write_steps[node][stream] = float(x_write[0])
                    self.stream_connect_steps[node][stream] = float(x_connect[0])
                    self.stream_process_steps[node][stream] = float(x_process[0])
                     
                if self.stream_n_steps[node][stream] > 10:
                    self.stream_last_timestep[node][stream] = time_now  
                    self.stream_sum_steptime[node][stream] = x_total #cur_diff
                    self.stream_n_steps[node][stream] = 1
            return         
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
            self.stream_n_steps[node] = {}
            self.restart[node] = {}
            self.restart_steps[node] = {}
            self.stream_read_steps[node] = {} 
            self.stream_write_steps[node] = {} 
            self.stream_connect_steps[node] = {} 
            self.stream_process_steps[node] = {} 
            for stream in list(self.active_conns[node].keys()):
                self.stream_cur_steps[node][stream] = 0
                self.stream_read_steps[node][stream] = 0 
                self.stream_write_steps[node][stream] = 0
                self.stream_connect_steps[node][stream] = 0
                self.stream_process_steps[node][stream] = 0 
                self.stream_sum_steptime[node][stream] = 0
                self.stream_path[node][stream] = stream[0 : stream.rfind('/')]
                self.stream_step_var[node][stream] = self.stream_config[node][stream][0].strip() 
                self.stream_expected_steptime[node][stream] = int(self.stream_config[node][stream][1].strip()) 
                self.stream_ext[node][stream] = self.stream_config[node][stream][2].strip() 
                self.stream_last_timestep[node][stream] = 0
                self.stream_n_steps[node][stream] = 0
                self.restart[node][stream] = True
                self.restart_steps[node][stream] = []
       
    def get_curr_state(self):
        j_data = {}
        nodes = self.active_conns.keys()
        time_now = dt.datetime.now() 
        for node in nodes:
            print("Outsteps1: Preparing an update for node ", node)
            j_data[node] = {}
            j_data[node]['N_STEPS'] = {}
            j_data[node]['AVG_STEP_TIME'] = {} 
            j_data[node]['RESTART_STEPS'] = {} 
            j_data[node]['LAST_STEP_TIMES'] = {} 
            streams = list(self.active_conns[node].keys())
            for stream in streams:
                str = stream.split('/')[1]
                print("Outsteps1: Preparing an update for node ", node, " stream ", str)
                j_data[node]['N_STEPS'][str] = self.stream_cur_steps[node][stream]
                j_data[node]['RESTART_STEPS'][str] = self.restart_steps[node][stream]
                j_data[node]['LAST_STEP_TIMES'][str] = [ self.stream_connect_steps[node][stream], self.stream_read_steps[node][stream], 
                                                         self.stream_process_steps[node][stream], self.stream_write_steps[node][stream] ] 
                #if self.stream_last_timestep[node][stream] == 0:
                #    cur_diff = time_now - adios_conc.get_open_timestamp() 
                #    cur_diff = cur_diff.total_seconds()
                #    self.stream_sum_steptime[node][stream] = cur_diff
                if self.stream_n_steps[node][stream] != 0 :
                    #j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream]/self.stream_cur_steps[node][stream])  
                    j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream]/self.stream_n_steps[node][stream])  
                else:
                    j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream])
            break
        return j_data

    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update 
                                                                                                             
