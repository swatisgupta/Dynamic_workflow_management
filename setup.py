#!/usr/bin/env python3

import os
import sys
from setuptools import setup, find_packages

setup(name='runtime_monitor',
      version='0.1.0',
      description='CODAR Experiment Harness',
      long_description=open('README.md').read(),
      url='https://github.com/swatisgupta/Dynamic_workflow_management.git',
      packages=find_packages(),
      scripts=['r_monitor'],
      install_requires=["numpy", "mpi4py", "pyzmq"],
      )
