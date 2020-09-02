#!/usr/bin/env python3

kb = 1024
mb = 1024*kb
gb = 1024*mb

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--effects', default='effects.csv')
parser.add_argument('-m', '--memory_footprints', default='memory_footprints.txt')
parser.add_argument('-b', '--benchmark', required=True)
parser.add_argument('-n', '--num_configurations', type=int, default=4)
parser.add_argument('-f', '--start_offset', type=int, default=0)
parser.add_argument('-s', '--step_size', type=int, default=0)
parser.add_argument('-o', '--output', required=True)
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
effects_df = pd.read_csv(args.effects, index_col='benchmark')
footprints_df = pd.read_csv(args.memory_footprints, index_col='benchmark')

mmap_effect = effects_df.loc[args.benchmark]['q_mmap']
brk_effect = effects_df.loc[args.benchmark]['q_brk']
mmap_footprint = footprints_df.loc[args.benchmark]['anon-mmap-max']
brk_footprint = footprints_df.loc[args.benchmark]['brk-max']

min_effect_footprint = brk_footprint
min_effect_arg = '-b'
max_effect_footprint = mmap_footprint
max_effect_arg = '-a'

if abs(mmap_effect) < abs(brk_effect):
    max_effect_footprint = brk_footprint
    max_effect_arg = '-b'
    min_effect_footprint = mmap_footprint
    min_effect_arg = '-a'

step_size = args.step_size
if step_size == 0:
    step_size = (max_effect_footprint - args.start_offset) / num_configurations
step_size = round_down(step_size, 2*mb)
if (step_size * num_configurations) > max_effect_footprint:
    raise ValueError('large step_size which may cause to exceed max footprint')

conf_prefix = '-fps 1GB ' \
        + min_effect_arg + 'ps ' + str(min_effect_footprint) + ' ' \
        + max_effect_arg + 'ps ' + str(max_effect_footprint) + ' '

configurations_list = []
for i in range(0, args.num_configurations):
    start_2mb = args.start_offset
    end_2mb = start_2mb + step_size * i
    configurations_list.append([0, 0, start_2mb, end_2mb])

import numpy as np
conf_array = np.array(configurations_list).astype('S140')
insert_args = [conf_prefix, max_effect_arg+'s1 ', max_effect_arg+'e1 '
        , max_effect_arg+'s2 ', max_effect_arg+'e2 ']
conf_args = np.insert(conf_array, (0,0,1,2,3), insert_args, axis=1).astype(str)

configurations = ''
for c in conf_args:
    configurations += ' '.join(c) + '\n'

with open(args.output, 'w') as output_fid:
    print(configurations, file=output_fid)


