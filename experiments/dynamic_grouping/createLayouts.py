#!/usr/bin/env python3
import sys
import os
import pandas as pd
import itertools
import os.path

sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import Utils
from Utils.ConfigurationFile import Configuration

sys.path.append(os.path.dirname(sys.argv[0])+"/../../analysis")
from performance_statistics import PerformanceStatistics

def loadDataframe(mean_file):
    mean_ps = PerformanceStatistics(mean_file)
    results_df = mean_ps.getDataFrame()
    results_df['cpu-cycles'] = mean_ps.getRuntime()
    results_df['walk_cycles'] = mean_ps.getWalkDuration()
    results_df['stlb_hits'] = mean_ps.getStlbHits()
    results_df['stlb_misses'] = mean_ps.getStlbMisses()
    df = results_df[['layout', 'walk_cycles', 'stlb_hits', 'stlb_misses', 'cpu-cycles']]
    # drop duplicated rows
    important_columns = list(df.columns)
    important_columns.remove('layout')
    #df.drop_duplicates(inplace=True, subset=important_columns)
    df = df.drop_duplicates(subset=important_columns)
    return df

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class StaticLog(metaclass=Singleton):
    def __init__(self, exp_dir):
        self._exp_dir = exp_dir
        self._log_file = self._exp_dir + '/static_layouts.log'
        self._df = self.readLog()

    def readLog(self):
        if not os.path.isfile(self._log_file):
            self._df = pd.DataFrame(columns=[
                'layout', 'right_layout', 'left_layout',
                'expected_coverage', 'real_coverage'])
        else:
            self._df = pd.read_csv(self._log_file)
        self._df['real_coverage'] = self._df['real_coverage'].astype(float)
        return self._df

    def addRecord(self,
                  layout, right_layout, left_layout, expected_coverage,
                  writeLog=False):
        self._df = self._df.append({
            'layout': layout,
            'right_layout': right_layout,
            'left_layout': left_layout,
            'expected_coverage': expected_coverage,
            'real_coverage': -1
            }, ignore_index=True)
        if writeLog:
            self.writeLog()

    def writeRealCoverage(self, results_df):
        max_walk_cycles = results_df['walk_cycles'].max()
        min_walk_cycles = results_df['walk_cycles'].min()
        delta_walk_cycles = max_walk_cycles - min_walk_cycles
        self._df['real_coverage'] = self._df['real_coverage'].astype(float)
        query = self._df.query('real_coverage == (-1)')
        for index, row in query.iterrows():
            layout = row['layout']
            walk_cycles = results_df.loc[results_df['layout'] == layout, 'walk_cycles'].iloc[0]
            real_coverage = (max_walk_cycles - walk_cycles) / delta_walk_cycles
            real_coverage *= 100
            self._df.loc[self._df['layout'] == layout, 'real_coverage'] = real_coverage
        self.writeLog()
        return self._df

    def writeLog(self):
        self._df.to_csv(self._log_file, index=False)

    def clear(self):
        self._df = pd.DataFrame(columns=self._df.columns)

    def _getField(self, layout, field):
        field_val = self._df.loc[self._df['layout'] == layout, field]
        field_val = field_val.to_list()
        if field_val == []:
            return None
        else:
            return field_val[0]

    def getRealCoverage(self, layout):
        return self._getField(layout, 'real_coverage')

    def getExpectedCoverage(self, layout):
        return self._getField(layout, 'expected_coverage')

import os.path
class GroupsLog(metaclass=Singleton):
    def __init__(self, exp_dir):
        self._exp_dir = exp_dir
        self._log_file = self._exp_dir + '/groups.log'
        self._df = self.readLog()

    def readLog(self):
        if not os.path.isfile(self._log_file):
            self._df = pd.DataFrame(columns=[
                'layout', 'total_budget', 'remaining_budget',
                'expected_coverage', 'real_coverage'])
        else:
            self._df = pd.read_csv(self._log_file)
        return self._df

    def addRecord(self,
                  layout, expected_coverage, writeLog=False):
        self._df = self._df.append({
            'layout': layout,
            'total_budget': -1,
            'remaining_budget': -1,
            'expected_coverage': expected_coverage,
            'real_coverage': -1
            }, ignore_index=True)
        if writeLog:
            self.writeLog()

    def writeRealCoverage(self, results_df):
        max_walk_cycles = results_df['walk_cycles'].max()
        min_walk_cycles = results_df['walk_cycles'].min()
        delta_walk_cycles = max_walk_cycles - min_walk_cycles
        self._df['real_coverage'] = self._df['real_coverage'].astype(float)
        query = self._df.query('real_coverage == (-1)')
        for index, row in query.iterrows():
            layout = row['layout']
            walk_cycles = results_df.loc[results_df['layout'] == layout, 'walk_cycles'].iloc[0]
            real_coverage = (max_walk_cycles - walk_cycles) / delta_walk_cycles
            real_coverage *= 100
            self._df.loc[self._df['layout'] == layout, 'real_coverage'] = real_coverage
        self.writeLog()
        return self._df

    def calculateBudget(self):
        query = self._df.query('real_coverage == (-1)')
        if len(query) > 0:
            raise Exception('GroupsLog.calculateBudget was called before updating the groups real_coverage.')
        query = self._df.query('total_budget < 0')
        if len(query) == 0:
            return
        # sort the group layouts by walk-cycles/real_coverage
        self._df = self._df.sort_values('real_coverage', ascending=True)
        # calculate the diff between each two adjacent layouts
        # (call it delta[i] for the diff between group[i] and group[i+1])
        self._df['delta'] = self._df['real_coverage'].diff().abs()
        self._df['delta'] = self._df['delta'].fillna(0)
        total_deltas = self._df.query('delta > 2.5')['delta'].sum()
        total_budgets = 46 # 55-9: num_layouts(55) - groups_layouts(9)
        for index, row in self._df.iterrows():
            delta = row['delta']
            # for each delta < 2.5 assign budget=0
            if delta <= 2.5:
                budget = 0
            else:
                budget = int((delta / total_deltas) * total_budgets)
            self._df.at[index, 'total_budget'] = budget
            self._df.at[index, 'remaining_budget'] = budget
        self.writeLog()

    def decreaseRemainingBudget(self, layout):
        self._df.loc[self._df['layout'] == layout, 'remaining_budget'] = self._df.loc[self._df['layout'] == layout, 'remaining_budget']-1
        self.writeLog()

    def writeLog(self):
        self._df.to_csv(self._log_file, index=False)

    def _getField(self, layout, field):
        field_val = self._df.loc[self._df['layout'] == layout, field]
        field_val = field_val.to_list()
        if field_val == []:
            return None
        else:
            return field_val[0]

    def getRealCoverage(self, layout):
        return self._getField(layout, 'real_coverage')

    def getExpectedCoverage(self, layout):
        return self._getField(layout, 'expected_coverage')

def writeLayoutAll2mb(layout, output):
    page_size = 1 << 21
    brk_pool_size = Utils.round_up(brk_footprint, page_size)
    configuration = Configuration()
    configuration.setPoolsSize(
            brk_size=brk_pool_size,
            file_size=1*Utils.GB,
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
            file_size=1*Utils.GB,
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

def buildGroupsSequentially(orig_pebs_df, exp_dir, desired_weights):
    pebs_df = orig_pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
    pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)
    groups = []
    all_pages = []
    i = 0
    epsilon = 3
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
            if current_total_weight > (desired_weights[i] + epsilon):
                found = False
                break
            elif current_total_weight > (desired_weights[i] - epsilon):
                found = True
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

def createGroups(pebs_df, exp_dir, write_layouts=True):
    i = 1
    desired_weights = [50, 20, 10]
    groups = []
    log = GroupsLog(exp_dir)
    # 1.1.1. create three groups of pages that are responsible for (50%, 20%, 10%)
    while len(groups) != 3:
        groups = buildGroupsSequentially(pebs_df, exp_dir, desired_weights)
        # if we could not find the required groups with current weights
        # then try to lower bound the desired weights
        desired_weights = [0.9*w for w in desired_weights]
    # 1.1.2. create eight layouts as all sub-groups of these three groups
    for subset_size in range(len(groups)+1):
        for subset in itertools.combinations(groups, subset_size):
            windows = []
            for l in subset:
                windows += l
            layout_name = 'layout' + str(i)
            i += 1
            expected_coverage = calculateTlbCoverage(pebs_df, windows)
            print(layout_name)
            print('#hugepages: '+ str(len(windows)))
            print('weight: ' + str(expected_coverage))
            print('hugepages: ' + str(windows))
            print('---------------')
            if write_layouts:
                writeLayout(layout_name, windows, exp_dir)
            log.addRecord(layout_name, expected_coverage)
    # 1.1.3. create additional layout in which all pages are backed with 2MB
    layout_name = 'layout' + str(i)
    print(layout_name)
    print('weight: 100%')
    print('hugepages: all pages')
    if write_layouts:
        writeLayoutAll2mb(layout_name, exp_dir)
    log.addRecord(layout_name, 100)
    log.writeLog()

def findTlbCoverageWindows(df, tlb_coverage_percentage, epsilon):
    windows = []
    total_weight = 0
    for index, row in df.iterrows():
        weight = row['NUM_ACCESSES']
        page_number = row['PAGE_NUMBER']
        if (total_weight + weight) <= (tlb_coverage_percentage + epsilon):
            #print('page: {page} - weight: {weight}'.format(page=page_number, weight=weight))
            total_weight += weight
            windows.append(page_number)
        if total_weight >= (tlb_coverage_percentage - epsilon):
            break

    if total_weight > (tlb_coverage_percentage + epsilon) \
            or total_weight < (tlb_coverage_percentage - epsilon):
        return []
    return windows

def createStatisLayouts(pebs_df, exp_dir, step_size):
    """ Creates 40 layouts statically:

    2.1.	Create 40 layouts statically:
        2.1.1.	such that each layout covers 2.5% of TLB-misses more than previous layout (according to PEBS)
        2.1.2.	for each layout log the following record:
            layout,	      right-layout, left-layout,	expected-coverage,	real-coverage
            <layout-name>,	0,	          0,	       <expected %>,	filled later (in 2.2)
    2.2.    createNextStaticLayout()
    """
    df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)
    tlb_coverage_percentage = 0
    num_layout = 1
    log = StaticLog(args.exp_dir)
    # 2.1. Create 40 layouts statically
    while tlb_coverage_percentage < 100:
        # 2.1.1. such that each layout covers 2.5% of TLB-misses more than previous layout (according to PEBS)
        windows = findTlbCoverageWindows(df, tlb_coverage_percentage, 0.5)
        print('TLB-coverage = {coverage} - Paegs = {pages}'.format(coverage=tlb_coverage_percentage, pages=windows))
        layout_name = 'layout'+str(num_layout)
        writeLayout(layout_name, windows, exp_dir)
        # 2.1.2. for each layout log the following record:
        log.addRecord(layout_name, 'TBD', 'TBD',
                       tlb_coverage_percentage)
        num_layout += 1
        tlb_coverage_percentage += step_size
    log.writeLog()

def createNextLayoutStatically(pebs_df, mean_file, layout, exp_dir):
    """ Creates layout based on the previous statically-created layouts
        (when the first-50-pages weight < 50%)
    2.1.	createStatisLayouts()
    2.2.	Create additional 15 layouts dynamically (in runtime):
        2.2.1.	collect their results
        2.2.2.	update the real-coverage in the log
        2.2.3.	calculate gaps between measurements
        2.2.4.	find the maximum gap:
            2.2.4.1.	find the two layouts of the gap’s two measurements (right and left)
            2.2.4.2.	scale the expected coverage according to the ratio between real coverages:
            real_coverage_delta = left_real_coverage - right_real_coverage
            exp_coverage_delta = left_exp_coverage - right_exp_coverage
            scale = exp_coverage_delta / real_coverage_delta
            new_delta = scale * 2.5
            2.2.4.3.	add new_delta coverage to the right layout
    """

    # 2.2. create additional 15 layouts dynamically (in runtime):
    # 2.2.1 collect their results
    results_df = loadDataframe(mean_file)
    # 2.2.2. update the real-coverage in the log
    log = StaticLog(args.exp_dir)
    #------------------------------------------------------------------------
    # TODO: remove the following copy process (from groups log to static log)
    # and replace it by running groups for the two methods and only then
    # run the specific algorithm of static or dynamic layouts allocation
    if log._df.empty and not results_df.empty:
        groups_log = GroupsLog(exp_dir)
        if groups_log._df.empty:
            createGroups(pebs_df, exp_dir, write_layouts=False)
        for index, row in groups_log._df.iterrows():
            log.addRecord(row['layout'], 'TBD', 'TBD', row['expected_coverage'])
        log.writeLog()
    #------------------------------------------------------------------------
    log.writeRealCoverage(results_df)
    # 2.2.3 calculate gaps between measurements
    results_df = results_df.sort_values('walk_cycles', ascending=False)
    # 2.2.4 find the maximum gap
    idx = results_df['walk_cycles'].diff().abs().argmax()
    # 2.2.4.1 find the two layouts of the gap’s two measurements (right and left)
    right_layout = results_df.iloc[idx-1]
    left_layout = results_df.iloc[idx]
    # 2.2.4.2 scale the expected coverage according to the ratio between real coverages
    left_real_coverage = log.getRealCoverage(left_layout['layout'])
    right_real_coverage = log.getRealCoverage(right_layout['layout'])
    real_coverage_delta = left_real_coverage - right_real_coverage
    left_exp_coverage = log.getExpectedCoverage(left_layout['layout'])
    right_exp_coverage = log.getExpectedCoverage(right_layout['layout'])
    exp_coverage_delta = left_exp_coverage - right_exp_coverage
    scale = exp_coverage_delta / real_coverage_delta
    new_delta = scale * 2.5
    # 2.2.4.3 add new_delta coverage to the right layout
    tlb_coverage_percentage = right_exp_coverage + new_delta
    windows = findTlbCoverageWindows(pebs_df, tlb_coverage_percentage, 0.5)
    print('TLB-coverage = {coverage} - Paegs = {pages}'.format(coverage=tlb_coverage_percentage, pages=windows))
    writeLayout(layout, windows, exp_dir)
    log.addRecord(layout, right_layout['layout'], left_layout['layout'], tlb_coverage_percentage, True)

def createNextDynamicLayoutStatically(pebs_df, mean_file, layout, exp_dir):
    # 2.2. create additional 15 layouts dynamically (in runtime):
    # 2.2.1 collect their results
    results_df = loadDataframe(mean_file)

    # 2.2.2. update the real-coverage in the log
    log = StaticLog(args.exp_dir)
    log.writeRealCoverage(results_df)

    # 2.2.3 calculate gaps between measurements
    #results_df = results_df.sort_values('walk_cycles', ascending=False)
    df = log._df.sort_values('real_coverage', ascending=True)

    # 2.2.4 find the maximum gap
    #idx = results_df['walk_cycles'].diff().abs().argmax()
    idx = df['real_coverage'].diff().abs().argmax()

    # 2.2.4.1 find the two layouts of the gap’s two measurements (right and left)
    #right_layout = results_df.iloc[idx-1]
    #left_layout = results_df.iloc[idx]
    right_layout = df.iloc[idx-1]
    left_layout = df.iloc[idx]

    # 2.2.4.2 scale the expected coverage according to the ratio between real coverages
    left_real_coverage = log.getRealCoverage(left_layout['layout'])
    right_real_coverage = log.getRealCoverage(right_layout['layout'])
    real_coverage_delta = left_real_coverage - right_real_coverage
    left_exp_coverage = log.getExpectedCoverage(left_layout['layout'])
    right_exp_coverage = log.getExpectedCoverage(right_layout['layout'])
    exp_coverage_delta = left_exp_coverage - right_exp_coverage
    scale = exp_coverage_delta / real_coverage_delta
    new_delta = scale * 2.5

    # 2.2.4.3 add new_delta coverage to the right layout
    tlb_coverage_percentage = abs(left_exp_coverage + right_exp_coverage)/2
    windows = findTlbCoverageWindows(pebs_df, tlb_coverage_percentage, 0.5)
    print('TLB-coverage = {coverage} - Paegs = {pages}'.format(coverage=tlb_coverage_percentage, pages=windows))
    writeLayout(layout, windows, exp_dir)
    log.addRecord(layout, right_layout['layout'], left_layout['layout'], tlb_coverage_percentage, True)

def createNextLayoutDynamically(pebs_df, mean_file, layout, exp_dir):
    # collect previous layouts results
    results_df = loadDataframe(mean_file)

    # calculate the real-coverage for each group and update the log
    groups_log = GroupsLog(exp_dir)
    if groups_log._df.empty:
        createGroups(pebs_df, exp_dir, write_layouts=False)
    groups_log.writeRealCoverage(results_df)
    groups_log.calculateBudget()

    # add layouts for each group staically
    static_log = StaticLog(exp_dir)
    for i in range(len(groups_log._df)-1):
        right_layout = groups_log._df.iloc[i]
        left_layout = groups_log._df.iloc[i+1]
        if left_layout['remaining_budget'] == 0:
            continue
        if left_layout['remaining_budget'] == left_layout['total_budget']:
            static_log.clear()
            static_log.addRecord(right_layout['layout'], 'TBD', 'TBD', right_layout['expected_coverage'])
            static_log.addRecord(left_layout['layout'], 'TBD', 'TBD', left_layout['expected_coverage'])
        groups_log.decreaseRemainingBudget(left_layout['layout'])
        static_log.writeLog()
        static_log.writeRealCoverage(results_df)
        createNextDynamicLayoutStatically(pebs_df, mean_file, layout, exp_dir)
        break

def buildGroupsSparsely(pebs_df, exp_dir, desired_weights):
    pebs_df.sort_values('NUM_ACCESSES', ascending=False, inplace=True)
    groups = []
    current_group = []
    current_total_weight = 0
    i = 0
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

def normalizePebsAccesses(pebs_mem_bins):
    # read mem-bins
    pebs_df = pd.read_csv(pebs_mem_bins, delimiter=',')

    # filter and eep only brk pool accesses
    pebs_df = pebs_df[pebs_df['PAGE_TYPE'].str.contains('brk')]
    if pebs_df.empty:
        sys.exit('Input file does not contain page accesses information about the brk pool!')
    pebs_df = pebs_df[['PAGE_NUMBER', 'NUM_ACCESSES']]
    pebs_df = pebs_df.reset_index()

    # transform NUM_ACCESSES from absolute number to percentage
    total_access = pebs_df['NUM_ACCESSES'].sum()
    pebs_df['NUM_ACCESSES'] = pebs_df['NUM_ACCESSES'].mul(100).divide(total_access)
    pebs_df = pebs_df.sort_values('NUM_ACCESSES', ascending=False)
    return pebs_df

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
parser.add_argument('-p', '--pebs_mem_bins', default='mem_bins_2mb.csv')
parser.add_argument('-l', '--layout', required=True)
parser.add_argument('-d', '--exp_dir', required=True)
parser.add_argument('-n', '--mean_file', required=True)
args = parser.parse_args()

# read memory-footprints
footprint_df = pd.read_csv(args.memory_footprint)
mmap_footprint = footprint_df['anon-mmap-max'][0]
brk_footprint = footprint_df['brk-max'][0]
last_page = int(brk_footprint / 4096)

pebs_df = normalizePebsAccesses(args.pebs_mem_bins)

headPagesWeight = pebs_df.iloc[0:50]['NUM_ACCESSES'].sum()
# 1. If first-50-pages weight > 50% then
if headPagesWeight > 50:
    print('[DEBUG]: sub-groups method')
    if args.layout == 'layout1':
        # 1.1. create nine layouts statically (using PEBS output):
        createGroups(pebs_df, args.exp_dir)
    else:
        # 1.2. create other layouts dynamically
        createNextLayoutDynamically(pebs_df, args.mean_file,
                                  args.layout, args.exp_dir)
# 2. else (first-50-pages weight < 50%) then
else:
    print('[DEBUG]: static method')
    if args.layout == 'layout1':
        # 2.1. create 40 layouts statically
        createStatisLayouts(pebs_df, args.exp_dir, 2.5)
    else:
        # 2.2. create additional 15 layouts dynamically (in runtime)
        createNextLayoutStatically(pebs_df, args.mean_file,
                               args.layout, args.exp_dir)



