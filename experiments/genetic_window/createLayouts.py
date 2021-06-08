#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *
import pandas as pd
from performance_statistics import PerformanceStatistics
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

page_size = 1 << 21
def writeLayout(layout, windows, output):
    configuration = Configuration(output, layout)
    configuration.setPoolsSize(
            brk_size=brk_footprint,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    for w in windows:
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=page_size,
                start_offset=w * page_size,
                end_offset=(w+1) * page_size)
    configuration.exportToCSV()

def findTlbCoverageWindows(df, tlb_coverage_percentage, start_pages, candidate_pages):
    epsilon = 0.5
    windows = []
    windows.append(start_pages)
    total_weight = df[df['PAGE_NUMBER'].isin(windows)]['REVISED_MISS_RATIO'].sum()
    for p in candidate_pages:
        if p in windows:
            continue
        weight = df[df['PAGE_NUMBER'] == p]['REVISED_MISS_RATIO']
        if (total_weight + weight) <= (tlb_coverage_percentage + epsilon):
            total_weight += weight
            windows.append(p)
    df.sort_values('REVISED_MISS_RATIO')
    for index, row in df.iterrows():
        weight = row['REVISED_MISS_RATIO']
        page_number = row['PAGE_NUMBER']
        if (total_weight + weight) <= (tlb_coverage_percentage + epsilon):
            total_weight += weight
            windows.append(page_number)
        else break
    return windows

def getLayoutHugepages(layout, layouts_dir):
    df = pd.read_csv('{dir}/{file}.csv'.format(dir=layouts_dir, file=layout))
    df = df[df['type'] == 'brk']
    df = df[df['pageSize'] == 2097152]
    pages = []
    for index, row in df.iterrows():
        start_page = int(row['startOffset'] / 2097152)
        end_page = int(row['endOffset'] / 2097152)
        for i in range(start_page, end_page, 1):
            pages.append(i)
    return pages

def recalculateMissRatio(df, measurement, pebs_df, layouts_dir):
    # calculate the measurement real stlb miss-rate
    row_4kb = df[df['layout'] == 'layout4kb']
    measurement_stlb_ratio = measurement['stlb_misses'] / row_4kb['stlb_misses']
    # read the layout configuration file (of the given measurement) and get the used hugepages
    layout = measurement['layout']
    pages = getLayoutHugepages(layout, layouts_dir)
    # revise pebs results to match the real measurement stlb miss-rate
    pebs_mask = pebs_df['PAGE_NUMBER'].isin(pages)
    pebs_stlb_saving_ratio = pebs_df[pebs_mask]['MISS_RATIO'].sum()
    measurement_expected_stlb_ratio = 1 - pebs_stlb_saving_ratio
    revised_value = measurement_stlb_ratio / measurement_expected_stlb_ratio
    pebs_df.loc[pebs_mask, 'REVISED_MISS_RATIO'] = pebs_df.loc[pebs_mask, 'REVISED_MISS_RATIO'].apply(lambda x: x*revised_ratio)
    return pages

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-s', '--single_page_size_results', default='results/single_page_size/mean.csv')
parser.add_argument('-g', '--genetic_results', default='results/genetic_window/mean.csv')
parser.add_argument('-b', '--pebs_mem_bins', required=True)
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--layouts_dir', required=True)
args = parser.parse_args()

# read memory-footprints
footprint_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = footprint_df['brk-max'][0]

# read single-page-siez mean file
sp_df = loadDataframe(args.single_page_size_results)
assert(sp_df.layout.str.find('4kb') >= 0)
assert(sp_df.layout.str.find('2mb') >= 0)

# read genetic_window mean file
gen_df = loadDataframe(args.genetic_results)
# append mean files
gen_df = sp_df.append(gen_df)
df = gen_df.sort_values('walk_cycles')

# read mem-bins
mem_bins_df = pd.read_csv(args.pebs_mem_bins, delimiter=',')
mem_bins_df = mem_bins_df[mem_bins_df['PAGE_TYPE'].str.contains('brk')]
if mem_bins_df.empty:
    sys.exit('The mem_bins input file does not contain page accesses information about the brk pool!')
mem_bins_df = mem_bins_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
mem_bins_df.reset_index(inplace=True)
# transform NUM_ACCESSES from absolute number to percentage
total_access = mem_bins_df['NUM_ACCESSES'].sum()
mem_bins_df['MISS_RATIO'] = mem_bins_df['NUM_ACCESSES']
mem_bins_df['MISS_RATIO'] = mem_bins_df['MISS_RATIO'].divide(total_access)
mem_bins_df = mem_bins_df.sort_values('MISS_RATIO', ascending=False)
mem_bins_df['REVISED_MISS_RATIO'] = mem_bins_df['MISS_RATIO']

# find the maximum gap of walk-cycles between measurements
max_gap_idx = df['walk_cycles'].diff().abs().idxmax()

high_measurement = df.iloc[max_gap_idx]
high_tlb_miss_rate = high_measurement['stlb_misses']
high_pages = recalculateMissRatio(df, high_measurement, mem_bins_df, args.layouts_dir)
high_pages.sort()

low_measurement = df.iloc[max_gap_idx-1]
low_tlb_miss_rate = low_measurement['stlb_misses']
low_pages = recalculateMissRatio(df, low_measurement, mem_bins_df, args.layouts_dir)
low_pages.sort()

expected_tlb_miss_raet = (high_tlb_miss_rate + low_tlb_miss_rate) / 2
windows = findTlbCoverageWindows(mem_bins_df, expected_tlb_miss_raet, low_pages, high_pages)
print('Low measurement pages: ',low_pages)
print('Next measurement pages: ',windows)
print('High measurement pages: ',high_pages)
writeLayout(args.layout, windows, args.layouts_dir)


