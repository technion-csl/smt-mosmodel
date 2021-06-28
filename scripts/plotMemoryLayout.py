#! /usr/bin/env python3

page_size = (2**21)

import pandas as pd
def getLayoutHugepages(layout_file):
    df = pd.read_csv(layout_file)
    df = df[df['type'] == 'brk']
    df = df[df['pageSize'] == 2097152]
    pages = []
    for index, row in df.iterrows():
        start_page = int(row['startOffset'] / page_size)
        end_page = int(row['endOffset'] / page_size)
        for i in range(start_page, end_page, 1):
            pages.append(i)
    return pages

def binary_data(data, yshift=0, limit=-1):
    data.sort()
    if limit == -1:
        limit = data[-1]
    return [yshift+1 if x in data else yshift for x in range(limit)]

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--layout_files', required=True)
parser.add_argument('-l', '--layout_labels', required=True)
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-o', '--output',  default='all_points', required=True)
args = parser.parse_args()

import math
# read memory-footprints
footprint_df = pd.read_csv(args.memory_footprint)
brk_footprint = footprint_df['brk-max'][0]
brk_footprint = math.ceil(brk_footprint / page_size) * page_size

import numpy as np
import matplotlib.pyplot as plt
fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(9,2.5))
ax2 = ax.twinx()
# set x, y labels
ax.set_xlabel('page number (2MB)')
ax.set_ylabel('page size')
ax2.set_ylabel('total pages')

limit = math.ceil(brk_footprint / page_size)
x = np.arange(0, limit)
# read the layout files
layout_files = args.layout_files.strip().split(',')
layout_labels = args.layout_labels.strip().split(',')
num_layouts = len(layout_files)
total_pages = [0, 0] * num_layouts
for i in range(num_layouts - 1, -1, -1):
    f = layout_files[i]
    l = layout_labels[i]
    pages = getLayoutHugepages(f)
    print(f,' has [',len(pages),'] hugepages')
    shift = i * 2
    bindata = binary_data(pages, shift, limit)
    y = np.array(bindata)
    #ax.step(x, y, label=l)
    ax.plot(x, y, '|', label=l)
    total_pages[i*2] = limit-len(pages)
    total_pages[i*2+1] = len(pages)

handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, labels, loc='best')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2),
        ncol=2, fancybox=True, shadow=False)
ax.set_yticks(np.arange((num_layouts)*2))
ax.set_yticklabels(['4KB', '2MB'] * num_layouts)
ax2.set_yticks(np.arange((num_layouts)*2))
ax2.set_yticklabels(total_pages)

fig.savefig(args.output, bbox_inches='tight')

