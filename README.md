# Dynamic_workflow_management

To install

```
git clone https://github.com/swatisgupta/Dynamic_workflow_management.git
cd Dynamic_workflow_management
python3 -m venv rmonitor
source rmonitor/bin/activate
pip3 install --editable .
```

Example:
Define a resource map as
```
cat ex_json.js
{ 
  "node" : [ { "name" : "n0" , 
             "mapping" : [ {"stream_nm" : "tau-metrics.bp", "ranks" : ["0", "1"] }]
             } ] 
}
```

Run the runtime monitoring demon as:
```
python3 r_monitor --bind_inport 8085 --bind_outaddr 10.103.128.13 --bind_outport 8080 --adios2_streams tau-metrics.bp  --adios2_stream_eng SST --rmap_file ex_json.js --tau_one_file=False --tau_file_type="trace" --memory 
```

Run the decision component as:
```
python3 runtime_monitor/decision_temp.py
```
