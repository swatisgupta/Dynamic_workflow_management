#
# This example illustrates the format of a Cheetah configuration file
#
from codar.cheetah import Campaign
from codar.cheetah import parameters as p

class HeatTransfer(Campaign):
    """Small example to run the heat_transfer application with heatAnalysis_write,
    using no compression, zfp, or sz. All other options are fixed, so there
    are only three runs."""

    name = "heat2d-simple"

    # This applications consists of two codes, with nicknames "heat" and
    # "heatAnalysis", exe locations as specified, and a delay of 5 seconds
    # between starting heatAnalysis and heat.
    codes = [('heatAnalysis', dict(exe="heatAnalysis", sleep_after=5)),
             ('heatSimulation', dict(exe="heatSimulation", sleep_after=0,
                           adios_xml_file="adios2.xml"))]

    # The application is designed to run on two machines.
    # (These are magic strings known to Cheetah.)
    supported_machines = ['local', 'titan']

    # Inputs are copied to each "run directory" -- directory created by
    # Cheetah for each run. The adios_xml_file for each code specified
    # above is included automatically, so does not need to be specified
    # here.
    inputs = []

    # If the heat or heatAnalysis code fails (nonzero exit code) during a run,
    # kill the other code if still running. This is useful for multi-code
    # apps that require all codes to complete for useful results. This
    # is usually the case when using an adios heatAnalysis code.
    kill_on_partial_failure = False

    # Options to pass to the scheduler (PBS or slurm). These are set per
    # target machine, since likely different options will be needed for
    # each.
    scheduler_options = {
        "titan": { "project": "CSC143",
                   "queue": "debug" }
    }

    app_config_scripts = {
	'titan': None,
        'local': 'mac_config.sh',
    }

    sweeps = [

     # Each SweepGroup specifies a set of runs to be performed on a
     # fixed number of nodes, determined based on the target machine and
     # the requirements of each run within the group. Here we have 1
     # SweepGroup, which will run on 4 nodes on titan.
     # On titan each executable consumes an entire node, even if it
     # doesn't make use of all processes on the node, so this will run
     # the first two instances at the same time across four nodes, and
     # start the last instance as soon as one of those two instances
     # finish. On a supercomputer without this limitation, with nodes
     # that have >14 processes, all three could be submitted at the same
     # time with one node unused.
     p.SweepGroup("small_scale",
                  walltime=1860,# Required. Set walltime for scheduler job.
                  per_run_timeout=600,
                                # Optional. If set, each run in the sweep
                                # group will be killed if not complete
                                # after this many seconds.
                  max_procs=10, # Optional. Set max number of processes to run
                                # in parallel. Must fit on the nodes
                                # specified for each target machine, and
                                # each run in the sweep group must use no
                                # more then this number of processes. If
                                # not specified, will be set to the max
                                # of any individual run. Can be used to
                                # do runs in parallel, i.e. setting to 28
                                # for this experiment will allow two runs
                                # at a time, since 28/14=2.
      # Within a SweepGroup, each parameter_group specifies arguments for
      # each of the parameters required for each code. Number of runs is the
      # product of the number of options specified. Below, it is 3, as only
      # one parameter has >1 arguments. There are two types of parameters
      # used below: system ("ParamRunner") and positional command line
      # arguments (ParamCmdLineArg). Also supported: command line options
      # (ParamCmdLineOption), ADIOS XML config file (ParamAdiosXML)

      parameter_groups=
      [p.Sweep([

        # First, the parameters for the ANALYSIS program

        # ParamRunner passes an argument to launch_multi_swift
        # nprocs: Number of processors (aka process) to use
        p.ParamRunner("heatAnalysis", "nprocs", 
                      lambda d: d["heatAnalysis"]["N"] * d["heatAnalysis"]["M"]),

        # ParamCmdLineArg passes a positional argument to the application
        # Arguments are:
          # 1) Code name (e.g., "heatAnalysis"),
          # 2) Logical name for parameter, used in output;
          # 3) positional argument number;
          # 4) options
        p.ParamCmdLineArg("heatAnalysis", "input", 1, ["sim.bp"]),
        p.ParamCmdLineArg("heatAnalysis", "output", 2, ["heat_res.bp"]),
        p.ParamCmdLineArg("heatAnalysis", "N", 3, [1]),
        p.ParamCmdLineArg("heatAnalysis", "M", 4, [1]),
        
       # Second, the parameters for the SIMULATION program

        # Parameters that are derived from other explicit parameters can be
        # specified as a function taking a dict of the other parameters
        # as input and returning the value.
        p.ParamRunner("heatSimulation", "nprocs",
                      lambda d: d["heatSimulation"]["N"] * d["heatSimulation"]["M"]),
        p.ParamCmdLineArg("heatSimulation", "output", 1, ["sim.bp"]),
        p.ParamCmdLineArg("heatSimulation", "N", 2, [2]),
        p.ParamCmdLineArg("heatSimulation", "M", 3, [1]),
        p.ParamCmdLineArg("heatSimulation", "nx", 4, [40]),
        p.ParamCmdLineArg("heatSimulation", "ny", 5, [50]),
        p.ParamCmdLineArg("heatSimulation", "steps", 6, [100000]),
        p.ParamCmdLineArg("heatSimulation", "iterations", 7, [100000]),
      ]),
     ]),
    ]
