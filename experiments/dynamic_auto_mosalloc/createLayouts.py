#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *
sys.path.append(os.path.dirname(sys.argv[0])+"/../../analysis")
from performance_statistics import PerformanceStatistics

import re
def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def loadDataframe(mean_file):
    mean_ps = PerformanceStatistics(mean_file)
    mean_df = mean_ps.getDataFrame()
    mean_df['cpu-cycles'] = mean_ps.getRuntime()
    mean_df['walk_cycles'] = mean_ps.getWalkDuration()
    mean_df['stlb_hits'] = mean_ps.getStlbHits()
    mean_df['stlb_misses'] = mean_ps.getStlbMisses()
    df = mean_df[['layout', 'walk_cycles', 'stlb_hits', 'stlb_misses', 'cpu-cycles']]
    # drop duplicated rows
    important_columns = list(df.columns)
    important_columns.remove('layout')
    #df.drop_duplicates(inplace=True, subset=important_columns)
    df = df.drop_duplicates(subset=important_columns)
    return df

import random
def writeLayout(layout_name, windows, output):
    page_size = 1 << 21
    random.seed(len(windows))
    start_deviation = random.randint(0, 511)
    offset_deviation = start_deviation * 4096

    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_footprint,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    for w in windows:
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=page_size,
                start_offset=w * page_size + offset_deviation,
                end_offset=(w+1) * page_size + offset_deviation)
    configuration.exportToCSV(output, layout_name)
    #configuration.exportToCSV(output, layout)

def getLayoutHugepages(layout_name, experiments_root_dir):
    layout_file = str.format('{exp_root}/layouts/{layout_name}.csv',
            exp_root=experiments_root_dir,
            layout_name=layout_name)
    df = pd.read_csv(layout_file)
    df = df[df['type'] == 'brk']
    df = df[df['pageSize'] == 2097152]
    pages = []
    for index, row in df.iterrows():
        start_page = int(row['startOffset'] / 2097152)
        end_page = int(row['endOffset'] / 2097152)
        for i in range(start_page, end_page, 1):
            pages.append(i)
    return pages

def calculateTlbCoverage(pebs_df, pages):
    total_weight = pebs_df.query(
            'PAGE_NUMBER in {pages}'.format(pages=pages))\
                    ['NUM_ACCESSES'].sum()
    return total_weight

def findTlbCoverageWindows(df, tlb_coverage_percentage, prev_windows, exclude_pages=None):
    epsilon = 0.5
    windows = None
    while windows == None:
        windows = _findTlbCoverageWindows(df, tlb_coverage_percentage, prev_windows, epsilon, exclude_pages)
        epsilon += 0.5
    return windows

def _findTlbCoverageWindows(df, tlb_coverage_percentage, prev_windows, epsilon, exclude_pages):
    # based on the fact that selected pages in prev_windows are ordered
    # from heaviest to the lightest
    for i in range(len(prev_windows)+1):
        windows = _findTlbCoverageWindowsBasedOnSubset(df, tlb_coverage_percentage, prev_windows[i:], epsilon, exclude_pages)
        if windows:
            return windows

def _findTlbCoverageWindowsBasedOnSubset(df, tlb_coverage_percentage, base_windows, epsilon, exclude_pages):
    total_weight = calculateTlbCoverage(df, base_windows)
    # use a new list instead of using the existing base_windows list to
    # keep it sorted according to page weights
    windows = []
    for index, row in df.iterrows():
        weight = row['NUM_ACCESSES']
        page_number = row['PAGE_NUMBER']
        if exclude_pages and page_number in exclude_pages:
            continue
        if base_windows and page_number in base_windows:
            # pages from base_windows already included in the total weight
            # just add them without increasing the total weight
            windows.append(page_number)
            continue
        if (total_weight + weight) <= (tlb_coverage_percentage + epsilon):
            #print('page: {page} - weight: {weight}'.format(page=page_number, weight=weight))
            total_weight += weight
            windows.append(page_number)
        if total_weight >= (tlb_coverage_percentage - epsilon):
            break

    if total_weight > (tlb_coverage_percentage + epsilon) \
            or total_weight < (tlb_coverage_percentage - epsilon):
        return []
    # add tailed pages from base_windows that were not selected (because
    # we are already reached the goal weight)
    windows += list(set(base_windows) - set(windows))
    return windows

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-s', '--single_page_size_mean', default='results/single_page_size/mean.csv')
parser.add_argument('-p', '--pebs_mem_bins', default='mem_bins_2mb.csv')
parser.add_argument('-r', '--results_mean_file', default='results/dynamic_auto_mosalloc/mean.csv')
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--layouts_dir', required=True)



args = parser.parse_args()

import pandas as pd

# read memory-footprints
footprint_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = footprint_df['brk-max'][0]

# read single_page_size mean file
single_page_size_df = loadDataframe(args.single_page_size_mean)
min_walk_cycles = single_page_size_df[single_page_size_df['layout'] == 'layout4kb'].iloc[0]['walk_cycles']
max_walk_cycles = single_page_size_df[single_page_size_df['layout'] == 'layout2mb'].iloc[0]['walk_cycles']
walk_cycles_span = max_walk_cycles - min_walk_cycles
max_x_delta_percentage = 2.5
max_x_delta = (max_x_delta_percentage/100) * walk_cycles_span

# read mem-bins
pebs_df = pd.read_csv(args.pebs_mem_bins, delimiter=',')

pebs_df = pebs_df[pebs_df['PAGE_TYPE'].str.contains('brk')]
if pebs_df.empty:
    sys.exit('Input file does not contain page accesses information about the brk pool!')
pebs_df = pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
pebs_df = pebs_df.reset_index()

# transform NUM_ACCESSES from absolute number to percentage
total_access = pebs_df['NUM_ACCESSES'].sum()
pebs_df['NUM_ACCESSES'] = pebs_df['NUM_ACCESSES'].mul(100).divide(total_access)
pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)

# read measurements
df = loadDataframe(args.results_mean_file)
df = df.sort_values('walk_cycles').reset_index()

# find the base layout to compare last layout to it
# base layout: the last successful measured layout that has a 2.5% increment
# from a previous base layout
layouts = natural_sort(df['layout'].to_list())
base_layout_name = layouts[0]
for l in layouts:
    base_layout = df[df['layout'] == base_layout_name].iloc[0]
    current_layout = df[df['layout'] == l].iloc[0]
    if current_layout['walk_cycles'] >= base_layout['walk_cycles'] \
            and current_layout['walk_cycles'] < (base_layout['walk_cycles'] + max_x_delta):
        base_layout_name = l

base_layout_pages = getLayoutHugepages(base_layout_name, args.layouts_dir)
last_layout_name = layouts[-1]
last_layout_pages = getLayoutHugepages(last_layout_name, args.layouts_dir)

base_layout = df[df['layout'] == base_layout_name]
last_layout = df[df['layout'] == last_layout_name]

if last_layout_name == base_layout_name:
    # find next layout based on last one + 2.5% of TLB coverage
    tlb_coverage_percentage = calculateTlbCoverage(pebs_df, last_layout_pages) + max_x_delta_percentage
    windows = findTlbCoverageWindows(pebs_df, tlb_coverage_percentage, last_layout_pages)
    '''
elif last_layout['walk_cycles'] < base_layout['walk_cycles']:
    do-something
elif last_layout['walk_cycles'] > base_layout['walk_cycles'] + max_x_delta:
    last_layout_pages_set = set(last_layout_pages)
    base_layout_pages_set = set(base_layout_pages)
    only_in_last_pages = list(last_layout_pages_set - base_layout_pages_set)
    in_both_pages = list(last_layout_pages_set & base_layout_pages_set)
    max_weight = 0
    min_weight = calculateTlbCoverage(last_layout_pages[0])
    for p in last_layout_pages:
        weight = calculateTlbCoverage(p)
        max_weight = max(max_weight, weight)
        min_weight = min(min_weight, weight)
    windows = last_layout_pages.copy()
    windows.remove(min_weight)
    '''
else:
    # try to lighten the last-layout hugepages
    last_layout_pages_set = set(last_layout_pages)
    base_layout_pages_set = set(base_layout_pages)
    only_in_last_pages = list(last_layout_pages_set - base_layout_pages_set)

    base_tlb_coverage = calculateTlbCoverage(pebs_df, base_layout_pages)
    tlb_coverage_percentage = base_tlb_coverage + max_x_delta_percentage

    windows = findTlbCoverageWindows(pebs_df, tlb_coverage_percentage, base_layout_pages, exclude_pages=only_in_last_pages)
#else:
#    raise('Error: invalid layouts mean file')

writeLayout(args.layout, windows, args.layouts_dir)

'''
# find the maximum gap of walk-cycles between measurements
max_gap_idx = df['walk_cycles'].diff().abs().idxmax()

left_index = df.iloc[max_gap_idx-1]
right_index = df.iloc[max_gap_idx]

left_pages = getLayoutHugepages(left_index, args.experiments_root_dir)
left_pages.sort()
left_coverage = findTlbCoverage(pebs_df, left_pages)


right_pages = getLayoutHugepages(right_index, args.experiments_root_dir)
right_pages.sort()
right_coverage = findTlbCoverage(pebs_df, right_pages)

# build layouts
prev_windows = #TODO
tlb_coverage_percentage = right_coverage + max_x_delta_percentage
windows = findTlbCoverageWindows(pebs_df, tlb_coverage_percentage, prev_windows)
print('TLB-coverage = {coverage} - Paegs = {pages}'.format(coverage=tlb_coverage_percentage, pages=windows))
'''

