#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *
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
def buildLayouts(num_layouts, brk_footprint, mmap_footprint, output):
    layouts = []
    step = int(math.floor(brk_footprint / num_layouts))
    step = round_up(step, 4*kb)
    # reverse layouts list order to enforce running layouts with more
    # huge pages first in growing_window to prevent huge-pages-reservation failures
    # in case of memory fragmentation (and then huge-pages reservation fails)
    for i in range(num_layouts-1):
        step_size = step * i
        region_2m_size = round_down(step_size, 2*mb)
        end_1g = 0
        if args.use_1gb_hugepages:
            end_1g = int(region_2m_size / gb) * gb
            end_1g = min(end_1g, max_1gb_hugepages)
        region_2m_size -= end_1g
        end_2m = end_1g + region_2m_size
        configuration = Configuration(output, 'layout'+str(num_layouts-i))
        configuration.setPoolsSize(
                brk_size=brk_footprint,
                file_size=1*gb,
                mmap_size=mmap_footprint)
        if end_1g > 0:
            configuration.addWindow(
                    type=configuration.TYPE_BRK,
                    page_size=1*gb,
                    start_offset=0,
                    end_offset=end_1g)
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=2*mb,
                start_offset=end_1g,
                end_offset=end_2m)
        configuration.exportToCSV()

footprint_df = pd.read_csv(args.memory_footprint)

mmap_footprint = footprint_df['anon-mmap-max'][0]
mmap_footprint = round_up(mmap_footprint, 2*mb)
brk_footprint = footprint_df['brk-max'][0]
brk_footprint = round_up(brk_footprint, 2*mb)
buildLayouts(args.num_layouts, brk_footprint, mmap_footprint, args.output)
# add extra layout of all 1GB pages
brk_1gb_footprint = round_up(brk_footprint, gb)
brk_2mb_footprint = round_up(brk_footprint, 2*mb)
mmap_2mb_footprint = round_up(mmap_footprint, 2*mb)
brk_rounded_footprint = max(min(max_1gb_hugepages, brk_1gb_footprint), brk_2mb_footprint)
brk_end_1gb = min(max_1gb_hugepages, round_down(brk_rounded_footprint, gb))

configuration = Configuration(args.output, 'layout1')
if args.use_1gb_hugepages:
    brk_pool_size=brk_rounded_footprint
    mmap_pool_size=mmap_2mb_footprint
    brk_end_2mb = brk_rounded_footprint
    configuration.addWindow(
            type=configuration.TYPE_BRK,
            page_size=1*gb,
            start_offset=0,
            end_offset=brk_end_1gb)
else:
    brk_pool_size=brk_2mb_footprint
    mmap_pool_size=mmap_2mb_footprint
    brk_end_2mb = brk_2mb_footprint
    brk_end_1gb=0

configuration.setPoolsSize(
        brk_size=brk_pool_size,
        file_size=1*gb,
        mmap_size=mmap_pool_size)
configuration.addWindow(
        type=configuration.TYPE_BRK,
        page_size=2*mb,
        start_offset=brk_end_1gb,
        end_offset=brk_end_2mb)
configuration.addWindow(
        type=configuration.TYPE_MMAP,
        page_size=2*mb,
        start_offset=0,
        end_offset=mmap_2mb_footprint)
configuration.exportToCSV()

