import json
from collections import deque
from functools import partial
from adios2_tau_reader import adios2_tau_reader
from mpi4py import MPI
import sys
import datetime as dt
import os
import numpy
import pandas as pd
from collections import Counter
from collections import OrderedDict
from enum import Enum
import math
import csv
from enum import Enum


class Granularity(Enum):
    NODEWORKFLOW = 0
    NODETASK = 1
    TASK = 2
    WORKFLOW = 3 

class OrderedCounter(Counter, OrderedDict):
     'Counter that remembers the order elements are first encountered'
     def __repr__(self):
         return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

     def __reduce__(self):
         return self.__class__, (OrderedDict(self),)


def _fix_ranges_(func, val_l, val_tot):
    if len(val_l) != len(val_tot):
        nlen = min(len(val_l), len(val_tot)) 
        val_l = val_l[:nlen]
        val_tot = val_tot[:nlen]
    return val_l, val_tot
    
def _percentage_(func, nprocs, val_l, val_tot):
    percentage = {}
    max_p = 0
    for i in range(nprocs):
        val_l[i], val_tot[i] = _fix_ranges_(func, val_l[i], val_tot[i])
        percentage[i] = [] 
        percentage[i].extend([ (x/y*100) if y else 0 for x,y in zip(val_l[i] , val_tot[i])])
        if len(percentage[i]) != 0 :
            if max(percentage[i]) == 0:
                print("[Rank ", self.my_rank, "] :","Max percenatge is 0 for index " , i, " in ", func)
        if len(percentage[i]) != 0 and max_p < max(percentage[i]):
             max_p = max(percentage[i])
    return percentage, max_p

def _divide_(func, nprocs, val_l, val_tot):
    div = {}
    max_v = 0
    for i in range(nprocs):
        val_l[i], val_tot[i] = _fix_ranges_(func, val_l[i], val_tot[i])
        div[i] = []
        div[i].extend([ x/y if y else 0 for x,y in zip(val_l[i] , val_tot[i])])
        if len(div[i]) != 0 :
            if max(div[i]) == 0:
                print("[Rank ", self.my_rank, "] :","Max division is 0 for index " , i, " in ", func)
        if len(div[i]) != 0 and max_v < max(div[i]):
             max_v = max(div[i])
    return div, max_v

def _sub_(func, nprocs, val_l):
    sub = {}
    max_v = 0
    for i in range(nprocs):
        sub[i] = []
        sub[i].extend([j-k for k, j in zip(vals[:-1], vals[1:])])
    return sub

#class memory(abstract_model.model):
class sensor():

    def __init__(self, config):
        self.iter = 0

        self.active_conns = []
        #self.reader_conns = []
        self.r_map = None
        self.name = config.name
        self.m_status_var = {} 
        self.var_val = {} 
        self.reduction_operation = {}
        self.first_write = {}
              
        for granularity in Granularity:
            self.m_status_var[granularity] = None 
            self.reduction_operation[granularity] = config.reduce[granularity]
            self.first_write[granularity] = True
 
        self.var_name = config.var_name
        self.my_rank = config.wrank
        self.comm = config.comm
        self.comm_size = config.comm_size
        self.update_model_conf(config)    

    def __compute_per(self, nprocs, val1, val2):
        val_per, maxp = _percentage_('compute_llc_miss_per', nprocs, val1, val2)
        return val_per
 
    def __compute_div(self, nprocs, val1, val2): 
        val_div, maxv = _divide_('compute_ipc', nprocs, val1, val2)
        return val_div
    
    def __timestamp_to_date(self, unix_ts):
        ts_in_ms = [ j/1000000 for j in unix_ts]
        dateconv = numpy.vectorize(dt.datetime.fromtimestamp)
        date1 = dateconv(ts_in_ms)
        return date1.tolist()

    def __group_by_frequency(self, narray, by_last=0): #Replace S with U for microsecond 
        narray_v = narray[:,0] # get the value
        nlist_k = narray[:,1].tolist() #get the timestamp
        nlist_k = self.__timestamp_to_date(nlist_k)

        pdf = pd.DataFrame(data=narray_v, index=nlist_k, columns=["value"])
        if by_last == 0:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).sum()
        else:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).last()
        #pdf = pdf["value"].fillna(method='ffill')
        pdf = pdf["value"].dropna() #method='ffill')
        #print("[Rank ", self.my_rank, "] :",pdf)  
        return pdf #.to_dict()

    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update

    def update_model_conf(self, config):
        self.active_conns = config.reader_objects
        self.blocks_to_read = config.reader_blocks
        #print(config.reader_objects) 
        ini_val = 0 #need a postive value for the counter
        ini_time = dt.datetime.now()

        nodes = self.active_conns.keys()

        for node in nodes:
            #for test
            self.m_status_var[node] = {}
            self.var_val[node] = {}
            streams = list(self.active_conns[node].keys())

            for stream in streams:
                procs = list(self.blocks_to_read[node][stream])
                self.m_status_var[node][stream] = []
                self.var_val[node][stream] = None
    
    def __remove_empty_nan(self, array):
        mask = numpy.any(numpy.isnan(array), axis=1) # | numpy.equal(array, 0), axis=1)
        return array[~mask]

  
    def __group_by_node_task_reduce(self, operation):
        var = {}
        for key in self.var_val.keys():
            var[key] = {}
            for task in self.var_val[key].keys():
                var[key][task] = {}
                if task in self.var_val[key].keys():
                    var[key][task] = self.__reduce(self.var_val[key][task], operation) 
        return var 
        
    def __group_by_task_reduce(self, operation):
        var = {}
        for key in self.var_val.keys():
            for task in self.var_val[key].keys():
                if task not in var.keys():
                        var[task] = self.var_val[key][task] 
                else:
                    var[task] = numpy.append(var[task], self.var_val[key][task])        
        for task in var.keys():
            var[task] = self.__reduce(var[task], operation)
        return var
  
    def __group_by_workflow_reduce(self, operation):
       var = None
       var_ret = {}
       var_ret["WORKFLOW"] = None
       for key in self.var_val.keys():
           for task in self.var_val[key].keys():
               if var is None:
                   var = self.var_val[key][task]
               else:
                   var = numpy.append(var, self.var_val[key][task])
       var_ret["WORKFLOW"] = self.__reduce(var, operation)
       return var_ret

    def __group_by_node_workflow_reduce(self, operation):
        var = {}
        for key in self.var_val.keys():
            var[key] = None
            for task in self.var_val[key].keys():
                if var[key] == None:
                    var[key] = self.var_val[key][task]
                else:
                    var[key] = numpy.append(var[key], self.var_val[key][task])
            var[key] = self.__reduce(var[key], operation)  
        return var 

    def __reduce(self, var, operation):
        if operation == "MAX":
            return numpy.nanmax(var)
        if operation == "MIN":
            return numpy.nanmin(var)
        if operation == "SUM":
            return numpy.nansum(var)
        if operation == "AVG":
            return numpy.nanmean(var)
        if operation == "STD":
            return numpy.nanstd(var)
        if operation == "FIRST":
            return var[0]
        if operation == "LAST":
            return var[-1]
        if operation == "ANY":
            return var[numpy.random.random_integers(0, high=var.size-1)]
    
    def __join(self, var1, var2, operation):
        if operation == "PER":
            return (var1/var2)* 100 
        if operation == "DIV":
            return (var1/var2) 
        if operation == "SUM":
            return (var1 + var2)
        if operation == "MAX":
            return numpy.nanmean(var)
        if operation == "SUB":
            return (var1 + var2)

    def __read_var(self, active_conc, cntr_map, procs=[0], threads=[0]):
        is_valid, val_ar = active_conc.read_var(self.var_name, procs, threads)
        if is_valid == True:
            for proc in procs:
                for th in threads:
                    val_tmp = val_ar[proc]
                    tmp_ar = val_tmp 
                    if tmp_ar.size != 0:
                        tmp_ar = self.__remove_empty_nan(tmp_ar)         
  
                    if tmp_ar.size != 0:
                        cntr_df = tmp_ar #cntr_df.dropna()
                        if cntr_map is None:
                            cntr_map = cntr_df
                        else:
                            cntr_map = numpy.concatenate((cntr_map, cntr_df), axis=0)
        return cntr_map

    def update_curr_state(self):
        var_val = {}
        k = 0 
        nodes = self.active_conns.keys()

        self.iter = self.iter + 1  
        for node in nodes:
            #for test
            #var_val[node] = {}
            streams = list(self.active_conns[node].keys())
            for stream in streams:
                #self.var_val[node][stream] = {}
                procs = list(self.blocks_to_read[node][stream])
                threads = [0]
                for active_conc in self.active_conns[node][stream]:
                    self.var_val[node][stream]  = self.__read_var(active_conc, self.var_val[node][stream], procs, threads)

        for granularity in Granularity:
            if self.reduction_operation[granularity] != None: 
                if ( granularity == Granularity.NODEWORKFLOW ):
                    self.m_status_var[granularity] = self.__group_by_node_workflow_reduce(self.reduction_operation[granularity])
                elif ( granularity == Granularity.NODETASK ) :
                    self.m_status_var[granularity] = self.__group_by_node_task_reduce(self.reduction_operation[granularity])
                elif  ( granularity == Granularity.TASK):
                    self.m_status_var[granularity] = self.__group_by_task_reduce( self.reduction_operation[granularity])
                elif ( granularity ==  Granularity.WORKFLOW ):
                    self.m_status_var[granularity] = self.__group_by_workflow_reduce(self.reduction_operation[granularity])


        self.dump_curr_state()
        return True

    def __filter_results(self, arr, res_dict, res_fltrd, idx, axis = 0):
        if arr is not None:
            arr  = [numpy.sum(arr, axis=0)]
            if idx not in res_dict.keys() or res_dict[idx] is None:
                res_dict[idx] = arr
            else:
                #print(res_dict[idx], arr) 
                res_dict[idx] = numpy.concatenate((res_dict[idx], arr))
        else:
            res_dict[idx] = None

        if res_dict is not None:# update the new state
            res_fltrd[idx] = self.__compute_rmax(self.__compute_ravg(res_dict[idx][-self.max_history:]))

            #if res_fltrd is not None:
            #    self.m_status_vms_max[node] = numpy.concatenate((self.m_status_vms_max[node], [self.__compute_max(res_fltrd)] ))
            #print("[Rank ", self.my_rank, "] :","Filtered RESULT::\n", res_fltrd[idx])
        return arr    

    def __compute_ravg(self, arr):
        if arr is None:
            return None 
        df = pd.DataFrame(arr)
        df_avg = df.rolling(self.avg_window, min_periods=1).mean()       
        return df_avg.to_numpy()
    
    def __compute_rmax(self, arr):
        if arr is None:
            return None 
        df = pd.DataFrame(arr)
        df_max = df.rolling(self.max_window, min_periods=1).max()       
        return df_max.to_numpy()

    def __compute_max(self, array):
        if isinstance(array,dict):
            return 0
        if array is None:
            return 0 
        array_max = array.max()
        return array_max

    def __compute_min(self, array):
        if isinstance(array,dict):
            return 0
        if array is None:
            return 0 
        #print("[Rank ", self.my_rank, "] :",df.head())
        array_min = array.min()
        return array_min

    def __compute_inc(self, lst):
        if lst is None:
            return 0 
        val_n = lst[-1]
        val_o = lst[-2]
        return ((val_n - val_o)/val_o) * 100 

    def __compute_dec(self, lst):
        if lst is None:
            return 0 
        val_n = lst[-1]
        val_o = lst[-2]
        return ((val_o - val_n)/val_o) * 100 

    def __check_overflow(self, ar, writer, index, sheetnm):
        if ar is None:
            return
        total_rows = numpy.shape(ar)[0] #ar.shape[0] 
        #print("[Rank ", self.my_rank, "] :",total_rows)
        if total_rows > index:
            temp_ar = ar[index:]
            #if temp_df.shape[0] > 1:
                #temp_df = temp_df[-2:]
            pd.DataFrame(temp_ar).to_csv(writer, header = False)
            #print("[Rank ", self.my_rank, "] : WROTE ", temp_ar, flush=True)
            #temp_df.to_excel(xlsx_writer, startrow = index, sheet_name = sheetnm)
            ar = ar[-self.max_history:] 
            total_rows = numpy.shape(ar)[0] 
            index = total_rows
        return ar, index
 
    def create_workbook(self, filename, sheetnames):
        workbook = xlsxwriter.Workbook(filename)
        for sheet in sheetnames:
            worksheet = workbook.add_worksheet(sheet)
        workbook.close()

    def dump_curr_state(self):
        for granularity in Granularity:
            if self.m_status_var[granularity] is not None:
                filename = self.name + "-" + str(self.my_rank) + "-" + granularity.name + "-" + self.var_name + ".csv"
                with open(filename, 'a') as writer:
                     w = csv.DictWriter(writer, self.m_status_var[granularity].keys())
                     if self.first_write[granularity] == True:
                         self.first_write[granularity] = False 
                         w.writeheader()
                     w.writerow(self.m_status_var[granularity])
        return
   
    def preprocess(self):
        pass 

    def join_sensor(self, sensor, granularity, operation):
        if self.join == True:
            if granularity != Granularity.TASK or granularity != Granularity.WORKFLOW:
                for key1 in self.m_status_var[granularity].keys():
                    for key2 in self.m_status_var[granularity][key1].keys():
                        var = numpy.append(self.m_status_var[granularity][key1][key2], sensor.m_status_var[granularity][key1][key2])
                        self.m_status_var[granularity][key1][key2] = self.__join(var, operation)
            else:
                for key1 in self.m_status_var[granularity].keys():
                    var = numpy.append(self.m_status_var[granularity][key1], sensor.m_status_var[granularity][key1])
                    self.m_status_var[granularity][key1] = self.__join(var, operation)
               
    def get_curr_state(self):
        j_data = {}
        print(self.m_status_var)
        for granularity in Granularity:
            if self.reduction_operation[granularity] is not None:
                j_data[granularity] = json.dumps(self.m_status_var[granularity])

        recvbuff = None

        global_data = self.comm.gather(j_data, root=0)
        j_data = {}
        if self.my_rank == 0:
           varW = None
           varT = {}
           for i in range(self.comm_size):
               #gdata = json.loads(global_data[i]) 
               gdata = global_data[i]
               #print(gdata)  
               print(gdata)
               for gran in gdata.keys():
                       if gran not in j_data.keys():
                           j_data[gran] = {}
                       gdata_gran = json.loads(gdata[gran])
                       for key in gdata_gran.keys():
                           print(gdata_gran[key], flush = True) 
                           if gdata_gran[key] is None:
                               continue
                           if gran == Granularity.TASK: 
                               if key not in varT:
                                   varT[key] = gdata_gran[key]
                               else:          
                                   varT[key] = numpy.append(varT[key], gdata_gran[key])
                           elif gran == Granularity.WORKFLOW: 
                               if varW is None:
                                   varW = gdata_gran[key]
                               else:          
                                   varW = numpy.append(varW, gdata_gran[key])
                           else:
                               j_data[gran][key] = gdata_gran[key]
         
           for key in varT.keys():
              j_data[Granularity.TASK][key] = self.__reduce(varT[key], self.reduction_operation[Granularity.TASK]) 
          
           j_data[Granularity.WORKFLOW]= self.__reduce(varW, self.reduction_operation[Granularity.TASK]) 

        self.comm.Barrier()
        return j_data 

class my_config:
    def __init__(self):
        self.reduce = {}
        for granularity in Granularity:
            self.reduce[granularity] = None
        self.reader_objects = None  
        self.reader_blocks = None 
        self.var_name = None
        self.join_operation = None  
        self.join_sensor = None 
        self.preprocess_sensor = None 
        self.wrank = None
        self.comm = None

if __name__ == "__main__":
    config = my_config()
    adios_reader = {}
    active_reader_blocks = {} 
    nstreams = int(sys.argv[1])
    nprocs = {}
    n_per_node = {}
    streams = {}
    config.comm = MPI.COMM_WORLD
    config.wrank = config.comm.Get_rank()
    config.comm_size = config.comm.Get_size()
    nnodes = config.comm_size 
   
    for n in range(nnodes):   
        node = n + 1 
        if n != config.wrank:
            continue 
        adios_reader[str(node)] = {}
        active_reader_blocks[str(node)] = {}
        for i in range(nstreams): 
            streams[i] = str(sys.argv[i+2])
            adios_reader[str(node)][streams[i]] = []
            active_reader_blocks[str(node)][streams[i]] = []

    for i in range(nstreams): 
        nprocs[i] = range(int(sys.argv[i + 2 + nstreams]))
        n_per_node[i] = len(nprocs[i])/nnodes
    #gpu_n = sys.argv[nstreams + 2 + nstreams]
    
    adios2_engine = "BPFile" #str(sys.argv[3]) # adios2 engine to use for reading..
    #freq_sec = "5s" #sys.argv[4] # frequency at which the data needs to be organised (in sec) - minimum value 1s..

    for n in range(nnodes): 
            #for test
        if n != config.wrank:
            continue 
        for i in range(nstreams):
            for proc in nprocs[i]:
                if proc >= n_per_node[i] * (n+1):
                    break
                if proc < n_per_node[i] * (n):
                    continue 

                str_split = streams[i].split('.bp')
                con_str = str_split[0] + "-" + str(proc) + ".bp"
                reader_obj = adios2_tau_reader(con_str, adios2_engine, MPI.COMM_SELF, [0], 'profile')
                adios_reader[str(n + 1)][streams[i]].append(reader_obj)
                active_reader_blocks[str(n + 1)][streams[i]].append(proc)
    
    config.reader_objects = adios_reader
    config.reader_blocks = active_reader_blocks

    print(adios_reader)   
    print(active_reader_blocks)    

    config.var_name = "LAST_LEVEL_CACHE_MISSES"
    config.reduce[Granularity.NODETASK] = "SUM"
    config.reduce[Granularity.TASK] = "SUM"
    config.reduce[Granularity.WORKFLOW] = "SUM"
    config.reduce[Granularity.NODEWORKFLOW] = "SUM"
    config.name = "LLCM"

    m_stats = sensor(config)
    
    reader_objs = [1]
    
    for n in range(nnodes):
        if n != config.wrank:
            continue 
        for i in range(nstreams):
            reader_objs.extend(adios_reader[str(n+1)][streams[i]])

    reader_objs = reader_objs[1:]
    done = 0

    for reader_ob in reader_objs:
        reader_ob.open()

    timestep = 1
    while done == 0:
        done = 1
        for reader_ob in reader_objs:
            #print (reader_ob)
            timestep += 1
            ret = reader_ob.advance_step()
            if ret == True:
               done = 0
        config.comm.Barrier()
 
        if done == 0:
            m_stats.update_curr_state()
            if timestep == 49:
                print("Update for" +  str(timestep) + ":")
                print(m_stats.get_curr_state(), end="\n\n")

            for reader_ob in reader_objs:
               reader_ob.end_step()

    for reader_ob in reader_objs:
        reader_ob.close()

    #m_stats.dump_curr_state()    
