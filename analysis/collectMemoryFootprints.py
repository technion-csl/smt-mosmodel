#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd
import argparse
import glob

parser = argparse.ArgumentParser()
parser.add_argument('experiments_root')
parser.add_argument('-b', '--benchmarks', required=True,
                    help='a comma-separated list of benchmarks')
parser.add_argument('-o', '--output', default='memory_footprints.csv')
args = parser.parse_args()

try:
    benchmark_list = args.benchmarks.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --benchmarks argument')

def roundToBase(x, base):
        return base * round(x/base)

mb_size = 1024*1024
gb_size = mb_size*1024
BASE_PAGE_SIZE = 4096
# mosalloc_hpbrs_sizes structure:
# region, max-size
# brk, <brk-max-size>
# anon-mmap, <annon-mmap-max-size>
# file-mmap, <file-mmap-max-size>
data_frame = pd.DataFrame(columns=['benchmark', 'brk', 'anon-mmap', 'file-mmap'])
df_cols = ['benchmark', 'brk', 'anon-mmap', 'file-mmap']
for i, benchmark in enumerate(benchmark_list):
    path = args.experiments_root + '/' + benchmark + '/repeat0'
    allFiles = glob.glob(path + "/mosalloc_hpbrs_sizes*.csv")
    for f in allFiles:
        df = pd.read_csv(f, index_col=False)
        brk = int(df.query('region == "brk"').iloc[0]['max-size'].astype(int))
        anon_mmap = int(df.query('region == "anon-mmap"').iloc[0]['max-size'].astype(int))
        file_mmap = int(df.query('region == "file-mmap"').iloc[0]['max-size'].astype(int))
        # Add 100MB to the memory footprint or 5% of the pool size (the minimum between them)
        brk = int(max(brk+100*mb_size, brk*1.02))
        brk = roundToBase(brk, BASE_PAGE_SIZE)
        anon_mmap = int(max(anon_mmap+20*mb_size, anon_mmap*1.02))
        anon_mmap = roundToBase(anon_mmap, BASE_PAGE_SIZE)
        data_frame = data_frame.append(pd.DataFrame(
                [[benchmark, brk, anon_mmap, file_mmap]], columns=df_cols))

#regions_sum = data_frame.groupby('benchmark', sort=False).sum().add(10*mb_size).reset_index()
regions_sum = data_frame.groupby('benchmark', sort=False).sum().reset_index()
regions_sum.columns = [['benchmark', 'brk-sum', 'anon-mmap-sum', 'file-mmap-sum']]
#regions_max = data_frame.groupby('benchmark', sort=False).max().add(10*mb_size).reset_index()
regions_max = data_frame.groupby('benchmark', sort=False).max().reset_index()
regions_max.columns = [['benchmark', 'brk-max', 'anon-mmap-max', 'file-mmap-max']]

out_df = regions_sum.merge(regions_max)
out_df.to_csv(args.output, index=False)

