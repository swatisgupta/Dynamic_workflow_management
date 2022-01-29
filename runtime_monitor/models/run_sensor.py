

rm -rf t1 t2 t3

rm -rf *.csv output

mkdir t1
mkdir t2

#mpirun -n 1 python sensor.py 1 simulation/tau_metrics_xgc1.bp 48 > output
#mv *.csv output t1

#mpirun -n 2 python sensor.py 1 simulation/tau_metrics_xgc1.bp 48 > output
mpirun -n 2 python memory_model.py 1 simulation/tau_metrics_xgc1.bp 48 > output
mv *.csv output t2

#mpirun -n 3 python sensor.py 1 simulation/tau_metrics_xgc1.bp 48 > output 
#mv *.csv output t3
