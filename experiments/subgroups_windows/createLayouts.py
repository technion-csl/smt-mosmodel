#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-r', '--hot_region', default='hot_region.txt')
parser.add_argument('-n', '--num_layouts', type=int, default=9)
parser.add_argument('-g', '--use_1gb_pages', action='store_true')
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()

standard_page_size = 4*kb
window_page_size = 2*mb
if args.use_1gb_pages:
    window_page_size = 1*gb

def findWeightedWindow(hot_region_df, weight, brk_footprint):
    conf_row = hot_region_df[hot_region_df['window-weight'] == weight]
    hot_region_start_page = conf_row['window-start'].iloc[0]
    hot_region_num_pages = conf_row['window-length'].iloc[0]
    if hot_region_start_page < 0 or hot_region_num_pages < 0:
        return None, None
    hot_region_start =  hot_region_start_page * standard_page_size
    hot_region_length = hot_region_num_pages * standard_page_size

    hot_region_brk_start = conf_row['brk-start'].iloc[0]
    hot_region_brk_size = conf_row['brk-length'].iloc[0]
    brk_ratio = brk_footprint / hot_region_brk_size
    window_start = round_down((int(hot_region_start * brk_ratio)), standard_page_size)
    raw_window_length = round_up(int(hot_region_length * brk_ratio), standard_page_size)
    window_length = round_up(raw_window_length, window_page_size)

    return window_start, window_length

import pandas as pd
footprint_df = pd.read_csv(args.memory_footprint)
hot_region_df = pd.read_csv(args.hot_region, index_col=False, comment='#')

mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = footprint_df['brk-max'][0]

weights = [80,60,50,40,20]
for w in weights:
    window_start, window_length = findWeightedWindow(hot_region_df, w, brk_footprint)
    if window_start is not None:
        break

'''
hot_region_brk_start = conf_row['brk-start'].iloc[0]
hot_region_brk_size = conf_row['brk-length'].iloc[0]
window_start = round_down(hot_region_start, standard_page_size)
raw_window_length = round_up(hot_region_length, standard_page_size)
window_length = round_up(raw_window_length, window_page_size)
'''
window_end = window_start + window_length

# extend pool footprint in case the window exceeds it (due to rounding works)
brk_footprint = max(brk_footprint, window_end)

num_huge_pages = int(window_length / window_page_size)
# case 1: window_huge_pages >= num_layouts
# in this case, select candidates for each n=N*i
# where N = window_huge_pages / num_layouts, i = 1..num_layouts
import random
random.seed(0)
if num_huge_pages >= args.num_layouts:
    step_size = num_huge_pages / args.num_layouts
    for i in range(1, args.num_layouts+1):
        configuration = Configuration()
        configuration.setPoolsSize(
                brk_size=brk_footprint,
                file_size=1*gb,
                mmap_size=mmap_footprint)
        subgroup_size = int(i*step_size)
        huge_pages_offsets = random.sample(range(num_huge_pages), subgroup_size)
        for l in huge_pages_offsets:
            page_offset = window_start + l*window_page_size
            configuration.addWindow(
                    type=configuration.TYPE_BRK,
                    page_size=window_page_size,
                    start_offset=page_offset,
                    end_offset=page_offset + window_page_size)
        configuration.exportToCSV(args.output, 'layout'+str(i))

# case 2: window_huge_pages < num_layouts
# in this case, select candidates for each n and l
# where n=1..window_huge_pages, and l is the offset of the first huge page
# such that nXl=num_layouts
else:
    raise NotImplementedError
