#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--max_res_memory_kb', default='max_mem.txt',
        type=int, help='Maximum resident memory in KB')
parser.add_argument('-m', '--mmap_pool_limit', default=100*1024*1024,
        type=int, help='The maximum size of mmap pool')
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()

import math
def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)

kb = 1024
mb = 1024*kb
gb = 1024*mb

max_res_memory = args.max_res_memory_kb * kb
extra_mem = min(100*mb, 0.1*max_res_memory)
brk_pool_size = round_up(max_res_memory + extra_mem, 4*kb)
mmap_pool_size = round_up(args.mmap_pool_limit, 4*kb)
layout_remplate = '-fps 1GB -aps {0} -as1 {1} -ae1 {2} -as2 {3} -ae2 {4} -bps {5} -bs1 {6} -be1 {7} -bs2 {8} -be2 {9}'
layout_4kb_pages = str.format(layout_remplate,
        mmap_pool_size, 0, 0, 0, 0,
        brk_pool_size, 0, 0, 0, 0)
layout_2mb_pages = str.format(layout_remplate,
        round_up(mmap_pool_size, 2*mb), 0, 0, 0, round_up(mmap_pool_size, 2*mb),
        round_up(brk_pool_size, 2*mb), 0, 0, 0, round_up(brk_pool_size, 2*mb))
layout_1gb_pages = str.format(layout_remplate,
        round_up(mmap_pool_size, gb), 0, round_up(mmap_pool_size, gb),0, 0,
        round_up(brk_pool_size, gb), 0, round_up(brk_pool_size, gb), 0, 0)

layouts = 'layout1gb: ' + layout_1gb_pages + '\n' \
        + 'layout2mb: ' + layout_2mb_pages + '\n' \
        + 'layout4kb: ' + layout_4kb_pages + '\n'

with open(args.output, 'w+') as output_fid:
    print(layouts, file=output_fid)



