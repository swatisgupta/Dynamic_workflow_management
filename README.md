# Dynamic_workflow_management

Example:
Define a resource map as
```
cat ex_json.js
{ 
  "node" : [ { "name" : "n0" , 
             "mapping" : [ {"c_str" : "tau-metrics.bp", "ranks" : ["0", "1"] }]
             } ] 
}
```

Run the runtime monitoring demon as:
```
python3 runtime_monitor.py --bind_inport 8085 --bind_outaddr 10.103.128.13 --bind_outport 8080 --adios2_conn_str tau-metrics.bp  --adios2_conn_eng SST --rmap_file ex_json.js --tau_one_file=False --tau_file_type="trace" --memory 
```

Run the decision component as:
```
python3 ./decision_temp.py
```
