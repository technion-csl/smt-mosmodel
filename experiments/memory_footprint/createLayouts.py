#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--mem_max_size_kb',
        type=int, help='The upper bound of the brk pool size in kB')
parser.add_argument('-m', '--mmap_pool_limit', default=100*1024*1024,
        type=int, help='The maximum size of mmap pool')
parser.add_argument('-o', '--output', required=True)
args = parser.parse_args()

import math
def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)

mem_max_size = args.mem_max_size_kb * 1024
brk_pool_size = round_down(mem_max_size, 4096)
mmap_pool_size = round_up(args.mmap_pool_limit, 4096)
layout_template = '-fps 1GB -aps {0} -as1 {1} -ae1 {2} -as2 {3} -ae2 {4} -bps {5} -bs1 {6} -be1 {7} -bs2 {8} -be2 {9}'
layout_4kb_pages = str.format(layout_template,
        mmap_pool_size, 0, 0, 0, 0,
        brk_pool_size, 0, 0, 0, 0)

layout = 'layout4kb: ' + layout_4kb_pages

with open(args.output, 'w+') as output_fid:
    print(layout, file=output_fid)



