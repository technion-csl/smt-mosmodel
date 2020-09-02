#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprints', default='memory_footprints.txt')
parser.add_argument('-b', '--benchmark', required=True)
parser.add_argument('-n', '--num_configurations', type=int, default=32)
parser.add_argument('--use_1gb_hugepages', action='store_true', default=False)
parser.add_argument('--max_1gb_hugepages', type=int, default=4)
parser.add_argument('-o', '--output_dir', required=True)
args = parser.parse_args()

import math
def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)

kb = 1024
mb = 1024*kb
gb = 1024*mb
max_1gb_hugepages = args.max_1gb_hugepages * gb
def buildConfiguration(levels, region_arg, region_footprint):
    configurations = []
    step = int(math.floor(region_footprint / levels))
    step = round_up(step, 4*kb)
    for i in range(0, levels):
        step_size = step * i
        region_2m_size = round_down(step_size, 2*mb)
        if args.use_1gb_hugepages:
            end_1g = int(region_2m_size / gb) * gb
            end_1g = min(end_1g, max_1gb_hugepages)
        else:
            end_1g = 0
        region_2m_size -= end_1g
        end_2m = end_1g + region_2m_size
        conf_line = region_arg + 'ps ' + str(region_footprint) + ' '
        conf_line += region_arg + 's1 0 '
        conf_line += region_arg + 'e1 ' + str(end_1g) + ' '
        conf_line += region_arg + 's2 ' + str(end_1g) + ' '
        conf_line += region_arg + 'e2 ' + str(end_2m)
        configurations.append(conf_line)
    return configurations

import itertools
def buildBenchmarkConfigurations(
        min_levels, max_levels,
        mmap_footprint, brk_footprint):
    mmap_levels = min_levels
    brk_levels = max_levels
    file_conf = ['-fps 1GB']
    anon_conf = buildConfiguration(mmap_levels, '-a', mmap_footprint)
    brk_conf = buildConfiguration(brk_levels, '-b', brk_footprint)
    regions_configurations = itertools.product(file_conf, anon_conf, brk_conf)
    configurations = []
    for c in regions_configurations:
        configurations += [' '.join(c)]
    return configurations

import pandas as pd
footprints_df = pd.read_csv(args.memory_footprints, index_col='benchmark')

def isPowerOfTwo(number):
    return (number != 0) and ((number & (number - 1)) == 0)

num_configurations = args.num_configurations - 1
if not isPowerOfTwo(num_configurations):
    raise ValueError('Number of configurations is not power of two')

import os
min_levels = 1
max_levels = int(num_configurations / min_levels)
mmap_footprint = footprints_df.loc[args.benchmark, 'anon-mmap-max']
mmap_footprint = round_up(mmap_footprint, 2*mb)
brk_footprint = footprints_df.loc[args.benchmark, 'brk-max']
brk_footprint = round_up(brk_footprint, 2*mb)
configurations = buildBenchmarkConfigurations(min_levels, max_levels, \
        mmap_footprint, brk_footprint)

# add extra configuration of all 1GB pages
brk_1gb_footprint = round_up(brk_footprint, gb)
brk_2mb_footprint = round_up(brk_footprint, 2*mb)
mmap_2mb_footprint = round_up(mmap_footprint, 2*mb)
brk_rounded_footprint = max(min(max_1gb_hugepages, brk_1gb_footprint), brk_2mb_footprint)
brk_end_1gb = min(max_1gb_hugepages, round_down(brk_rounded_footprint, gb))
if args.use_1gb_hugepages:
    brk_end_2mb = brk_rounded_footprint
else:
    brk_end_2mb = brk_2mb_footprint

if args.use_1gb_hugepages:
    all_hugepages_configuration = str.format('-fps 1GB -aps {0} -as1 0 -ae1 0 -as2 0 -ae2 {0} -bps {1} -bs1 0 -be1 {2} -bs2 {2} -be2 {3}',
            str(mmap_2mb_footprint),
            str(brk_rounded_footprint), str(brk_end_1gb), str(brk_end_2mb))
else:
    all_hugepages_configuration = str.format('-fps 1GB -aps {0} -as1 0 -ae1 0 -as2 0 -ae2 {0} -bps {1} -bs1 0 -be1 0 -bs2 0 -be2 {1}',
            str(mmap_2mb_footprint),
            str(brk_2mb_footprint))

configurations += [all_hugepages_configuration]

# reverse configurations list order to enforce running configurations with more
# huge pages first in growing_window to prevent huge-pages-reservation failures
# in case of memory fragmentation (and then huge-pages reservation fails)
configurations.reverse()

output = args.output_dir + '/' + args.benchmark + '/configurations.txt'
if not os.path.exists(os.path.dirname(output)):
    try:
        os.makedirs(os.path.dirname(output))
    except OSError as exc: # Guard against race condition
        if exc.errno != exc.errno.EEXIST:
            raise
with open(output, 'w+') as output_fid:
    print('\n'.join(configurations), file=output_fid)


