#! /usr/bin/env python3

import numpy as np
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from performance_statistics import PerformanceStatistics

def loadDataframe(mean_file):
    mean_ps = PerformanceStatistics(mean_file)
    mean_df = mean_ps.getDataFrame()
    mean_df['walk_cycles'] = mean_ps.getWalkDuration()
    mean_df['cpu-cycles'] = mean_ps.getRuntime()
    mean_df['stlb_misses'] = mean_ps.getStlbMisses()
    mean_df['stlb_hits'] = mean_ps.getStlbHits()
    df = mean_df[['walk_cycles', 'stlb_misses', 'stlb_hits', 'cpu-cycles']]

    return df

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--root_dir', default='analysis/unified_windows',
                    help='the root directory which contains the mean files of the given benchmarks')
parser.add_argument('-b', '--benchmarks', required=True,
                    help='a comma-separated list of benchmarks')
parser.add_argument('-m', '--mean_file_name', default='mean.csv',
                    help='the name of the mean file to be read from the root directory for each benchmark')
parser.add_argument('-o', '--output',  default='r_squares.csv')
args = parser.parse_args()

try:
    benchmark_list = args.benchmarks.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --benchmarks argument')

from sklearn.linear_model import LinearRegression
res_df = pd.DataFrame(columns=['C', 'M', 'H'], index=benchmark_list)
for benchmark in benchmark_list:
    df = loadDataframe(args.root_dir + '/' + benchmark + '/' + args.mean_file_name)

    linear_regressor = LinearRegression(fit_intercept=True)
    
    linear_regressor.fit(df[['walk_cycles']], df['cpu-cycles'])
    walk_cycles_r_squared = linear_regressor.score(df[['walk_cycles']], df['cpu-cycles'])

    linear_regressor.fit(df[['stlb_misses']], df['cpu-cycles'])
    tlb_misses_r_squared = linear_regressor.score(df[['stlb_misses']], df['cpu-cycles'])

    linear_regressor.fit(df[['stlb_hits']], df['cpu-cycles'])
    tlb_hits_r_squared = linear_regressor.score(df[['stlb_hits']], df['cpu-cycles'])

    res_df.loc[benchmark] = {
            'C' : walk_cycles_r_squared,
            'M' : tlb_misses_r_squared,
            'H' : tlb_hits_r_squared}

import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from shortenBenchmarkName import shortenBenchmarkName
benchmark_list = [shortenBenchmarkName(b) for b in benchmark_list]
res_df.index = benchmark_list

res_df.to_csv(args.output, index_label='benchmark', float_format='%.3f')
