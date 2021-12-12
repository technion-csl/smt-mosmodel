#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import *
from Utils.ConfigurationFile import *

import math
def writeLayoutAll2mb(layout, output):
    page_size = 1 << 21
    brk_pool_size = round_up(brk_footprint, page_size)
    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_pool_size,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    configuration.addWindow(
            type=configuration.TYPE_BRK,
            page_size=page_size,
            start_offset=0,
            end_offset=brk_pool_size)
    configuration.exportToCSV(output, layout)

def writeLayout(layout, windows, output):
    page_size = 1 << 21
    configuration = Configuration()
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
    configuration.exportToCSV(output, layout)

def calculateTlbCoverage(pebs_df, pages):
    total_weight = pebs_df.query(
            'PAGE_NUMBER in {pages}'.format(pages=pages))\
                    ['NUM_ACCESSES'].sum()
    return total_weight

def buildGroupsSequentially(orig_pebs_df, layouts_dir, desired_weights):
    pebs_df = orig_pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
    threshold = 60
    pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)
    groups = []
    all_pages = []
    i = 0
    epsilon = 1
    for index, row in pebs_df.iterrows():
        current_total_weight = 0
        current_group = []

        page_number = int(row['PAGE_NUMBER'])
        if page_number in all_pages:
            continue

        weight = row['NUM_ACCESSES']
        if weight > (desired_weights[i] + epsilon):
            continue

        query = pebs_df.query(
            'PAGE_NUMBER <= {max_page} and PAGE_NUMBER >= {min_page} and PAGE_NUMBER not in {all_pages}'.format(
                max_page=page_number+25,
                min_page=page_number-25,
                all_pages=all_pages))
        if query['NUM_ACCESSES'].sum() < desired_weights[i]:
            continue
        query_df = query.sort_values('PAGE_NUMBER', ascending=True).reset_index()
        query_df = query_df[['PAGE_NUMBER', 'NUM_ACCESSES']]

        page_index = query_df[query_df['PAGE_NUMBER'] == page_number].index.to_list()[0]
        left_index = page_index-1 if page_index > 0 else 0
        right_index = page_index+1 if page_index < len(query_df)-1 else page_index

        current_total_weight += weight
        current_group.append(page_number)

        found = True
        while right_index < len(query_df) or left_index >= 0:
            # if we already achieved our goal then stop
            if current_total_weight > (desired_weights[i] - epsilon):
                found = False
                break
            # if there is a right side then get its weight
            if right_index != page_index and right_index < len(query_df):
                right_page = query_df.iat[right_index, 0]
                right_weight = query_df.iat[right_index, 1]
            else:
                right_page = -1
                right_weight = -1
            # if there is a left side then get its weight
            if left_index != page_index and left_index >= 0:
                left_page = query_df.iat[left_index, 0]
                left_weight = query_df.iat[left_index, 1]
            else:
                left_page = -1
                left_weight = -1
            # if we are adding too much then stop
            if (current_total_weight + right_weight) > (desired_weights[i] + epsilon) \
            or (current_total_weight + left_weight) > (desired_weights[i] + epsilon):
                found = False
                break
            # take the larger side
            if right_weight > left_weight:
                current_total_weight += right_weight
                current_group.append(right_page)
                right_index += 1
            else:
                current_total_weight += left_weight
                current_group.append(left_page)
                left_index -= 1
        if found:
            groups.append(list(set(current_group)))
            all_pages += current_group
            i += 1
        if i == len(desired_weights):
            break
    return groups

def buildGroups(pebs_df, layouts_dir):
    threshold = 60
    pebs_df.sort_values('NUM_ACCESSES', ascending=False, inplace=True)
    groups = []
    current_group = []
    current_total_weight = 0
    i = 0
    desired_weights = [30, 20, 10]
    for index, row in pebs_df.iterrows():
        page_number = int(row['PAGE_NUMBER'])
        weight = row['NUM_ACCESSES']
        if current_total_weight >= desired_weights[i]:
            groups.append(current_group)
            current_group = []
            current_total_weight = 0
            i += 1
        if i == len(desired_weights):
            break
        if current_total_weight < desired_weights[i]:
            current_total_weight += weight
            current_group.append(page_number)
    return groups

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-p', '--pebs_mem_bins', default='mem_bins_2mb.csv')
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--layouts_dir', required=True)
args = parser.parse_args()

import pandas as pd
# read memory-footprints
footprint_pebs_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_pebs_df['anon-mmap-max'][0]
brk_footprint = footprint_pebs_df['brk-max'][0]
last_page = int(brk_footprint / 4096)

# read mem-bins
pebs_df = pd.read_csv(args.pebs_mem_bins, delimiter=',')
#pebs_df['PAGE_NUMBER'] = pebs_df['PAGE_NUMBER'].astype(int)

pebs_df = pebs_df[pebs_df['PAGE_TYPE'].str.contains('brk')]
if pebs_df.empty:
    sys.exit('Input file does not contain page accesses information about the brk pool!')
pebs_df = pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
pebs_df = pebs_df.reset_index()

# transform NUM_ACCESSES from absolute number to percentage
total_access = pebs_df['NUM_ACCESSES'].sum()
pebs_df['NUM_ACCESSES'] = pebs_df['NUM_ACCESSES'].mul(100).divide(total_access)
pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)

import itertools
if args.layout == 'layout1':
    i = 1
    desired_weights = [30, 20, 10]
    groups = []
    while len(groups) != 3:
        groups = buildGroupsSequentially(pebs_df, args.layouts_dir, desired_weights)
        desired_weights = [0.9*w for w in desired_weights]
    for subset_size in range(len(groups)+1):
        for subset in itertools.combinations(groups, subset_size):
            windows = []
            for l in subset:
                windows += l
            layout_name = 'layout' + str(i)
            i += 1
            print(layout_name)
            print('#hugepages: '+ str(len(windows)))
            print('weight: ' + str(calculateTlbCoverage(pebs_df, windows)))
            print('hugepages: ' + str(windows))
            print('---------------')
            writeLayout(layout_name, windows, args.layouts_dir)
    layout_name = 'layout' + str(i)
    print(layout_name)
    print('weight: 100%')
    print('hugepages: all pages')
    writeLayoutAll2mb(layout_name, args.layouts_dir)
else:
    sys.exit(args.layout + ' is not supported yet!')
