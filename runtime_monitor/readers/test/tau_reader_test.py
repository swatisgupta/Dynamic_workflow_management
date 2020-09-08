from adios2_tau_reader import adios2_tau_reader
from mpi4py import MPI
import numpy as np
import sys 

def write_to_csv(measure, data_dict):
    if len(data_dict) == 0:
        return
    i = 0
    #print(data_dict.values())
    filename = measure + ".csv"  
    with open(filename, 'a') as writer:
        for k in data_dict.keys():
            np.savetxt(writer, data_dict[k], newline="\n")
            #writer.write("\n") 

if __name__ == "__main__":

    stream = str(sys.argv[1]) # tau-metric stream name (application) to connect..
    #print(stream, flush = True)
    procs = list(str(sys.argv[2]).split(",")) # processes (of this application) that wrote seperate streams on this node.. 
    #print(procs, flush = True)
    threads = list(str(sys.argv[3]).split(",")) # processes (of this application) that wrote seperate streams on this node.. 
    adios2_engine = str(sys.argv[4]) # adios2 engine to use for reading..
    tau_file_type = str(sys.argv[5]) # frequency at which the data needs to be organised (in sec) - minimum value 1..
    metrics = list(str(sys.argv[6]).split(",")) 

    separate_files = True
 
    adios_reader = {}
    adios_reader[stream] = []
    
    # for separate file case....
    if separate_files == True:
        for proc in procs:
            str_split = stream.split('.bp')
            con_str = str_split[0] + "-" + str(proc) + ".bp"
            reader_obj = adios2_tau_reader(con_str, adios2_engine, MPI.COMM_WORLD, [0], tau_file_type)
            adios_reader[stream].append(reader_obj)
    else: 
            reader_obj = adios2_tau_reader(stream, adios2_engine, MPI.COMM_WORLD, [0], tau_file_type)
            adios_reader[stream].append(reader_obj)

    reader_objs = adios_reader[stream]
    
    done = 0

    print("Opening files/streams... ", flush = True)
    for reader_ob in reader_objs:
        reader_ob.open()

    print("Reading data... ", flush = True)
    while done == False: 
        done = True
        for reader_ob in reader_objs:
            ret = reader_ob.advance_step()
            if ret == True:
               done = False

        data = None
        if done == False:
            for reader_ob in reader_objs:
                for metr in metrics:
                    if separate_files == False:
                        is_valid, data = reader_ob.read_var(metr, procs, threads)
                    else: 
                        is_valid, data = reader_ob.read_var(metr, [0] , threads)

                    if is_valid == True:
                        write_to_csv(metr, data)
  
            for reader_ob in reader_objs:
               reader_ob.end_step()

    print("Closing files/streams... ", flush = True)
    for reader_ob in reader_objs:
        reader_ob.close()
