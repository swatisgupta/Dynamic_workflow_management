from runtime_monitor import helper
import json
from collections import deque
from runtime_monitor import abstract_model
from functools import partial
#from pandas.tseries.frequencies import to_offset
#from pandas import Timestamp
import datetime as dt
import os
import numpy
import pandas as pd
from collections import Counter
from collections import OrderedDict
from enum import Enum
import math
import openpyxl
import xlsxwriter

likwid_counters = {}
papi_counters = {
           "Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz" : {
              "llc_misses": [ "LAST_LEVEL_CACHE_MISSES", "D"],
              "llc_refs": [ "LAST_LEVEL_CACHE_REFERENCES", "D"],
              "ld_stalls": [ "CYCLE_ACTIVITY:STALLS_LDM_PENDING", "D"],
              "inst_ret": ["INSTRUCTIONS_RETIRED", "D"],
              "st_stalls" : ["RESOURCE_STALLS:SB", "D" ],
              "cpu_cyc" : ["ix86arch::UNHALTED_CORE_CYCLES", "D"]
           },
           "POWER9, altivec supported" : {
              "llc_refs": ["perf::LLC-LOADS", "D" ],
              "llc_misses": ["perf::LLC-LOAD-MISSES", "D" ],
              "ld_stalls": ["PM_LD_L3MISS_PEND_CYC", "D"], #PM_CMPLU_STALL_DMISS_L3MISS", "D"],
              "inst_ret": ["PM_INST_CMPL", "D" ],
              "cpu_cyc": ["PM_RUN_CYC", "D"], #perf::PERF_COUNT_SW_CPU_CYCLES", "D" ],
              "gpu_tbw": ["cuda:::metric_nvlink_transmit_throughput:device=0", "D" ],
              "gpu_rbw": ["cuda:::metric_nvlink_receive_throughput:device=0", "D" ]
            }
       }

metrics = {
            "Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz" : [
              "llc_miss_per",
              "ld_stalls_per",
              "ipc"
            ],
            "POWER9, altivec supported" : [
              "llc_miss_per",
              "ld_stalls_per",
              "ipc"
            ]
       }

memory_size = {
            "Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz" : "128",
            "POWER9, altivec supported" : "512"
        }


class MetricID(Enum):
    RSS = 0
    VMS = 1
    LLCM = 2 
    LLCR = 3
    LDS = 4
    INS = 5
    CYC = 6


class OrderedCounter(Counter, OrderedDict):
     'Counter that remembers the order elements are first encountered'

     def __repr__(self):
         return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

     def __reduce__(self):
         return self.__class__, (OrderedDict(self),)


def _fix_ranges_(func, val_l, val_tot):
    if len(val_l) != len(val_tot):
        print("[Rank ", self.my_rank, "] :",func, " : Length of meaurements donot match!\n", len(val_l), "!=", len(val_tot))
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

class memory(abstract_model.model):

    def __init__(self, config):
        self.iter = 0
        self.hd_counters = {} 
        self.rss_m = ["Memory Footprint (VmRSS) (KB)", "C"]
        self.vms_m = ["Heap Memory Used (KB)", "C"] # "Peak Memory Usage Resident Set Size (VmHWM) (KB)", "C"]
        self.metric_func = []
        self.adios2_active_conns = []
        self.r_map = None
        self.name = "memory"
        self.frequency = '1s'
        self.m_status_rss_max = {} 
        self.m_status_vms_max = {} 
        self.m_status_ipc_max = {} 
        self.m_status_ldsp_max = {} 
        self.m_status_llcp_max = {} 
        self.m_status_ipc_dec = {} 
        self.m_status_ldsp_inc = {} 
        self.m_status_llcp_inc = {} 
        self.last_index = {}
        self.avg_window = 60 
        self.max_window = 60
        self.max_history = 120
        self.my_rank = config.wrank
        self.last_rcd = {}
        self.rss = {}
        self.vms = {}
        self.ldsp = {}
        self.llcp = {}
        self.ipc = {}
        self.fltrd_rss = {}
        self.fltrd_vms = {}
        self.fltrd_ldsp = {}
        self.fltrd_llcp = {}
        self.fltrd_ipc = {}
        self.urgent_update = False
          
        if config.hc_lib  == 'papi':
            self.hd_counters = papi_counters[config.cpu_model.strip()]
            self.metric_func = metrics[config.cpu_model.strip()]
            self.rss_thresh = math.ceil(0.90 * int(memory_size[config.cpu_model.strip()]))
        #print("[Rank ", self.my_rank, "] :","Machine name", config.cpu_model, "counter" , self.hd_counters)            
        self.update_model_conf(config)    

    def __compute_llc_miss_per(self, nprocs, llc_miss, llc_refs):
        llc_per, maxp = _percentage_('compute_llc_miss_per', nprocs, llc_miss, llc_refs)
        return llc_per
 
    def __compute_ld_stalls_per(self, nprocs, ld_stalls, core_cyc): 
        lds_per, maxp = _percentage_('compute_ld_stalls_per', nprocs, ld_stalls, core_cyc)
        return lds_per
        
    def __compute_ipc(self, nprocs, ins_ret, core_cyc): 
        ipc, maxv = _divide_('compute_ipc', nprocs, ins_ret, core_cyc)
        return ipc
    
    def __timestamp_to_date(self, unix_ts):
        ts_in_ms = [ j/1000000 for j in unix_ts]
        dateconv = numpy.vectorize(dt.datetime.fromtimestamp)
        date1 = dateconv(ts_in_ms)
        return date1.tolist()

    def __group_by_frequency(self, narray, by_last=0): #Replace S with U for microsecond 
        #print("[Rank ", self.my_rank, "] :",narray)  
        narray_v = narray[:,0] # get the value
        nlist_k = narray[:,1].tolist() #get the timestamp
        nlist_k = self.__timestamp_to_date(nlist_k)

        pdf = pd.DataFrame(data=narray_v, index=nlist_k, columns=["value"])
        #print("[Rank ", self.my_rank, "] :",pdf)
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
        self.adios2_active_conns = config.active_reader_objs
        self.r_map = config.local_res_map
        self.procs_per_ctr = config.reader_procs
        self.blocks_to_read = config.reader_blocks
        ini_val = 0 #need a postive value for the counter
        ini_time = dt.datetime.now()
        pdf = pd.DataFrame(data=[ini_val], index=[ini_time], columns=["value"])
        pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).last()  
        obj = pdf["value"] #numpy.array([[ini_time, ini_val]])
        nodes = self.adios2_active_conns.keys()
        for node in nodes:
            self.ldsp[node] = {}
            self.llcp[node] = {}
            self.ipc[node] = {}
            self.fltrd_ldsp[node] = {}
            self.fltrd_llcp[node] = {}
            self.fltrd_ipc[node] = {}
            self.fltrd_ipc[node] = {}
            self.fltrd_rss[node] = {}
            self.fltrd_vms[node] = {}
            self.last_rcd[node] = {}
            self.m_status_rss_max[node] = []
            self.m_status_vms_max[node] = []
        
            self.m_status_ldsp_max[node] = {}
            self.m_status_llcp_max[node] = {}
            self.m_status_ipc_max[node] = {}
            self.m_status_ldsp_inc[node] = {}
            self.m_status_llcp_inc[node] = {}
            self.m_status_ipc_dec[node] = {}
            self.last_index[node] = { 'rss':0, 'vms':0}
        
      
            streams = list(self.adios2_active_conns[node].keys())
            for stream in streams:
                procs = list(self.blocks_to_read[node][stream])
                #obj = OrderedCounter(pdf["value"].to_dict()) #numpy.array([[ini_time, ini_val]])
                #obj[ini_time] = ini_val
                self.last_index[node][stream] = {'lds':0, 'llc':0, 'ipc':0}
                self.m_status_ldsp_max[node][stream] = []
                self.m_status_llcp_max[node][stream] = []
                self.m_status_ipc_max[node][stream] = []
                self.m_status_ldsp_inc[node][stream] = []
                self.m_status_llcp_inc[node][stream] = []
                self.m_status_ipc_dec[node][stream] = []

                self.last_rcd[node][stream] = {}
                for i in range(0,7): #for each metrics
                    self.last_rcd[node][stream][i] = obj 
                self.ldsp[node][stream] = None 
                self.fltrd_ldsp[node][stream] = None 
                self.llcp[node][stream] = None 
                self.fltrd_ldsp[node][stream] = None 
                self.ipc[node][stream] = None 
                self.fltrd_ipc[node][stream] = None 
    
    def __remove_empty_nan(self, array):
        mask = numpy.any(numpy.isnan(array), axis=1) # | numpy.equal(array, 0), axis=1)
        return array[~mask]

    def __get_agg_values_for(self, adios_conc, cntr, cntr_map, last_rcd, by_last=0, procs=[0], threads=[0], diff_idx=-1):
        is_valid, val_ar = adios_conc.read_var(cntr[0], procs, threads)
        if is_valid == True:
            for proc in procs:
                for th in threads:
                    val_tmp = val_ar[proc]
                    #tmp_ar = val_tmp #[val_tmp[:,0] == th] 
                    print("[Rank ", self.my_rank, "] : process ", proc, " counter ", cntr, "Raw values ", val_tmp, flush = True)
                    #print("[Rank ", self.my_rank, "] :",val_tmp)
                    tmp_ar = val_tmp 
                    if tmp_ar.size != 0:
                        tmp_ar = tmp_ar[:,[1,2]]
                        tmp_ar = self.__remove_empty_nan(tmp_ar)         
                        print("[Rank ", self.my_rank, "] : process ", proc, " counter ", cntr, "After empty/Nan remova ", tmp_ar, flush = True)
  
                    if tmp_ar.size != 0:
                        cntr_df = self.__group_by_frequency(tmp_ar, by_last)
                        print("[Rank ", self.my_rank, "] : process ", proc, " counter ", cntr, "After group by ", cntr_df, flush = True)
                        #cntr_df = cntr_df.dropna()
                        if diff_idx != -1:
                             temp_df = last_rcd[diff_idx]
                             if cntr[1] == "C": 
                                 cntr_df = temp_df.append(cntr_df)
                             #else:
                             #    cntr_df = temp_df
                             last_rcd[diff_idx] = cntr_df[-1:]
                             if cntr[1] == "C": 
                                cntr_df = cntr_df.diff()[1:]
                             print("[Rank ", self.my_rank, "] : process ", proc, " counter ", cntr, "After diff ", cntr_df, flush = True)
                        if cntr_map is None:
                            cntr_map = cntr_df
                            #print("[Rank ", self.my_rank, "] :","Was None ", cntr_map )
                            print("[Rank ", self.my_rank, "] : process " , proc , "counter ", cntr, " Counter mapping ", cntr_map, flush = True)
                        else:
                            cntr_map = cntr_map.append(cntr_df)
                            
                            print("[Rank ", self.my_rank, "] : process " , proc , "counter ", cntr, " Counter mapping ", cntr_map, flush = True)
                            if by_last == 1:
                                cntr_map = cntr_map.sort_index(ascending=True)
                                cntr_map = cntr_map.groupby(pd.Grouper(freq=self.frequency)).last()
                                #cntr_map = cntr_map.groupby(pd.Grouper(freq=self.frequency)).tail(1)
                            else:
                                cntr_map = cntr_map.sort_index(ascending=True)
                                cntr_map = cntr_map.groupby(pd.Grouper(freq=self.frequency)).sum()
                print("[Rank ", self.my_rank, "] : process " , proc , "counter ", cntr, " Processed values ", cntr_map, flush = True)
        return cntr_map, last_rcd

    def update_curr_state(self):
        rss_val = {}
        vms_val = {}
        llcr_val = {} 
        llcm_val = {} 
        lds_val = {} 
        ins_val = {} 
        cyc_val = {}
        k = 0 
        c_pressure = False
        b_pressure = False
        flag_llc = flag_lds = flag_ipc = False 
        nodes = self.adios2_active_conns.keys()
        print("[Rank ", self.my_rank, "] :","Update for step ::", self.iter)
        self.iter = self.iter + 1  
        for node in nodes:
            rss_val = None
            vms_val = None
            #print("[Rank ", self.my_rank, "] :","Looking for node:: ", node)
            streams = list(self.adios2_active_conns[node].keys())
            for stream in streams:
                procs = list(self.blocks_to_read[node][stream])
                print("[Rank ", self.my_rank, "] :","Looking for stream:: ", stream, " with procs", procs)
                print("Active connections ", self.adios2_active_conns[node][stream]) 
                llcm_val = None
                llcr_val = None
                lds_val = None
                ins_val = None
                cyc_val = None
                thread_l1 = [0]
                thread_l = [0,1,2,3]
                for active_conc in self.adios2_active_conns[node][stream]:
                #read RSS
                    rss_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.rss_m, rss_val, self.last_rcd[node][stream], 1, procs, thread_l1)
                    #print("[Rank ", self.my_rank, "] :","Read RSS", self.last_rcd[node][stream][0])
                    vms_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.vms_m, vms_val, self.last_rcd[node][stream], 1, procs, thread_l1)
                    #print("[Rank ", self.my_rank, "] :","Read VMS", self.last_rcd[node][stream][1])
                    #print("[Rank ", self.my_rank, "] :","Metric funcs are ", self.metric_func)
                    read_cyc = 0
                    for met in self.metric_func:
                        if met == "ld_stalls_per" or met == "ipc":
                            #read No of CPU cycles
                            if read_cyc != 1:
                                cyc_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.hd_counters['cpu_cyc'], cyc_val, self.last_rcd[node][stream], 0, procs, thread_l1, MetricID.CYC.value)
                                read_cyc = 1
                            #print("[Rank ", self.my_rank, "] :","Read CYC")
                        if met == "ld_stalls_per":
                            #read No of Load Stalls
                            lds_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.hd_counters['ld_stalls'], lds_val, self.last_rcd[node][stream], 0, procs, thread_l1, MetricID.LDS.value)
                            #print("[Rank ", self.my_rank, "] :","Read STALLS")
                        elif met == "llc_miss_per":
                            #read No of L3 misses
                            #print("[Rank ", self.my_rank, "] :",self.hd_counters['llc_misses'])
                            llcm_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.hd_counters['llc_misses'], llcm_val, self.last_rcd[node][stream], 0, procs, thread_l1, MetricID.LLCM.value)
                            #print("[Rank ", self.my_rank, "] :","Read LLC MISS")
                            #print("[Rank ", self.my_rank, "] :",llcm_val)
                            #read No of L3 references
                            llcr_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.hd_counters['llc_refs'], llcr_val, self.last_rcd[node][stream], 0, procs, thread_l1, MetricID.LLCR.value)
                        elif met == "ipc":
                            #read No of Instruction
                            ins_val, self.last_rcd[node][stream] = self.__get_agg_values_for(active_conc, self.hd_counters['inst_ret'], ins_val, self.last_rcd[node][stream], 0, procs, thread_l1, MetricID.INS.value)
                            #print("[Rank ", self.my_rank, "] :","Read IPC")
                for met in self.metric_func:
                    if met == "llc_miss_per" and llcm_val is not None: 
                        print("[Rank ", self.my_rank, "] :","LLC VAR ", llcm_val, " LLCR  val ", llcr_val, flush=True)
                        if self.llcp[node][stream] is None:
                            self.llcp[node][stream] = llcm_val.div(llcr_val, fill_value=0).mul(100) 
                        else:
                            self.llcp[node][stream] = self.llcp[node][stream].append(llcm_val.div(llcr_val, fill_value=0).mul(100))
                        #self.llcp[node][stream] = self.llcp[node][stream][-self.max_history:]
                        self.fltrd_llcp[node][stream] = self.__compute_rmax(self.__compute_ravg(self.llcp[node][stream][-self.max_history:]))
                        print("[Rank ", self.my_rank, "] :","Filtered LLCP[", node, "][", stream ,"]:: \n", self.fltrd_llcp[node][stream])
                        '''
                        self.m_status_llcp_max[node][stream].append(self.__compute_max(self.fltrd_llcp[node][stream]))
                        self.m_status_llcp_inc[node][stream].append(self.__compute_inc(self.m_status_llcp_max[node][stream]))
                        if self.m_status_llcp_inc[node][stream][-1] >= 20:
                            flag_llc = True
                        '''
                    if met == "ld_stalls_per" and lds_val is not None:
                        if self.ldsp[node][stream] is None:
                            self.ldsp[node][stream] = lds_val.div(cyc_val, fill_value=0).mul(100) 
                        else:
                            self.ldsp[node][stream] = self.ldsp[node][stream].append(lds_val.div(cyc_val, fill_value=0).mul(100))
                        #self.lds[node][stream] = self.lds[node][stream][-self.max_history:]
                        self.fltrd_ldsp[node][stream] = self.__compute_rmax(self.__compute_ravg(self.ldsp[node][stream][-self.max_history:]))
                        print("[Rank ", self.my_rank, "] :","Filtered LDSP[", node, "][", stream ,"]:: \n", self.fltrd_ldsp[node][stream])
                        '''
                        self.m_status_lds_inc[node][stream].append(self.__compute_inc(self.m_status_lds_max[node][stream]))
                        if self.m_status_llcp_inc[node][stream][-1] >= 20:
                            flag_lds = True
                        ''' 
                    if met == "ipc" and ins_val is not None:
                        if self.ipc[node][stream] is None:
                            self.ipc[node][stream] = ins_val.div(cyc_val, fill_value=0).mul(100) 
                        else:
                            self.ipc[node][stream] = self.ipc[node][stream].append(ins_val.div(cyc_val, fill_value=0))
                        #self.ipc[node][stream] = self.ipc[node][stream][-self.max_history:]
                        self.fltrd_ipc[node][stream] = self.__compute_rmax(self.__compute_ravg(self.ipc[node][stream][-self.max_history:]))
                        print("[Rank ", self.my_rank, "] :","Filtered IPC[", node, "][", stream ,"]:: \n", self.fltrd_ipc[node][stream])
                        '''
                        self.m_status_ipc_max[node][stream].append(self.__compute_min(self.fltrd_ipc[node][stream]))
                        self.m_status_ipc_dec[node][stream].append(self.__compute_dec(self.m_status_ipc_max[node][stream]))
                        if self.m_status_llcp_inc[node][stream][-1] >= 20:
                            flag_ipc = True
                        '''
                    if flag_llc and flag_lds and flag_ipc:
                        b_pressure == True
            # keep only last X records
            if rss_val is not None: 
                 if node not in self.rss.keys():
                     self.rss[node] = rss_val
                 else: 
                     self.rss[node] = self.rss[node].append(rss_val)
            else:
                self.rss[node] = None 
            if self.rss[node] is not None:
            #    self.rss[node] = self.rss[node][-self.max_history:]
                self.fltrd_rss[node] = self.__compute_rmax(self.__compute_ravg(self.rss[node][-self.max_history:]))
            if self.fltrd_rss[node] is not None:
                self.m_status_rss_max[node].append(self.__compute_max(self.fltrd_rss[node]))
            print("[Rank ", self.my_rank, "] :","Filtered RSS::\n", self.fltrd_rss[node])

            if vms_val is not None:
                 if node not in self.vms.keys():
                     self.vms[node] = vms_val
                 else: 
                     self.vms[node] = self.vms[node].append(vms_val)
            else:
                self.vms[node] = None 
            if self.vms[node] is not None:
            #    self.vms[node] = self.vms[node][-self.max_history:]
            # update the new state
                self.fltrd_vms[node] = self.__compute_rmax(self.__compute_ravg(self.vms[node][-self.max_history:]))
 
            if self.fltrd_vms[node] is not None:
                self.m_status_vms_max[node].append(self.__compute_max(self.fltrd_vms[node]))
            print("[Rank ", self.my_rank, "] :","Filtered VMS::\n", self.fltrd_vms[node])

            if self.m_status_rss_max[node] is not None and ( len(self.m_status_rss_max[node]) != 0 and int(math.ceil(self.m_status_rss_max[node][-1]/(1024*1024))) >= self.rss_thresh ) or ( len(self.m_status_vms_max[node]) != 0 and int(math.ceil(self.m_status_vms_max[node][0])) > 0 ):
                c_pressure = True
                #print("[Rank ", self.my_rank, "] :","RSS is high", self.m_status_rss_max[node][-1], ">=", self.rss_thresh) 
                #print("[Rank ", self.my_rank, "] :","VMS is high", self.m_status_vms_max[node][-1], ">=", 0) 
             
            #if c_pressure or b_pressure:
            #    self.urgent_update = True 
            self.dump_curr_state()
        return True

    def __compute_ravg(self, df):
        if df is None:
            return None 
        df_avg = df.rolling(self.avg_window, min_periods=1).mean()       
        return df_avg
    
    def __compute_rmax(self, df):
        if df is None:
            return None 
        df_max = df.rolling(self.max_window, min_periods=1).max()       
        return df_max

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

    def __check_overflow(self, df, writer, index, sheetnm):
        if df is None:
            return
        total_rows = df.shape[0] 
        print("[Rank ", self.my_rank, "] :",total_rows)
        if total_rows > index:
            temp_df = df[index:]
            #if temp_df.shape[0] > 1:
                #temp_df = temp_df[-2:]
            temp_df.to_csv(writer, header = False)
            #print("[Rank ", self.my_rank, "] : WROTE ", temp_df, flush=True)
            #temp_df.to_excel(xlsx_writer, startrow = index, sheet_name = sheetnm)
            df = df[-self.max_history:] 
            total_rows = df.shape[0] 
            index = total_rows
        return df, index
 
    def create_workbook(self, filename, sheetnames):
        workbook = xlsxwriter.Workbook(filename)
        for sheet in sheetnames:
            worksheet = workbook.add_worksheet(sheet)
        workbook.close()

    def dump_curr_state(self):
        nodes = self.adios2_active_conns.keys()
        file_md = 'a'
        print("[Rank ", self.my_rank, "] :","NODES..", nodes)
        for node in nodes:
            filename = "memory-" + str(node) + "rss.csv"
            #print("[Rank ", self.my_rank, "] :","WRITING..", filename) 
            with open(filename, 'a') as writer:
                 self.rss[node], self.last_index[node]['rss'] = self.__check_overflow(self.rss[node], writer, self.last_index[node]['rss'], 'rss')
            filename = "memory-" + str(node) + "vms.csv"
            #print("[Rank ", self.my_rank, "] :","WRITING..", filename) 
            with open(filename, 'a') as writer:
                 self.vms[node], self.last_index[node]['vms'] = self.__check_overflow(self.vms[node], writer, self.last_index[node]['vms'], 'vms')

            streams = list(self.adios2_active_conns[node].keys())
            for stream in streams:
                filename = "memory-" + str(node) + "-" + str(stream.replace('.', '').replace('/', '-')) + "llcp.csv"
                with open(filename, 'a') as writer:
                    self.llcp[node][stream], self.last_index[node][stream]['llc'] = self.__check_overflow(self.llcp[node][stream], writer, self.last_index[node][stream]['llc'], 'llc')
                filename = "memory-" + str(node) + "-" + str(stream.replace('.', '').replace('/', '-')) + "ldsp.csv"
                with open(filename, 'a') as writer:
                    self.ldsp[node][stream], self.last_index[node][stream]['lds'] = self.__check_overflow(self.ldsp[node][stream], writer, self.last_index[node][stream]['lds'], 'lds')
                filename = "memory-" + str(node) + "-" + str(stream.replace('.', '').replace('/', '-')) + "ipc.csv"
                with open(filename, 'a') as writer:
                    self.ipc[node][stream], self.last_index[node][stream]['ipc'] = self.__check_overflow(self.ipc[node][stream], writer, self.last_index[node][stream]['ipc'], 'ipc')
        return   
    

    def get_curr_state(self):
        j_data = {}
        nodes = self.adios2_active_conns.keys()
        for node in nodes:
            j_data[node] = {}
            j_data[node]['RSS'] = self.m_status_rss_max[node][-1] 
            j_data[node]['VMS'] = self.m_status_vms_max[node][-1] 
            j_data[node]['LLC'] = {}
            j_data[node]['LDS'] = {}
            j_data[node]['IPC'] = {}
            streams = list(self.adios2_active_conns[node].keys())
            for stream in streams:
                if len(self.m_status_llcp_inc[node][stream]) == 0:
                    j_data[node]['LLC'][stream] = []
                else:  
                    j_data[node]['LLC'][stream] = self.m_status_llcp_inc[node][stream][-1] 
                if len(self.m_status_ldsp_inc[node][stream]) == 0:
                    j_data[node]['LDS'][stream] = []
                else:  
                    j_data[node]['LDS'][stream] = self.m_status_ldsp_inc[node][stream][-1] 
                if len(self.m_status_ipc_dec[node][stream]) == 0:
                    j_data[node]['IPC'][stream] = []
                else:  
                    j_data[node]['IPC'][stream] = self.m_status_ipc_dec[node][stream][-1] 
        return j_data  
