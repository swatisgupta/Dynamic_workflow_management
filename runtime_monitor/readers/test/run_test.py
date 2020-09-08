#trace
jsrun -n 1 python3 ./test.py tau-metrics-stream_mpi3.bp "0,2" "0,1" BP4 trace "pthread_create,pthread_join"

#profile
jsrun -n 1 python3 ./test.py tauprofile-stream_mpi3.bp "0,2" "0,1" BP4 profile "pthread_create,pthread_join"
