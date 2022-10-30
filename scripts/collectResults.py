#! /usr/bin/env python3

import sys
import numpy as np
import pandas as pd

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--experiments_root', default='experiments/',
                    help='the directory containing results in a tree of layout/repeat')
parser.add_argument('-l', '--layouts', required=False, default=None,
                    help='a comma-separated list of layouts')
parser.add_argument('-i', '--instruction_count', type=str,
                    help='the number of instructions in the 4KB layout')
parser.add_argument('-o', '--output_dir', required=True,
                    help='the directory for all output files')
args = parser.parse_args()

import os
layout_list = []
if args.layouts == None:
    for f in os.scandir(args.experiments_root):
        if f.is_dir() and f.name.startswith('layout') and not f.name == 'layouts':
            layout_list.append(f.name)
    if layout_list == []:
        print('layouts argument is empty, skipping...')
        sys.exit(0)
else:
    if args.layouts.replace(' ', '') == '':
        print('layouts argument is empty, skipping...')
        sys.exit(0)

    try:
        layout_list = args.layouts.strip().split(',')
    except KeyError:
        sys.exit('Error: could not parse the --layouts argument')

# build the output directory
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
output_dir = args.output_dir + '/'

with open(args.instruction_count) as f:
    instruction_count = int(next(f))

results = []
for layout in layout_list:
    perf_file = args.experiments_root + '/' + layout + '/1/repeat0/perf.time'
    df = pd.read_csv(perf_file, delimiter=',', index_col='time')
    metrics = list(df.columns)
    df = df.cumsum('columns')
    last_time = np.interp(instruction_count, df['instructions'], df.index)
    stats = [np.interp(last_time, df.index, df[m]) for m in metrics]
    results.append([layout] + stats)

df = pd.DataFrame(results, columns=['layout']+metrics)

df.to_csv(output_dir + 'mean.csv', na_rep='NaN')

