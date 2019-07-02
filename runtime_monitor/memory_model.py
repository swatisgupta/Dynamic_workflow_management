import helper
import json
from collections import deque
import abstract_model
from functools import partial
from pandas.tseries.frequencies import to_offset
from pandas import Timestamp
import datetime as dt
import numpy
import pandas as pd
from collections import Counter

likwid_counters = {}

papi_counters = {}
papi_counters['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'] = []
papi_counters['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'].append({
              'llc_misses': 'PAPI_NATIVE_LAST_LEVEL_CACHE_MISSES',
              'llc_refs': 'PAPI_NATIVE_LAST_LEVEL_CACHE_REFERENCES',
              'ld_stalls':'PAPI_NATIVE_CYCLE_ACTIVITY:STALLS_LDM_PENDING',
              'ins_ret': 'PAPI_NATIVE_INSTRUCTIONS_RETIRED',
              'st_stalls' : 'PAPI_NATIVE_RESOURCE_STALLS:SB',
              'cpu_cyc' : 'PAPI_NATIVE_ix86arch::UNHALTED_CORE_CYCLES' })

metric = {}
metric['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'] = []
metric['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'].append('llc_miss_per')
metric['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'].append('ld_stalls_per')
metric['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'].append('ipc')

def _fix_ranges_(func, val_l, val_tot):
    if len(val_l) != len(val_tot):
        print(func, " : Length of meaurements donot match!\n", len(val_l), "!=", len(val_tot))
        nlen = min(len(val_l), len(val_tot)) 
        val_l = val_l[:nlen]
        val_tot = val_len[:nlen]
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
                print("Max percenatge is 0 for index " , i, " in ", func)
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
                print("Max division is 0 for index " , i, " in ", func)
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
        self.hd_counters = []
        self.rss_m = "Memory Footprint (VmRSS) (KB)"
        self.vms_m = "Peak Memory Usage Resident Set Size (VmHWM) (KB)"
        self.metric_func = []
        self.adios2_active_conns = []
        self.r_map = None
        self.name = "memory"
        self.m_status_abs = {} 
        self.m_status_avg = {} 
        self.m_status_inc = {} 
        self.m_status_dec = {} 
        self.urgent_update = False
        self.frequency = '1S'
 
        if config.hc_lib  == 'papi':
            hd_counters = papi_counters[config.cpu_model]
            metric_func = metric[config.cpu_model]
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

    def round(t, freq_v):
        freq = to_offset(freq_v)
        return pd.Timestamp((t.value // freq.delta.value) * freq.delta.value)

    def __group_by_frequency(self, narray, by_last=0): #Replace S with U for microsecond 
        #print(narray)  
        narray_v = narray[:,0] # get the value
        nlist_k = narray[:,1].tolist() #get the timestamp
        nlist_k = self.__timestamp_to_date(nlist_k)

        pdf = pd.DataFrame(data=narray_v, index=nlist_k, columns=["value"])
        #print(pdf)
        if by_last == 0:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).sum()
        else:
            pdf = pdf.groupby(pd.Grouper(freq=self.frequency)).last()
        pdf = pdf["value"].fillna(method='ffill')
        #print(pdf["value"])  
        return pdf.to_dict()

    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update

    def update_model_conf(self, config):
        self.adios2_active_conns = config.adios2_c_objs
        self.r_map = config.local_res_map
        self.procs_per_ctr = config.procs_per_cstr
        self.blocks_to_read = config.blocks_to_read

    def __get_agg_values_for(self, adios_conc, cntr, cntr_map, index, by_last=0, procs=[0], threads=[0]):
        is_valid, val_ar = adios_conc.read_var(cntr, procs, threads)
        if is_valid == True:
            for proc in procs:
                for th in threads:
                    val_tmp = val_ar[proc]
                    tmp_ar = val_tmp[val_tmp[:,0] == th] 
                    if tmp_ar.size != 0:
                        #print(tmp_ar)  
                        tmp_ar = tmp_ar[:,[1,2]]
                        cntr_df = self.__group_by_frequency(tmp_ar, by_last)
                        A = Counter(cntr_map[index])
                        B = Counter(cntr_df) 
                        cntr_map[index]= dict(A + B) 
        return cntr_map

    def update_curr_state(self):
        rss_val = {}
        ''' 
        llcr_val = {} 
        llcm_val = {} 
        lds_val = {} 
        ins_val = {} 
        cyc_val = {}
        ''' 
        k = 0 
        p_ctrs = list(self.blocks_to_read.values())
        keys = list(self.adios2_active_conns.keys()) 
        #print(keys)
        for concs in self.adios2_active_conns.values():
            rss_val[keys[k]] = [] 
            '''
            llcm_val[keys[k]] = [] 
            llcr_val[keys[k]] = [] 
            lds_val[keys[k]] = [] 
            ins_val[keys[k]] = [] 
            cyc_val[keys[k]] = []
            ''' 
            thread_l1 = [0]
            thread_l = [0,1,2,3]
            for conc in concs:
                #read RSS
                rss_val = self.__get_agg_values_for(conc, self.rss_m, rss_val, keys[k], 0, p_ctrs[k], thread_l1)
                '''
                vms_val = self.__get_agg_values_for(conc, self.vms_m, vms_val, keys[k], 0, p_ctrs[k], thread_l1)
                for met in self.metric_func:
                    if met == "ld_stall_per":
                        #read No of Load Stalls
                        lds_val = self.__get_agg_values_for(conc, self.hd_counters['ld_stalls'], lds_val, keys[k], 1, p_ctrs[k], thread_l)
                    else if met == "llc_miss_per":
                        #read No of L3 misses
                        llcm_val = self.__get_agg_values_for(conc, self.hd_counters['llc_misses'], llcm_val, keys[k], 1, p_ctrs[k], thread_l)
                        #read No of L3 references
                        llcr_val = self.__get_agg_values_for(conc, self.hd_counters['llc_refs'], llcr_val, keys[k], 1, p_ctrs[k], thread_l)
                    else if met == "ipc":
                        #read No of Instruction
                        ins_val = self.__get_agg_values_for(conc, self.hd_counters['inst_ret'], ins_val, keys[k], 1, p_ctrs[k], thread_l)
                    if met == "ld_stalls_per" or met == "ipc":
                        #read No of CPU cycles
                        cyc_val = self.__get_agg_values_for(conc, self.hd_counters['cpu_cyc'], cyc_val, keys[k], 1, p_ctrs[k], thread_l)
                '''
            k = k + 1    
        print("RSS val", rss_val)
        return True

    def get_curr_state(self):
        j_data = {}
        print("To be implemented \n");
        return j_data  
