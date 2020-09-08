#tau_reader_test.py
# Inputs: 
# stream name 
# Comma separated list of processes(writer) to read data for
# Comma separated list of threads(writer) to read data for 
# Adios engine to use
# Tau file type : trace or profile
# Comma separated list of metrics to read 

#trace
jsrun -n 1 python3 ./tau_reader_test.py tau-metrics-stream_mpi3.bp "0,2" "0,1" BP4 trace "pthread_create,pthread_join"

#profile
jsrun -n 1 python3 ./tau_reader_test.py tauprofile-stream_mpi3.bp "0,2" "0,1" BP4 profile "pthread_create,pthread_join"
