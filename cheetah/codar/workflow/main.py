"""Main program for executing workflow script with different producers and
runners."""

import argparse
import threading
import logging
import signal
import os
import json
import time
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlparse
from urllib.request import urlopen

from codar.workflow.producer import JSONFilePipelineReader
from codar.workflow.consumer import PipelineRunner
from codar.workflow.model import mpiexec, aprun, srun

consumer = None
pipelines = {}
timestamps= {}


def send_control_signal(controlparams):
    filename = controlparams['filename']
    procid = controlparams['procid']
    message_type = int(controlparams['mtype'])
    if timestamps[procid] is None:
        timestamps[procid] = 0
    else:
        x = int(timestamps[procid]) 
        timestamps[procid] = x + 1 
    
    string = procid+":"+timestamps[procid]+":"
 
    with open(filename, 'w') as cntrlf: 
        if message_type == CHNGE_COMPACC:
            message = float(controlparams['mtype'])
            string += "CHNGE_COMPCC:"+message 
            cntrlf.write(string)    
        elif message_type == SWITCH_ENGINE:
            message = controlparams['mtype']
            string += "SWITCH_ENGINE"; 
            cntrlf.write(string);    

        
    
class UserControls(BaseHTTPRequestHandler):

    def _set_headers_json(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def _set_headers_json_204(self):
        self.send_response(204)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def _set_headers_text(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def _set_headers_text_204(self):
        self.send_response(204)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        print(parsed_path)
        response = None
        filename = None
        if parsed_path.query == "":
            curdir = os.path.abspath(os.curdir)
            if parsed_path.path == "/":
                filename = os.path.join('/Users/Swati/Documents/Projects/Dynamic_workflow/cheetah/codar/workflow/', 'default.html')
            else:
                filename = os.path.join('/Users/Swati/Documents/Projects/Dynamic_workflow/cheetah/codar/workflow/', parsed_path.path[1:])
            if os.path.exists(filename) == True:
                self._set_headers_text()
                print("sending the file "+ filename +"\n")
                with open(filename, 'r') as f: 
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self._set_headers_text_204()
        elif parsed_path.query == "q=getstatus":
            if len(consumer._running_pipelines) == 0 and consumer._done_all == False:
                self._set_headers_json()
                response = []
            else:
                self._set_headers_json()
                #response = '{ "header": "Workflow runtime ", "pipelines ": ['
                response = []
                for pipeline in consumer._running_pipelines:
                    response.append(pipeline.to_json())
            print(response)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
           self.do_POST()
  
    def do_POST(self):
        content_len = int(self.headers['Content-Length'])
        print(content_len)
        post_body = self.rfile.read(content_len)
        print(post_body)
        jstring = json.loads(post_body)
        print(jstring)
        request_type = jstring['query'] 
        pid = jstring["pipe"]
        self._set_headers_text()
        comp_name = jstring["comp-name"]
        params={}
        params["run-name"] = jstring["comp-name"]
        params["args"] = jstring["args"]
        params["mprocs"] = jstring["mprocs"]
        if request_type == 'addproc':
            params["command"] = "add_procs"
            print("Received a request to add a process to pipeline "  + str(pid) + " and component " + str(comp_name) + "\n", flush=True)
            if consumer.restart_nprocs(str(pid), params) == 1:
                response = "Added a new process to" + comp_name
            else:
                response = "Sorry, a new process to " + comp_name +" cannot be added"
        elif request_type == 'termproc':
            params["command"] = "term_procs"
            print("Received a request to terminate a process from pipeline "+ str(pid) +" and component " +str(comp_name) + "\n", flush=True)
            if consumer.restart_nprocs(str(pid), params) == 1:
                response = "Terminating a new process to" + comp_name
            else:
                response = "Sorry, a process from " + comp_name +" cannot be terminated"
        elif request_type == 'change_params':
            cotrolparams = {}
            controlparams['procid'] = pipelines[pid].get_pid(jstring["comp-name"])
            controlparams['filename'] = pipelines[pid].get_filename(jstring["comp-name"])
            chng_cmd = jstring["change-command"]

            if  change_cmd == "compress-level":
                controlparams['msgtype'] = 0
            elif change_cmg == "switch-engine":
                controlparams['msgtype'] = 1

            send_control_signals(controlparams)
             
            print("Received a request to change process parameters from pipeline "+ str(pid) +" and component " +str(comp_name) + "\n", flush=True)
            print("Send a signal to process id" + pipelines[pid].get_pid(jstring["comp-name"]) + "\n", flush=True ); 
            response = "Functionality not available"
        else:
            response = "Unknown functionality"
        self.wfile.write(response.encode("utf-8"))


    def do_HEAD(self):
        self._set_headers_text()



def dynamic_controls(server_class=HTTPServer,
    handler_class=UserControls, port=9000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    while len(consumer._running_pipelines) != 0 and consumer._done_all == False:
        httpd.handle_request()


def parse_args():
    parser = argparse.ArgumentParser(description='HPC Worflow script')
    parser.add_argument('--max-nodes', type=int, required=True)
    parser.add_argument('--processes-per-node', type=int, required=True)
    parser.add_argument('--runner', choices=['mpiexec', 'aprun', 'srun',
                                             'none'],
                        required=True)
    parser.add_argument('--producer', choices=['file'], default='file')
    parser.add_argument('--producer-input-file')
    parser.add_argument('--log-file')
    parser.add_argument('--log-level',
                        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
                        default='INFO')
    parser.add_argument('--status-file')

    args = parser.parse_args()

    return args

def write_status():
    path2='/Users/Swati/Documents/Dynamic_workflow/cheetah/runtime_status.txt' 
    
    while len(consumer._running_pipelines) == 0 and consumer._done_all == False:
        continue

    with open(path2, 'w') as stats:
        for pipeline in consumer._running_pipelines:
            stats.write(pipeline.to_String())
            stats.write('\n')

def dynamic_control_signals():
    """check for dynamic control signals and take steps accordingly"""
    path='/Users/Swati/Documents/Dynamic_workflow/cheetah/dynamic_control.json'
    write_status()
    time.sleep(10)
    print("Monitoring the execution..\n", flush=True)
    while consumer._done_all == False:
        if os.path.isfile(path) == True:
            line=''
            with open(path, "r+") as f:
                line = f.readline()
                print(str(line), flush=True)
                f.seek(0,0)
                f.truncate()

            if line != '':
                jstring = json.loads(str(line))
                pid = jstring["add"]["pipeId"]
                run_name = jstring["add"]["run_name"]
                print("Received a request to add new stage write process to pipeline "+ str(pid) +"\n", flush=True)
                consumer.kill_and_add(str(pid), str(run_name))
                write_status()

def main():
    global consumer

    args = parse_args()

    if args.runner == 'mpiexec':
        runner = mpiexec
    elif args.runner == 'aprun':
        runner = aprun
    elif args.runner == 'srun':
        runner = srun
    elif args.runner == 'none':
        runner = None
    else:
        # Note: arg parser should have caught this already
        raise ValueError('Unknown runner: %s' % args.runner)

    logger = logging.getLogger('codar.workflow')
    if args.log_file:
        handler = logging.FileHandler(args.log_file)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(args.log_level)
    else:
        logger.addHandler(logging.NullHandler())

    print(args.max_nodes)
    consumer = PipelineRunner(runner=runner,
                              max_nodes=args.max_nodes,
                              processes_per_node=args.processes_per_node,
                              status_file=args.status_file)

    producer = JSONFilePipelineReader(args.producer_input_file)

    t_consumer = threading.Thread(target=consumer.run_pipelines)
    t_consumer.start()

    # producer runs in this main thread
    for pipeline in producer.read_pipelines():
        consumer.add_pipeline(pipeline)

    # signal that there are no more pipelines and thread should exit
    # when reached
    consumer.stop()
    for pipeline in consumer._running_pipelines:
         pipelines[pipeline.name] = pipeline

    dynamic_controls()

    #Recieve signal from the user if dynamic changes are required???
    # if some signal is received...do 	
    # signal_file = Path(args.producer_signal_file)
    # while not signal_file.is_file():
    #
    # signaler = JSONFileSignalReader(args.producer_input_file)
    
    # set up signal handlers for graceful exit
    def handle_signal_kill_consumer(signum, frame):
        consumer.kill_all()

    signal.signal(signal.SIGTERM, handle_signal_kill_consumer)
    signal.signal(signal.SIGINT,  handle_signal_kill_consumer)

    # All threads created for workflow are non-daemon, so the
    # interpreter will not exit until all threads exit. Doing an
    # explicit join on the consumer thread is not necessary, and
    # actually causes problems because Python can't handle signals if
    # the main thread is in a join, since that is basically pure C code
    # (pthread_join).
