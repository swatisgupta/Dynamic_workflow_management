from mpi4py import MPI
import abc
import sys
import numpy as np
import datetime as dt
from runtime_monitor import abstract_model

class pace(abstract_model.model):
    def __init__(self, config):
        self.active_conns = None
        self.procs_per_conns = None
        self.rmap = None
        self.stream_path = {}
        self.stream_config = None
        self.stream_eng = None
        self.urgent_update = False
        self.stream_cur_steps = {} 
        self.stream_read_steps = {} 
        self.read_values = {} 
        self.stream_write_steps = {} 
        self.stream_connect_steps = {} 
        self.stream_process_steps = {} 
        self.stream_expected_steptime = {} 
        self.stream_sum_steptime = {} 
        self.stream_step_var = {} 
        self.stream_n_steps = {} 
        self.stream_ext = {} 
        self.restart_steps = {} 
        self.restart = {} 
        self.frequency="S"
        self.update_model_conf(config, True)  
        self.name = "pace"

    def dump_curr_state(self):
        return

    def __timestamp_to_date(self, unix_ts):
        ts_in_ms = [ j/1000000 for j in unix_ts]
        dateconv = np.vectorize(dt.datetime.fromtimestamp)
        date1 = dateconv(ts_in_ms)
        return date1

    def __group_by_frequency(self, narray, by_last=0): #Replace S with U for microsecond 
        #print("[Rank ", self.my_rank, "] :",narray)  
        narray_v = narray[:,0] # get the value
        nlist_k = narray[:,1].tolist() #get the timestamp
        nlist_k = self.__timestamp_to_date(nlist_k)

        pdf = pd.DataFrame(data=narray_v, index=nlist_k, columns=["value"])
        #print("[Rank ", self.my_rank, "] :",pdf)
        if by_last == 0:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).sum()
        elif by_last == 1:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).last()
        else:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).max()
        #pdf = pdf["value"].fillna(method='ffill')
        pdf = pdf["value"].dropna() #method='ffill')
        #print("[Rank ", self.my_rank, "] :",pdf)  
        return pdf #.to_dict()

    def __compute_step_times(self, values):
        if len(values) < 2:
            return values
        print(values[:,2], flush=True)
        values = values[:,[2,3]]
        entry_vals = values[np.where(values[:,0] == 0)] #, values[:,3])
        print("ENTRY ", entry_vals)
        exit_vals = values[np.where(values[:,0] == 1)] #, values[:,3]) 
        print("EXIT" , exit_vals)
        exit_vals = self.__timestamp_to_date(exit_vals[:,1])
        entry_vals = self.__timestamp_to_date(entry_vals[0:exit_vals.shape[0],1]) 
        
        vals = exit_vals - entry_vals
        to_sec = lambda t: t.total_seconds()
        vals = np.array([to_sec(x) for x in vals])
        return vals

    def __compute_max_set(self, values):
        vals = np.array([])
        if len(values) == 0:
            return vals
        nvals = len(values) 
        for i in range(nvals):
            if vals.size == 0:
                vals = values[i]
            vals = np.maximum(vals, values[i]) 
        print("Inside compute", vals)   
        return vals
 
    def update_curr_state(self):
        #print(self.active_conns)
        step_times = {}
        for node in self.active_conns.keys():
            print("Processing node ", node, "connections ", self.active_conns[node] )
            step_times[node] = {}
            sys.stdout.flush()
            for stream in list(self.active_conns[node].keys()):
                x_conn_var = {}
                x_step = self.stream_n_steps[node][stream]
                i = 0
                n_steps_min = 0
                for adios_conc in self.active_conns[node][stream]: 
                    if adios_conc.get_reset() == True :
                        self.stream_sum_steptime[node][stream] = 0
                        self.stream_cur_steps[node][stream] = 0
                        self.stream_n_steps[node][stream] = 0 
                        self.restart[node][stream] = True


                    for proc in self.procs_per_conns[node][stream]:
                        id = i + proc
                        isvalid, conn_var = adios_conc.read_var(self.stream_step_var[node][stream], [proc])

                        if isvalid is False:
                            continue

                        x_conn_var[id] = conn_var[proc] 
                        print("Read ", id ," isvlalid = ", isvalid, " var = ", x_conn_var[id], flush=True)

                        if id not in self.read_values[node][stream].keys():
                            self.read_values[node][stream][id] = np.array([])
                        
                        if self.read_values[node][stream][id].size == 0:
                            self.read_values[node][stream][id] =  x_conn_var[id]
                        else:                 
                            #print("Contatenating ", self.read_values[node][stream][id], " with ", x_conn_var[id], flush = True) 
                            self.read_values[node][stream][id] = np.concatenate((self.read_values[node][stream][id], x_conn_var[id]), axis=0) 
                        
                        x_conn_var[id] = self.read_values[node][stream][id]
                        print("Read 2 ", id ," isvlalid = ", isvalid, " var = ", x_conn_var[id], flush=True)
                
                        if n_steps_min == 0:
                            n_steps_min = self.read_values[node][stream][id].shape[0]
                        elif self.read_values[node][stream][id].shape[0] < n_steps_min:
                            n_steps_min = self.read_values[node][stream][id].shape[0]
                    i += 1 

                i = 0
                print("Total steps" , n_steps_min, flush= True)  
                for adios_conc in self.active_conns[node][stream]: 
                    for proc in self.procs_per_conns[node][stream]:
                        id = i + proc
                        diff = self.read_values[node][stream][id].shape[0] - n_steps_min  
                        print("Diff for id=",id, " is ", diff, " original ", self.read_values[node][stream][id].shape[0])
                        if id not in x_conn_var.keys():
                            continue
                        if x_conn_var[id].ndim == 2 and n_steps_min %2 == 1:
                           diff += 1
                        shape0 = self.read_values[node][stream][id].shape[0] - diff
                        if diff > 0: 
                            if x_conn_var[id].ndim == 2:
                                x_conn_var[id] = x_conn_var[id][0:shape0,:]
                                self.read_values[node][stream][id] = self.read_values[node][stream][id][-diff:, :]
                            else:
                                x_conn_var[id] = x_conn_var[id][0:shape0]
                                self.read_values[node][stream][id] = self.read_values[node][stream][id][-diff:]
                        else: 
                            self.read_values[node][stream][id] =  np.array([])

                        print("Read values for proc ", id, " values ", x_conn_var[id], flush = True)
                        x_conn_var[id] = self.__compute_step_times(x_conn_var[id]);                           
                        print("After proccessing proc ", id, " values ", x_conn_var[id], " shape ", x_conn_var[id].shape[0], flush = True)
                    i += 1
                       
                step_times[node][stream] = self.__compute_max_set(x_conn_var)
                n_steps = len(step_times[node][stream])

                if self.stream_n_steps[node][stream] == 0:
                    self.stream_sum_steptime[node][stream] = 0

                time_now = dt.datetime.now() 

                if n_steps > 0: #self.stream_cur_steps[node][stream]:
                    if self.restart[node][stream] == True:
                        self.restart_steps[node][stream].append(n_steps)
                        self.restart[node][stream] = False          
                    self.stream_read_steps[node][stream].append(list(step_times[node][stream]))
                    self.stream_cur_steps[node][stream] = self.stream_cur_steps[node][stream] + n_steps
                    self.stream_sum_steptime[node][stream] = np.sum(step_times[node][stream]) #cur_diff
                    self.stream_n_steps[node][stream] = self.stream_n_steps[node][stream] + n_steps 
                     
                if self.stream_n_steps[node][stream] > 10:
                    t_read = self.stream_cur_steps[node][stream] - 10
                    self.stream_sum_steptime[node][stream] =  np.sum(self.stream_read_steps[node][stream][t_read:]) #cur_diff
                    self.stream_n_steps[node][stream] = 0
            return         
        #sys.stdout.flush()

    def update_model_conf(self, config, restart=False):
        self.active_conns = config.active_reader_objs
        self.procs_per_conns = config.reader_blocks
        self.r_map = config.local_res_map
        self.stream_config = config.reader_config
        #print(config.reader_config, " next ", self.stream_config)
        ini_time = dt.datetime.now()
        for node in self.active_conns.keys():
            self.stream_cur_steps[node] = {}
            self.stream_expected_steptime[node] = {}
            self.stream_sum_steptime[node] = {} 
            self.stream_path[node] = {}
            self.stream_ext[node] = {}
            self.stream_step_var[node] = {}
            self.stream_n_steps[node] = {}
            self.restart[node] = {}
            self.restart_steps[node] = {}
            self.stream_read_steps[node] = {} 
            self.read_values[node] = {} 
            self.stream_write_steps[node] = {} 
            self.stream_connect_steps[node] = {} 
            self.stream_process_steps[node] = {} 
            for stream in list(self.active_conns[node].keys()):
                self.stream_cur_steps[node][stream] = 0
                self.stream_read_steps[node][stream] = [] 
                self.read_values[node][stream] = {} 
                self.stream_write_steps[node][stream] = 0
                self.stream_connect_steps[node][stream] = 0
                self.stream_process_steps[node][stream] = 0 
                self.stream_sum_steptime[node][stream] = 0
                self.stream_path[node][stream] = stream[0 : stream.rfind('/')]
                self.stream_step_var[node][stream] = self.stream_config[node][stream][0].strip() 
                self.stream_expected_steptime[node][stream] = int(self.stream_config[node][stream][1].strip()) 
                self.stream_ext[node][stream] = self.stream_config[node][stream][2].strip() 
                self.stream_n_steps[node][stream] = 0
                self.restart[node][stream] = True
                self.restart_steps[node][stream] = []
       
    def get_curr_state(self):
        j_data = {}
        nodes = self.active_conns.keys()
        time_now = dt.datetime.now() 
        for node in nodes:
            #print("Pace: Preparing an update for node ", node)
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
                if self.stream_n_steps[node][stream] != 0 :
                    j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream]/self.stream_n_steps[node][stream])  
                else:
                    j_data[node]['AVG_STEP_TIME'][str] = float(self.stream_sum_steptime[node][stream])
            break
        return j_data

    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update 
                                                                                                             
