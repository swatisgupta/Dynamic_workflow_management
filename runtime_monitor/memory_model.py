import helper
import json
from collections import deque
import abstract_model

likwid_counters = {}

papi_counters = {}
papi_counters['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'] = []
papi_counters['Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz'].append({
              'llc_misses': 'PAPI_NATIVE_LAST_LEVEL_CACHE_MISSES',
              'llc_refs': 'PAPI_NATIVE_LAST_LEVEL_CACHE_REFERENCES',
              'ld_stalls':'PAPI_NATIVE_CYCLE_ACTIVITY:STALLS_LDM_PENDING',
              'ins_ret': 'PAPI_NATIVE_INSTRUCTIONS_RETIRED',
              'st_stalls' : 'PAPI_NATIVE_RESOURCE_STALLS:SB',
              'core_cyc' : 'PAPI_NATIVE_ix86arch::UNHALTED_CORE_CYCLES' })

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
        self.rss_m = ['Memory Footprint (VmRSS) (KB)']
        self.vmswaps_m = ['Peak Memory Usage Resident Set Size (VmHWM) (KB)']
        self.metric_func = []
        self.adios2_active_conns = []
        self.r_map = None
        self.name = "memory"
        self.m_status_abs = {} 
        self.m_status_avg = {} 
        self.m_status_inc = {} 
        self.m_status_dec = {} 
        self.urgent_update = False

        if config.hc_lib  == 'papi':
            hd_counters = papi_counters[config.cpu_model]
            metric_func = metric[config.cpu_model]
        self.refresh_model_conf(config)    

    def __compute_llc_miss_per(self, nprocs, llc_miss, llc_refs):
        llc_per, maxp = _percentage_('compute_llc_miss_per', nprocs, llc_miss, llc_refs)
        return llc_per
 
    def __compute_ld_stalls_per(self, nprocs, ld_stalls, core_cyc): 
        lds_per, maxp = _percentage_('compute_ld_stalls_per', nprocs, ld_stalls, core_cyc)
        return lds_per
        
    def __compute_ipc(self, nprocs, ins_ret, core_cyc): 
        ipc, maxv = _divide_('compute_ipc', nprocs, ins_ret, core_cyc)
        return ipc


    def get_model_name(self):
        return self.name

    def if_urgent_update(self):
        return self.urgent_update

    def refresh_model_conf(self, config):
        self.adios2_active_conns = config.adios2_c_objs
        self.r_map = config.local_res_map
        self.procs_per_ctr= config.procs_per_cstr

    def update_curr_state(self):
        rss_all = None
        k = 0 
        p_ctrs = list(self.procs_per_ctr.values())
        for concs in self.adios2_active_conns.values():
            i = 0
            for conc in concs:
                is_valid, rss_temp = conc.read_var(self.rss_m[0], [0]) 
                #print(rss_temp) 
                if is_valid == True and rss_all is None:
                    rss_all = rss_temp
                elif is_valid == True :
                    #print(rss_temp)
                    rss_all[p_ctrs[k][i]] = rss_temp[0]
                i = i + 1 
            k = k + 1    
        print("RSS", rss_all)
        return True

    def get_curr_state(self):
        j_data = {}
        print("To be implemented \n");
        return j_data  
