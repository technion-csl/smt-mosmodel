#! /usr/bin/env python3

import sys
import os
import time
import subprocess
import shutil
import shlex
from os.path import join, getsize

class BenchmarkRun:
    def __init__(self, benchmark_name, output_directory, benchmarks_root):
        self._benchmarks_root = benchmarks_root
        self._benchmark_name = benchmark_name
        self._assertBenchmarkIsValid()

        self._output_directory = os.getcwd() + '/' + benchmark_name + '/' + output_directory
        if os.path.exists(self._output_directory):
            print('output directory', self._output_directory, 'already exists...')
            self._does_output_directory_exist = True
        else:
            print('creating a new output directory', self._output_directory, '...')
            self._createNewRunDirectory(self._output_directory)
            self._does_output_directory_exist = False

        log_file_name = self._output_directory + '/benchmark.log'
        self._log_file = open(log_file_name, 'w')

    def __del__(self):
        if hasattr(self, "_log_file"):
            self._log_file.close()

    def _assertBenchmarkIsValid(self):
        self._benchmark_dir = self._benchmarks_root + '/' + self._benchmark_name
        error_string = 'Error: the benchmark ' + self._benchmark_name + ' was not found.\n' + \
                'Did you spell it correctly?'
        if not os.path.exists(self._benchmark_dir):
            sys.exit(error_string)

    def _createNewRunDirectory(self, new_output_directory):
        # the output directory is prefixed to the benchmark name
        print('copying the benchmark files to ' + new_output_directory + '...')
        # symlinks are copied as symlinks with symlinks=True
        shutil.copytree(self._benchmark_dir, new_output_directory, symlinks=True)

    def doesOutputDirectoryExist(self):
        return self._does_output_directory_exist

    def warmup(self):
        print('warming up before running...')
        os.chdir(self._output_directory)
        # the warmup script will read input files to force them to reside
        # in the page-cache before run() is invoked.
        subprocess.check_call('./warmup.sh', stdout=self._log_file, stderr=self._log_file)

    def run(self, num_threads, submit_command):
        print('running the benchmark ' + self._benchmark_name + '...')
        print('the full submit command is:\n\t' + submit_command + ' ./run.sh')
        environment_variables = {"OMP_NUM_THREADS": str(num_threads),
                "OMP_THREAD_LIMIT": str(num_threads)}
        environment_variables.update(os.environ)
        os.chdir(self._output_directory)
        self._run_process = subprocess.Popen(shlex.split(submit_command + ' ./run.sh'),
                stdout=self._log_file, stderr=self._log_file, env=environment_variables)

    def wait(self):
        print('waiting for the run to complete...')
        self._run_process.wait()
        if self._run_process.returncode != 0:
            raise subprocess.CalledProcessError(self._run_process.returncode, ' '.join(self._run_process.args))
        print('sleeping a bit to let the filesystem recover...')
        time.sleep(5) # seconds

    def validate(self):
        print('validating the run outputs...')
        os.chdir(self._output_directory)
        subprocess.check_call('./validate.sh', stdout=self._log_file, stderr=self._log_file)

    def clean(self, exclude_files=[], threshold=1024*1024):
        print('cleaning large files from the output directory...')
        for root, dirs, files in os.walk('./'):
            for name in files:
                file_path = join(root, name)
                # remove files larger than threshold (default is 1MB)
                if getsize(file_path) > threshold and name not in exclude_files:
                    os.remove(file_path)
        print('syncing to clean all pending I/O activity...')
        os.sync()

import argparse
def getCommandLineArguements():
    parser = argparse.ArgumentParser(description='This python script runs a single benchmark, \
            possibly with a prefixing submit command like \"perf stat --\". \
            The script creates a new output directory in the current working directory, \
            copy the benchmark files there, and then warmup, run, and validate the benchmark. \
            Finally, the script deletes large files (> 1MB) residing in the output directory.')
    parser.add_argument('-n', '--num_threads', type=int, default=4,
            help='the number of threads (for multi-threaded benchmarks)')
    parser.add_argument('-s', '--submit_command', type=str, default='',
            help='a command that will prefix running the benchmark, e.g., "perf stat --".')
    parser.add_argument('-x', '--exclude_files', type=str, nargs='*', default=[],
            help='list of files to not remove')
    parser.add_argument('-r', '--repeats', type=int, default=1,
                    help='the number of repeated runs')
    parser.add_argument('benchmark_name', type=str)
    args = parser.parse_args()
    return args

def findBenchmarksRoot():
    benchmarks_root = sys.path[0]
    # override benchmarks_root if supplied by an environment variable
    environment_variables = dict(os.environ)
    if 'BENCHMARKS_ROOT' in environment_variables:
        benchmarks_root = environment_variables['BENCHMARKS_ROOT']
    error_string = 'Error: the benchmarks root ' + benchmarks_root + ' was not found.\n' + \
            'The directory search path is (in the following order):\n' + \
            '(1) the BENCHMARKS_ROOT environment variable.\n' + \
            '(2) the directory containing this script, i.e., ' + sys.path[0]
    if not os.path.exists(benchmarks_root):
        sys.exit(error_string)
    return benchmarks_root

if __name__ == "__main__":
    args = getCommandLineArguements()
    benchmarks_root = findBenchmarksRoot()

    repeated_runs = [BenchmarkRun(args.benchmark_name, 'repeat'+str(i), benchmarks_root)
            for i in range(args.repeats)]
    for run in repeated_runs:
        if run.doesOutputDirectoryExist():
            continue # skip existing directories
        else:
            run.warmup()
            run.run(args.num_threads, args.submit_command)
            run.wait()
            run.validate()
            run.clean(args.exclude_files)

