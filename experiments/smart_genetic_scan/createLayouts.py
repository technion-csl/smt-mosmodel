#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
#sys.path.append('../')
#sys.path.append('../../')
from Utils.utils import *
from Utils.ConfigurationFile import *
import pandas as pd
sys.path.append(os.path.dirname(sys.argv[0])+"/../../analysis")
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
def writeLayout(layout, windows, start_offset, output):
    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_footprint,
            file_size=1*gb,
            mmap_size=mmap_footprint)
    for w in windows:
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=page_size,
                start_offset=w * page_size + start_offset,
                end_offset=(w+1) * page_size + start_offset)
    configuration.exportToCSV(output, layout)

import random
def combineGenes(father_allele, mother_allele, gene_length, gene_weights_df, father_gene_weight, mother_gene_weight):
    gene = []
    father_set = set(father_allele)
    mother_set = set(mother_allele)
    only_in_father = list(father_set - mother_set)
    only_in_mother = list(mother_set - father_set)
    in_both = list(father_set & mother_set)
    gene += in_both

    weights_df = pd.DataFrame(columns=['origin', 'id', 'weight'])
    # calculate the gene variance-weight in father
    only_in_father_weight = 0
    for l in only_in_father:
        freq = gene_weights_df[gene_weights_df['PAGE_NUMBER'] == l]['NUM_ACCESSES']
        if freq.empty:
            continue
        weight = freq.iloc[0] * father_gene_weight
        only_in_father_weight += weight
        weights_df = weights_df.append({
            'origin':'father',
            'id':l,
            'weight':weight}, ignore_index=True)
    # calculate the gene variance-weight in mother
    only_in_mother_weight = 0
    for l in only_in_mother:
        freq = gene_weights_df[gene_weights_df['PAGE_NUMBER'] == l]['NUM_ACCESSES']
        if freq.empty:
            continue
        weight = freq.iloc[0] * mother_gene_weight
        only_in_mother_weight += weight
        weights_df = weights_df.append({
            'origin':'mother',
            'id':l,
            'weight':weight}, ignore_index=True)
    # find smallest set that covers the expected weight
    if not weights_df.empty:
        weights_df = weights_df.sort_values('weight', ascending=False).reset_index()
        gene_expected_weight = (only_in_father_weight + only_in_mother_weight) / 2
        total_weight = 0
        epsilon = 0.5
        for index, row in weights_df.iterrows():
            if (total_weight + row['weight']) <= (gene_expected_weight + epsilon):
                total_weight += row['weight']
                gene.append(row['id'])
            if total_weight > gene_expected_weight:
                break

    random.seed(len(gene))
    gene_deviation = random.randint(0, 511)

    return gene, gene_deviation

import numpy as np
def calculatePageWalkLatency(df, pages, pebs_df):
    total_misses = 0
    for p in pages:
        row = pebs_df[pebs_df['PAGE_NUMBER'] == p]
        if row['NUM_ACCESSES'].any():
                total_misses += row.iloc[0]['NUM_ACCESSES']
    if total_misses == 0:
        return np.inf
    walk_cycles = df['walk_cycles']
    return walk_cycles / total_misses

def getLayoutHugepages(layout, layouts_dir):
    #FIXME don't hardcode the path
    if layout.find('4kb') > 0 or layout.find('2mb') > 0:
        layouts_dir = 'experiments/single_page_size'
    df = pd.read_csv('{dir}/layouts/{file}.csv'.format(dir=layouts_dir, file=layout))
    df = df[df['type'] == 'brk']
    df = df[df['pageSize'] == 2097152]
    pages = []
    for index, row in df.iterrows():
        start_page = int(row['startOffset'] / 2097152)
        end_page = int(row['endOffset'] / 2097152)
        for i in range(start_page, end_page, 1):
            pages.append(i)
    return pages

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-s', '--single_page_size_results', default='results/single_page_size/mean.csv')
parser.add_argument('-g', '--smart_genetic_results', default='results/smart_genetic_scan/mean.csv')
parser.add_argument('-b', '--pebs_mem_bins', required=True)
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--layouts_dir', required=True)
args = parser.parse_args()

# read memory-footprints
footprint_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = round_up(footprint_df['brk-max'][0], page_size)

# read mem-bins
mem_bins_df = pd.read_csv(args.pebs_mem_bins, delimiter=',')
mem_bins_df = mem_bins_df[mem_bins_df['PAGE_TYPE'].str.contains('brk')]
if mem_bins_df.empty:
    sys.exit('The mem_bins input file does not contain page accesses information about the brk pool!')
mem_bins_df = mem_bins_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
mem_bins_df.reset_index(inplace=True)
'''
# transform NUM_ACCESSES from absolute number to percentage
total_access = mem_bins_df['NUM_ACCESSES'].sum()
mem_bins_df['MISS_RATIO'] = mem_bins_df['NUM_ACCESSES']
mem_bins_df['MISS_RATIO'] = mem_bins_df['MISS_RATIO'].divide(total_access)
mem_bins_df = mem_bins_df.sort_values('MISS_RATIO', ascending=False)
mem_bins_df['REVISED_MISS_RATIO'] = mem_bins_df['MISS_RATIO']
'''

# read single-page-siez mean file
sp_df = loadDataframe(args.single_page_size_results)
assert(sp_df.layout.str.findall('4kb').sum())
assert(sp_df.layout.str.findall('2mb').sum())

from os import path
if path.exists(args.smart_genetic_results):
    # read smart_genetic_window mean file
    gen_df = loadDataframe(args.smart_genetic_results)
    # append mean files
    gen_df = sp_df.append(gen_df)
else:
    gen_df= sp_df
df = gen_df.sort_values('walk_cycles').reset_index()

# find the maximum gap of walk-cycles between measurements
max_gap_idx = df['walk_cycles'].diff().abs().idxmax()

print(df)
print('max diff between: [',
        df.iloc[max_gap_idx]['layout'], ' - ', df.iloc[max_gap_idx-1]['layout'], ']')

father = df.iloc[max_gap_idx]
mother = df.iloc[max_gap_idx-1]
#high_measurement = df.iloc[max_gap_idx]
father_pages = getLayoutHugepages(father['layout'], args.layouts_dir)
father_pages.sort()

#low_measurement = df.iloc[max_gap_idx-1]
mother_pages = getLayoutHugepages(mother['layout'], args.layouts_dir)
mother_pages.sort()

father_page_walk_latency = calculatePageWalkLatency(father, father_pages, mem_bins_df)
mother_page_walk_latency = calculatePageWalkLatency(mother, mother_pages, mem_bins_df)

num_of_huge_pages = int(brk_footprint / page_size)
windows, hugepage_start_location = combineGenes(father_pages, mother_pages, num_of_huge_pages, mem_bins_df, father_page_walk_latency, mother_page_walk_latency)
#print('Low measurement pages: ',low_pages)
#print('Next measurement pages: ',windows)
#print('High measurement pages: ',high_pages)
writeLayout(args.layout, windows, hugepage_start_location*4096, args.layouts_dir)


