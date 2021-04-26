#!/usr/bin/env python3
from Utils.utils import *
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

conf_prefix = '-fps 1GB ' \
        + '-aps ' + str(mmap_footprint) + ' ' \
        + '-bps ' + str(brk_footprint) + ' '

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
    layouts_list.append([0, 0, random_start_offset, random_end_offset])

conf_array = np.array(layouts_list).astype('S140')
insert_args = [conf_prefix, '-bs1 ', '-be1 '
        , '-bs2 ', '-be2 ']
conf_args = np.insert(conf_array, (0,0,1,2,3), insert_args, axis=1).astype(str)

layouts = ''
i = 1
for c in conf_args:
    layouts += 'layout' +str(i) + ': ' + ' '.join(c) + '\n'
    i += 1

with open(args.output, 'w') as output_fid:
    print(layouts, file=output_fid)


