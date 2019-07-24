#!/usr/bin/python
import json
import os
import string

def dynamic_control_signals():
    """check for dynamic control signals and take steps accordingly"""
    path='/lustre/atlas/scratch/ssinghal/csc143/cheetah/dynamic_control.json'
    _done_all = False
    while _done_all == False:
        if os.path.isfile(path) == True:
            line=''
            with open(path, "r+") as f:
                line = f.readline()
                print(str(line))
                f.truncate()

                if line != '':
                    jstring = json.loads(str(line))
                    pid = jstring["add"]["pipeId"]
                    run_name = jstring["add"]["run_name"]
                    print("Received a request to add new stage write process to pipeline "+ str(pid) +"\n")
                    #consumer.kill_and_add(pid, run_name)
                    _done_all = True


if __name__=='__main__':
    dynamic_control_signals()
