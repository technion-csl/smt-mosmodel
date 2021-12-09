#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *

import math
def writeLayoutAll2mb(layout, output):
    page_size = 1 << 21
    brk_pool_size = round_up(brk_footprint, page_size)
    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_pool_size,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    configuration.addWindow(
            type=configuration.TYPE_BRK,
            page_size=page_size,
            start_offset=0,
            end_offset=brk_pool_size)
    configuration.exportToCSV(output, layout)

def writeLayout(layout, windows, output):
    page_size = 1 << 21
    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_footprint,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    for w in windows:
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=page_size,
                start_offset=w * page_size,
                end_offset=(w+1) * page_size)
    configuration.exportToCSV(output, layout)

def buildGroups(pebs_df, layouts_dir):
    threshold = 60
    total_weight = 0
    pebs_df.sort_values('NUM_ACCESSES', ascending=False, inplace=True)
    groups = []
    current_group = []
    current_total_weight = 0
    i = 0
    desired_weights = [30, 20, 10]
    for index, row in pebs_df.iterrows():
        page_number = int(row['PAGE_NUMBER'])
        weight = row['NUM_ACCESSES']
        if current_total_weight >= desired_weights[i]:
            groups.append(current_group)
            current_group = []
            current_total_weight = 0
            i += 1
        if i == len(desired_weights):
            break
        if current_total_weight < desired_weights[i]:
            current_total_weight += weight
            current_group.append(page_number)
    return groups

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-p', '--pebs_mem_bins', default='mem_bins_2mb.csv')
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--layouts_dir', required=True)
args = parser.parse_args()

import pandas as pd
# read memory-footprints
footprint_pebs_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_pebs_df['anon-mmap-max'][0]
brk_footprint = footprint_pebs_df['brk-max'][0]

# read mem-bins
pebs_df = pd.read_csv(args.pebs_mem_bins, delimiter=',')
#pebs_df['PAGE_NUMBER'] = pebs_df['PAGE_NUMBER'].astype(int)

pebs_df = pebs_df[pebs_df['PAGE_TYPE'].str.contains('brk')]
if pebs_df.empty:
    sys.exit('Input file does not contain page accesses information about the brk pool!')
pebs_df = pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
pebs_df = pebs_df.reset_index()

# transform NUM_ACCESSES from absolute number to percentage
total_access = pebs_df['NUM_ACCESSES'].sum()
pebs_df['NUM_ACCESSES'] = pebs_df['NUM_ACCESSES'].mul(100).divide(total_access)
pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)

import itertools
if args.layout == 'layout1':
    i = 1
    groups = buildGroups(pebs_df, args.layouts_dir)
    for subset_size in range(len(groups)+1):
        for subset in itertools.combinations(groups, subset_size):
            windows = []
            for l in subset:
                windows += l
            layout_name = 'layout' + str(i)
            i += 1
            print(layout_name)
            print('#hugepages: '+ str(len(windows)))
            print('hugepages: ' + str(windows))
            print('---------------')
            writeLayout(layout_name, windows, args.layouts_dir)
    writeLayoutAll2mb('layout'+str(i), args.layouts_dir)
else:
    sys.exit(args.layout + ' is not supported yet!')
