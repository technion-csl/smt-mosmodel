#!/usr/bin/env python3

kb = 1024
mb = 1024*kb
gb = 1024*mb

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprints', default='memory_footprints.txt')
parser.add_argument('-b', '--benchmark', required=True)
parser.add_argument('-n', '--num_configurations', type=int, default=4)
parser.add_argument('-w', '--window_min_size_ratio', type=float, default=0)
parser.add_argument('-s', '--seed', type=int, default=0)
parser.add_argument('-o', '--output_dir', required=True)
args = parser.parse_args()

import math
def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)


def isPowerOfTwo(number):
    return (number != 0) and ((number & (number - 1)) == 0)

num_configurations = args.num_configurations - 1
if not isPowerOfTwo(num_configurations):
    raise ValueError('Number of configurations is not power of two')

import pandas as pd
footprints_df = pd.read_csv(args.memory_footprints, index_col='benchmark')

mmap_footprint = footprints_df.loc[args.benchmark]['anon-mmap-max']
brk_footprint = footprints_df.loc[args.benchmark]['brk-max']

conf_prefix = '-fps 1GB ' \
        + '-aps ' + str(mmap_footprint) + ' ' \
        + '-bps ' + str(brk_footprint) + ' '

start_offset = 0
end_offset = brk_footprint
window_min_size = max(2*mb, round_up(args.window_min_size_ratio * brk_footprint, 2*mb))

configurations_list = []
import random
random.seed(args.seed)
for i in range(args.num_configurations):
    random_start_offset = random.randrange(start_offset,
            end_offset - window_min_size, (4*kb))
    random_end_offset = random.randrange(random_start_offset + window_min_size,
            end_offset, 2*mb)
    configurations_list.append([0, 0, random_start_offset, random_end_offset])

import numpy as np
conf_array = np.array(configurations_list).astype('S140')
insert_args = [conf_prefix, '-bs1 ', '-be1 '
        , '-bs2 ', '-be2 ']
conf_args = np.insert(conf_array, (0,0,1,2,3), insert_args, axis=1).astype(str)

configurations = ''
for c in conf_args:
    configurations += ' '.join(c) + '\n'

import os
output = args.output_dir + '/' + args.benchmark + '/configurations.txt'
if not os.path.exists(os.path.dirname(output)):
    try:
        os.makedirs(os.path.dirname(output))
    except OSError as exc: # Guard against race condition
        if exc.errno != exc.errno.EEXIST:
            raise

with open(output, 'w') as output_fid:
    print(configurations, file=output_fid)


