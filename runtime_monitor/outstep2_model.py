from mpi4py import MPI
import abc
import os
import glob
import re
import sys
import datetime as dt
from runtime_monitor import abstract_model

class outsteps2(abstract_model.model):
    def __init__(self, config):
        self.active_conns = None
        self.rmap = None
        self.stream_path = {}
        self.stream_config = None
        self.urgent_update = False
        self.stream_out_freq = {}
        self.stream_alert_steps = {}
        self.stream_cur_steps = {} 
        self.stream_global_steps = {} 
        self.stream_local_steps = {} 
        self.stream_ndigits = {} 
        self.stream_ext = {} 
        self.update_model_conf(config, True)  

    def update_curr_state(self):
        #print(self.active_conns) 
        for node in self.active_conns.keys():
            #print("Processing node ", node)
            sys.stdout.flush()
            for stream_nm in list(self.active_conns[node].keys()):
                next_step = self.stream_cur_steps[node][stream_nm] 
                #if self.stream_cur_steps[node][stream_nm] != 0:
                next_step += self.stream_out_freq[node][stream_nm] 
                new_stream = stream_nm.strip() + "{:0{}d}".format(next_step, self.stream_ndigits[node][stream_nm]) + self.stream_ext[node][stream_nm]
                new_stream = new_stream.strip() 
                print("Processing stream", new_stream, "stream")
                sys.stdout.flush()
                if os.path.isfile(new_stream) == True:
                    self.stream_cur_steps[node][stream_nm] += self.stream_out_freq[node][stream_nm]
                    self.stream_global_steps[node][stream_nm] += self.stream_out_freq[node][stream_nm]
                    self.stream_local_steps[node][stream_nm] += self.stream_out_freq[node][stream_nm]
                    print("found ", new_stream, " local steps ", self.stream_local_steps[node][stream_nm], " global steps ", self.stream_global_steps[node][stream_nm])
                else:
                    new_stream = stream_nm.strip() + '*' 
                    all_files = glob.glob(new_stream)
                    #print("pattern matches for ", new_stream, " are : ",  all_files)
                    if len(all_files) != 0:
                        print(all_files)    
                        latest_file = sorted(all_files)[-1].split("/")[-1] 
                        steps = int(re.search(r'\d+', latest_file).group()) 
                        print("For file ",  latest_file, " found integer ", steps) 
                        if self.stream_cur_steps[node][stream_nm] < steps:
                            self.stream_cur_steps[node][stream_nm] = steps
                            self.stream_global_steps[node][stream_nm] += self.stream_out_freq[node][stream_nm]  
                            self.stream_local_steps[node][stream_nm] = 0
                    #stream_name = stream_nm[stream.rfind('/') : -1]
                        
                if self.stream_cur_steps[node][stream_nm] >= self.stream_alert_steps[node][stream_nm]:  
                    self.urgent_update = True
        #print("done update")       
        sys.stdout.flush()

    def update_model_conf(self, config, restart=False):
        self.active_conns = config.active_reader_objs
        self.r_map = config.local_res_map
        self.stream_config = config.reader_config
        print(config.reader_config, " next ", self.stream_config)
        ini_time = dt.datetime.now()
        for node in self.active_conns.keys():
            self.stream_cur_steps[node] = {}
            self.stream_out_freq[node] = {}
            self.stream_alert_steps[node] = {}
            self.stream_global_steps[node] = {} 
            self.stream_local_steps[node] = {} 
            self.stream_ndigits[node] = {}
            self.stream_path[node] = {}
            self.stream_ext[node] = {}
            for stream in list(self.active_conns[node].keys()):
                self.stream_cur_steps[node][stream] = int(self.stream_config[node][stream][0])
                self.stream_local_steps[node][stream] = 0
                self.stream_global_steps[node][stream] = 0
                self.stream_path[node][stream] = stream[0 : stream.rfind('/')]
                if restart == True:
                    self.stream_local_steps[node][stream] = 0
                #if self.stream_cur_step[node][stream] == 0:
                #    self.stream_out_freq[node][stream] = int(self.stream_config[node][stream][1]) - 1 
                #else:
                self.stream_out_freq[node][stream] = int(self.stream_config[node][stream][1])  
                self.stream_alert_steps[node][stream] = int(self.stream_config[node][stream][2]) 
                self.stream_ndigits[node][stream] = int(self.stream_config[node][stream][3]) 
                self.stream_ext[node][stream] = self.stream_config[node][stream][4].strip() 
       
    def get_curr_state(self):
        j_data = {}
        nodes = self.active_conns.keys()
        for node in nodes:
            j_data[node] = {}
            j_data[node]['STEPS'] = {}
            j_data[node]['G_STEPS'] = 0
            streams = list(self.adios2_active_conns[node].keys())
            for stream in streams:
                j_data[node]['STEPS'][stream] = self.stream_local_steps[node][stream]
                j_data[node]['G_STEPS'] += self.stream_global_steps[node][stream]
        return j_data

    def get_model_name(self):
        return "outsteps2"

    def if_urgent_update(self):
        return self.urgent_update 
                                                                                                             
