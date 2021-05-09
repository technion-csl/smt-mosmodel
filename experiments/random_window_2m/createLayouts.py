#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *
import math
import argparse
import pandas as pd
import random
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-n', '--num_layouts', type=int, default=9)
parser.add_argument('-w', '--window_min_size_ratio', type=float, default=0)
parser.add_argument('-s', '--seed', type=int, default=0)
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()


num_layouts = args.num_layouts - 1
if not isPowerOfTwo(num_layouts):
    raise ValueError('Number of layouts is not power of two')

footprint_df = pd.read_csv(args.memory_footprint)

mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = footprint_df['brk-max'][0]

start_offset = 0
end_offset = brk_footprint
window_min_size = max(2*mb, round_up(args.window_min_size_ratio * brk_footprint, 2*mb))

layouts_list = []
random.seed(args.seed)
for i in range(args.num_layouts):
    random_start_offset = random.randrange(start_offset,
            end_offset - window_min_size, (4*kb))
    random_end_offset = random.randrange(random_start_offset + window_min_size,
            end_offset, 2*mb)
    configuration = Configuration(args.output, 'layout'+str(i+1))
    configuration.setPoolsSize(
            brk_size=round_up(brk_footprint, 2*mb),
            file_size=1*gb,
            mmap_size=mmap_footprint)
    configuration.addWindow(type=configuration.TYPE_BRK,
            page_size=2*mb,
            start_offset=random_start_offset,
            end_offset=random_end_offset)
    configuration.exportToCSV()

