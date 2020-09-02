#! /usr/bin/env python3

import numpy as np
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from performance_statistics import PerformanceStatistics

def loadDataframe(mean_file):
    mean_ps = PerformanceStatistics(mean_file, index_col='benchmark')
    mean_df = mean_ps.getDataFrame()
    mean_df['walk_cycles'] = mean_ps.getWalkDuration()
    mean_df['cpu-cycles'] = mean_ps.getRuntime()
    mean_df['stlb_hits'] = mean_ps.getStlbHits()
    mean_df['stlb_misses'] = mean_ps.getStlbMisses()
    df = mean_df[['walk_cycles', 'stlb_hits', 'stlb_misses', 'cpu-cycles']]

    return df

def calculateBasuCoeffs(benchmark, df):
    '''
    Basu_runtime = A * TLB_MISSES + B
    A = PAGE_WALK_LATENCY / TLB_MISSES
    B = 4kb_runtime - PAGE_WALK_LATENCY
    '''
    runtime = df.loc[benchmark]['cpu-cycles']
    walk_latency = df.loc[benchmark]['walk_cycles']
    stlb_misses = df.loc[benchmark]['stlb_misses']
    B = runtime - walk_latency
    A = walk_latency / stlb_misses
    assert(abs(runtime - (A*stlb_misses + B)) < 10)
    return A, B

def calculateAlamCoeffs(benchmark, df):
    '''
    Alam_runtime = PAGE_WALK_LATENCY + B
    B = 2mb_runtime - PAGE_WALK_LATENCY
    '''
    runtime = df.loc[benchmark]['cpu-cycles']
    walk_latency = df.loc[benchmark]['walk_cycles']
    B = runtime - walk_latency
    return B

def calculatePhamCoeffs(benchmark, df):
    '''
    Pham_runtime = 1xDTLB_HITS + 7xSTLB_HITS + PAGE_WALK_LATENCY + B
    DTLB_HITS can be ignored, therefore:
    B = 4kb_runtime - (7xSTLB_HITS + PAGE_WALK_LATENCY)
    '''
    runtime = df.loc[benchmark]['cpu-cycles']
    walk_latency = df.loc[benchmark]['walk_cycles']
    stlb_hits = df.loc[benchmark]['stlb_hits']
    B = runtime - walk_latency - 7*stlb_hits
    return B

def calculateGandhiCoeffs(benchmark, df_2mb, df_4kb):
    '''
    runtime = B + A*stlb_misses
    Where:
    B = runtime[2mb] - walk_cycles[2mb]
    A = walk_cycles / stlb_misses
    '''
    B = df_2mb.loc[benchmark]['cpu-cycles'] - df_2mb.loc[benchmark]['walk_cycles']
    A = df_4kb.loc[benchmark]['walk_cycles'] / df_4kb.loc[benchmark]['stlb_misses']
    return A, B

def calculateYanivCoeffs(benchmark, df_4kb, df_2mb):
    delta_y = df_4kb.loc[benchmark]['cpu-cycles'] - df_2mb.loc[benchmark]['cpu-cycles']
    delta_x = df_4kb.loc[benchmark]['walk_cycles'] - df_2mb.loc[benchmark]['walk_cycles']
    A = delta_y / delta_x
    B = df_4kb.loc[benchmark]['cpu-cycles'] - A * df_4kb.loc[benchmark]['walk_cycles']
    return A,B

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-b', '--benchmarks', required=True,
                    help='a comma-separated list of benchmarks')
#parser.add_argument('-m1gb', '--mean_1gb_file', default='mean_1gb.csv')
parser.add_argument('-m2mb', '--mean_2mb_file', default='mean_2mb.csv')
parser.add_argument('-m4kb', '--mean_4kb_file', default='mean_4kb.csv')
parser.add_argument('-o', '--output',  default='linear_models_coeffs.csv')
args = parser.parse_args()

try:
    benchmark_list = args.benchmarks.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --benchmarks argument')

res_df = pd.DataFrame(columns=[\
        'basu_A', 'basu_B', \
        'alam_B', \
        'pham_B', \
        'gandhi_A', 'gandhi_B', \
        'yaniv_A', 'yaniv_B'], index=benchmark_list)
for benchmark in benchmark_list:
    df_4kb = loadDataframe(args.mean_4kb_file)
    df_2mb = loadDataframe(args.mean_2mb_file)
    basu_A, basu_B = calculateBasuCoeffs(benchmark, df_4kb)
    alam_B = calculateAlamCoeffs(benchmark, df_2mb)
    pham_B = calculatePhamCoeffs(benchmark, df_4kb)
    gandhi_A, gandhi_B = calculateGandhiCoeffs(benchmark, df_2mb, df_4kb)
    yaniv_A, yaniv_B = calculateYanivCoeffs(benchmark, df_4kb, df_2mb)
    res_df.loc[benchmark] = {
            'basu_A': basu_A, 'basu_B':basu_B,
            'alam_B': alam_B,
            'pham_B':pham_B,
            'gandhi_A':gandhi_A, 'gandhi_B':gandhi_B,
            'yaniv_A':yaniv_A, 'yaniv_B':yaniv_B
            }

res_df.to_csv(args.output, index_label='benchmark')


