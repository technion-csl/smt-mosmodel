#!/usr/bin/env python3
from Utils.utils import *
import math
import argparse
import itertools
import pandas as pd
import os



parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-n', '--num_layouts', type=int, default=9)
parser.add_argument('--use_1gb_hugepages', action='store_true', default=False)
parser.add_argument('--max_1gb_hugepages', type=int, default=4)
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()


max_1gb_hugepages = args.max_1gb_hugepages * gb
def buildLayout(levels, region_arg, region_footprint):
    layouts = []
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
        layouts.append(conf_line)
    return layouts


def buildBenchmarkLayouts(
        min_levels, max_levels,
        mmap_footprint, brk_footprint):
    mmap_levels = min_levels
    brk_levels = max_levels
    file_conf = ['-fps 1GB']
    anon_conf = buildLayout(mmap_levels, '-a', mmap_footprint)
    brk_conf = buildLayout(brk_levels, '-b', brk_footprint)
    regions_layouts = itertools.product(file_conf, anon_conf, brk_conf)
    layouts = []
    for c in regions_layouts:
        layouts += [' '.join(c)]
    return layouts

footprint_df = pd.read_csv(args.memory_footprint)



num_layouts = args.num_layouts - 1
if not isPowerOfTwo(num_layouts):
    raise ValueError('Number of layouts is not power of two')


min_levels = 1
max_levels = int(num_layouts / min_levels)
mmap_footprint = footprint_df['anon-mmap-max'][0]
mmap_footprint = round_up(mmap_footprint, 2*mb)
brk_footprint = footprint_df['brk-max'][0]
brk_footprint = round_up(brk_footprint, 2*mb)
layouts = buildBenchmarkLayouts(min_levels, max_levels, \
        mmap_footprint, brk_footprint)

# add extra layout of all 1GB pages
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
    all_hugepages_layout = str.format('-fps 1GB -aps {0} -as1 0 -ae1 0 -as2 0 -ae2 {0} -bps {1} -bs1 0 -be1 {2} -bs2 {2} -be2 {3}',
            str(mmap_2mb_footprint),
            str(brk_rounded_footprint), str(brk_end_1gb), str(brk_end_2mb))
else:
    all_hugepages_layout = str.format('-fps 1GB -aps {0} -as1 0 -ae1 0 -as2 0 -ae2 {0} -bps {1} -bs1 0 -be1 0 -bs2 0 -be2 {1}',
            str(mmap_2mb_footprint),
            str(brk_2mb_footprint))

layouts += [all_hugepages_layout]

# reverse layouts list order to enforce running layouts with more
# huge pages first in growing_window to prevent huge-pages-reservation failures
# in case of memory fragmentation (and then huge-pages reservation fails)
layouts.reverse()

# prefix each configuration with layoutX: where X is the layout number
for i in range(len(layouts)):
    layouts[i] = 'layout' +str(i+1) + ': ' + layouts[i]

with open(args.output, 'w+') as output_fid:
    print('\n'.join(layouts), file=output_fid)


