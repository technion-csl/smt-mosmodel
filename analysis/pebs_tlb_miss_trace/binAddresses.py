#! /usr/bin/env python3

import sys
import pandas as pd
import numpy as np
import datetime

def writeDataframeToCsv(df, file_name):
    df.to_csv(file_name, na_rep='NaN', index=False)

def getAddress(strAddr):
    try:
        return int(strAddr, 16)
    except Exception:
        return 0

def applyBins(df, pid, bin_width,
        anon_start, anon_end, brk_start, brk_end, file_start, file_end):
    anon_mask = (df['PID'] == pid) & (df['ADDR'] >= anon_start) & (df['ADDR'] < anon_end)
    brk_mask = (df['PID'] == pid) & (df['ADDR'] >= brk_start) & (df['ADDR'] < brk_end)
    file_mask = (df['PID'] == pid) & (df['ADDR'] >= file_start) & (df['ADDR'] < file_end)
    df.loc[anon_mask, 'ADDR'] -= anon_start
    df.loc[anon_mask, 'ADDR'] /= bin_width
    df.loc[anon_mask, 'PAGE_TYPE'] = 'anon'
    df.loc[brk_mask, 'ADDR'] -= brk_start
    df.loc[brk_mask, 'ADDR'] /= bin_width
    df.loc[brk_mask, 'PAGE_TYPE'] = 'brk'
    df.loc[file_mask, 'ADDR'] -= file_start
    df.loc[file_mask, 'ADDR'] /= bin_width
    df.loc[file_mask, 'PAGE_TYPE'] = 'file'

import argparse
import sys
import math
parser = argparse.ArgumentParser()
parser.add_argument('-w', '--width', type=int, default=1<<21,
                    help='the bin width')
parser.add_argument('-p', '--pools_range_file', required=True,
                    help='file that contains the pools addresses range')
parser.add_argument('-i', '--input_file', type=argparse.FileType('r'),
                    default=sys.stdin,
                    help='input file that contains "perf mem -D report" results')
parser.add_argument('-o', '--output_file', required=True,
                    help='the output file to write memory accesses according to input file')
args = parser.parse_args()

df = pd.read_csv(args.input_file, delimiter=';',
                 converters={' ADDR': lambda x: getAddress(x)})
df.columns = ['PID', 'TID', 'IP', 'ADDR', 'LOCAL WEIGHT', 'DSRC', 'SYMBOL']
df['NUM_ACCESSES'] = 1
df['PAGE_TYPE'] = 'unkown'
df = df[['PID', 'ADDR','NUM_ACCESSES', 'PAGE_TYPE']]

pools_df=pd.read_csv(args.pools_range_file, index_col='pid')
pids=pools_df.index.values
for pid in pids:
    p=pools_df.loc[pid]
    applyBins(df, pid, args.width,
            getAddress(p['anon-mmap-start']), getAddress(p['anon-mmap-end']),
            getAddress(p['brk-start']), getAddress(p['brk-end']),
            getAddress(p['file-mmap-start']), getAddress(p['file-mmap-end']))

df['ADDR'] = df['ADDR'].astype(int)
df.columns= ['PID', 'PAGE_NUMBER','NUM_ACCESSES', 'PAGE_TYPE']
df_g=df.groupby(['PID', 'PAGE_NUMBER', 'PAGE_TYPE'], sort=False).size().rename('NUM_ACCESSES').reset_index()
df_g.sort_values('NUM_ACCESSES', ascending=False, inplace=True)

#Write each process results to separate file and plot it
for pid in pids:
    df_g_pid = df_g[df_g['PID']==pid]
    output_file = args.output_file + '.' + str(pid)
    writeDataframeToCsv(df_g_pid, output_file)

df_g = df_g[['PAGE_NUMBER','NUM_ACCESSES', 'PAGE_TYPE']]
df_g=df_g.groupby(['PAGE_NUMBER', 'PAGE_TYPE'], sort=False).sum().reset_index()
df_g.sort_values('NUM_ACCESSES', ascending=False, inplace=True)
#Write all processes data to single file
writeDataframeToCsv(df_g, args.output_file)
