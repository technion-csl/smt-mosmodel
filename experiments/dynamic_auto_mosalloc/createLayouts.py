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

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Log():
    def __init__(self, exp_dir, results_df, log_name, default_columns):
        self._exp_dir = exp_dir
        self._results_df = results_df
        self._log_file = self._exp_dir + '/' + log_name
        self._default_columns = default_columns
        self._df = self.readLog()

    def readLog(self):
        if not os.path.isfile(self._log_file):
            self._df = pd.DataFrame(columns=self._default_columns)
        else:
            self._df = pd.read_csv(self._log_file)
        return self._df

    def writeLog(self):
        self._df.to_csv(self._log_file, index=False)

    def clear(self):
        self._df = pd.DataFrame(columns=self._default_columns)

    def empty(self):
        return self._df.empty

    def getField(self, key_name, key_value, field_name):
        field_val = self._df.loc[self._df[key_name] == key_value, field_name]
        field_val = field_val.to_list()
        if field_val == []:
            return None
        else:
            return field_val[0]

    def getRealCoverage(self, layout):
        return self.getField('layout', layout, 'real_coverage')

    def getPebsCoverage(self, layout):
        return self.getField('layout', layout, 'pebs_coverage')

    def getLastRecord(self):
        if self.empty():
            return None
        return self._df.iloc[len(self._df)-1]

    def getLastLayoutName(self):
        """
        Returns
        -------
        string
            returns the name of the last layout in the state log.
        """
        last_record = self.getLastRecord()
        assert last_record is not None,'getLastLayoutName: there is no state records'
        return last_record['layout']

    def getRecord(self, key_name, key_value):
        record = self._df.query('{key} == "{value}"'.format(
            key=key_name,
            value=key_value))
        if record.empty:
            return None
        else:
            return record.iloc[0]

    def writeRealCoverage(self):
        max_walk_cycles = self._results_df['walk_cycles'].max()
        min_walk_cycles = self._results_df['walk_cycles'].min()
        delta_walk_cycles = max_walk_cycles - min_walk_cycles
        self._df['real_coverage'] = self._df['real_coverage'].astype(float)
        query = self._df.query('real_coverage == (-1)')
        for index, row in query.iterrows():
            layout = row['layout']
            walk_cycles = self._results_df.loc[self._results_df['layout'] == layout, 'walk_cycles'].iloc[0]
            real_coverage = (max_walk_cycles - walk_cycles) / delta_walk_cycles
            real_coverage *= 100
            self._df.loc[self._df['layout'] == layout, 'real_coverage'] = real_coverage
            self._df.loc[self._df['layout'] == layout, 'walk_cycles'] = walk_cycles
        self.writeLog()

class GroupsLog(Log, metaclass=Singleton):
    def __init__(self, exp_dir, results_df):
        default_columns = [
            'layout', 'total_budget', 'remaining_budget',
            'pebs_coverage', 'real_coverage', 'walk_cycles']
        super().__init__(exp_dir, results_df, 'groups.log', default_columns)

    def addRecord(self,
                  layout, pebs_coverage, writeLog=False):
        self._df = self._df.append({
            'layout': layout,
            'total_budget': -1,
            'remaining_budget': -1,
            'pebs_coverage': pebs_coverage,
            'real_coverage': -1,
            'walk_cycles': -1
            }, ignore_index=True)
        if writeLog:
            self.writeLog()

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
                budget = round((delta / total_deltas) * total_budgets)
            self._df.at[index, 'total_budget'] = budget
            self._df.at[index, 'remaining_budget'] = budget
        # fix total budgets due to rounding
        rounded_total_budgets = self._df['total_budget'].sum()
        delta_budget = total_budgets - rounded_total_budgets
        self._df.at[index, 'total_budget'] = budget + delta_budget
        self._df.at[index, 'remaining_budget'] = budget + delta_budget

        self.writeLog()

    def decreaseRemainingBudget(self, layout):
        self._df.loc[self._df['layout'] == layout, 'remaining_budget'] = self._df.loc[self._df['layout'] == layout, 'remaining_budget']-1
        self.writeLog()

    def zeroBudget(self, layout):
        self._df.loc[self._df['layout'] == layout, 'remaining_budget'] = 0
        self._df.loc[self._df['layout'] == layout, 'total_budget'] = 0
        self.writeLog()

    def addExtraBudget(self, layout, extra_budget):
        self._df.loc[self._df['layout'] == layout, 'remaining_budget'] = self._df.loc[self._df['layout'] == layout, 'remaining_budget']+extra_budget
        self._df.loc[self._df['layout'] == layout, 'total_budget'] = self._df.loc[self._df['layout'] == layout, 'total_budget']+extra_budget
        self.writeLog()

    def writeLog(self):
        self._df.to_csv(self._log_file, index=False)

class StateLog(Log):
    def __init__(self, exp_dir, results_df, right_layout, left_layout):
        default_columns = [
            'layout',
            'scan_method', 'scan_direction', 'scan_value', 'scan_base',
            'pebs_coverage', 'real_coverage', 'walk_cycles',
            'pages', 'offset']
        self._right_layout = right_layout
        self._left_layout = left_layout
        state_name = right_layout + '_' +left_layout
        super().__init__(exp_dir, results_df, state_name + '_state.log', default_columns)
        super().writeRealCoverage()

    def addRecord(self,
                  layout,
                  scan_method, scan_direction, scan_value, scan_base,
                  pebs_coverage, pages, offset,
                  writeLog=True):
        self._df = self._df.append({
            'layout': layout,
            'scan_method': scan_method,
            'scan_direction': scan_direction,
            'scan_value': scan_value,
            'scan_base': scan_base,
            'pebs_coverage': pebs_coverage,
            'pages': pages,
            'offset': offset,
            'real_coverage': -1,
            'walk_cycles': -1
            }, ignore_index=True)
        if writeLog:
            self.writeLog()

    def hasOnlyBaseLayouts(self):
        return self.getLastRecord()['scan_method'] == 'none'

    def getRightLayoutName(self):
        return self._right_layout

    def getLeftLayoutName(self):
        return self._left_layout

    def getRigthRecord(self):
        assert(not self.empty())
        return self.getRecord('layout', self.getRightLayoutName())

    def getLeftRecord(self):
        assert(not self.empty())
        return self.getRecord('layout', self.getLeftLayoutName())

    def isLastRecordInRange(self):
        #self.writeRealCoverage()
        last_layout = self.getLastRecord()
        right_layout = self.getRecord('layout', self.getRightLayoutName())
        assert(right_layout is not None)
        left_layout = self.getRecord('layout', self.getLeftLayoutName())
        assert(left_layout is not None)

        return right_layout['walk_cycles'] >= last_layout['walk_cycles'] and \
            last_layout['walk_cycles'] >= left_layout['walk_cycles']

    def getGapFromBase(self, layout, base_layout):
        layout_coverage = self.getRealCoverage(layout)
        assert(layout_coverage is not None)
        base_coverage = self.getRealCoverage(base_layout)
        assert(base_coverage is not None)

        print('--------------------------')
        print('last-layout = '+str(layout)+' , base_layout= '+str(base_layout))
        print('last-layout-coverage = '+str(layout_coverage)+' , base_layout_coverage= '+str(base_coverage))
        print('--------------------------')

        return layout_coverage - base_coverage

    def lastLayoutImprovedMaxGap(self):
        """
        Calculates if the last layout contributed to reducing the
        maximal gap in the current group

        Returns
        -------
        bool
            Returns True if the last layout reduced the maximal gap
            Returns False otherwise
        """
        #self.writeRealCoverage()
        including_df_diffs = self._df.sort_values('real_coverage', ascending=True)
        including_max_diff = including_df_diffs['real_coverage'].diff().max()

        excluding_df = self._df.iloc[0:len(self._df)-1]
        excluding_df_diffs = excluding_df.sort_values('real_coverage', ascending=True)
        excluding_max_diff = excluding_df_diffs['real_coverage'].diff().max()

        return including_max_diff < excluding_max_diff

    def lastLayoutImprovedGaps(self):
        """
        Calculates if the last layout contributed to reducing the total
        'big gaps', which are greater than 2.5%.

        Returns
        -------
        bool
            Returns True if the last layout reduced the sum of the '
            big gaps' or splitted one 'big gap' to two more smalled gaps.
            Returns False otherwise
        """
        #self.writeRealCoverage()
        including_df_diffs = self._df.sort_values('real_coverage', ascending=True)
        including_df_diffs['diff'] = including_df_diffs['real_coverage'].diff()
        including_df_diffs = including_df_diffs.query('diff > 2.5')

        excluding_df = self._df.iloc[0:len(self._df)-1]
        excluding_df_diffs = excluding_df.sort_values('real_coverage', ascending=True)
        excluding_df_diffs['diff'] = excluding_df_diffs['real_coverage'].diff()
        excluding_df_diffs = excluding_df_diffs.query('diff > 2.5')

        sum_diff = excluding_df_diffs['diff'].sum() - including_df_diffs['diff'].sum()
        count_diff = excluding_df_diffs['diff'].count() - including_df_diffs['diff'].count()

        return count_diff > 0 or sum_diff > 0

    def getGapBetweenLastRecordAndBase(self):
        #self.writeRealCoverage()
        last_layout = self.getLastRecord()
        base_layout = last_layout['scan_base']
        return self.getGapFromBase(last_layout['layout'], base_layout)

    def getBaseLayout(self, layout_name):
        return self.getField('layout', layout_name, 'scan_base')

    def getNextLayoutToIncrement(self, start_layout):
        max_coverage = self.getRealCoverage(self.getLeftLayoutName())
        #current_layout = self.getLastLayoutName()
        current_layout = start_layout
        current_coverage = self.getRealCoverage(current_layout)
        while current_coverage <= max_coverage:
            query = self._df.query(
                'real_coverage > {current} and real_coverage <= {next}'.format(
                    current = current_coverage,
                    next = current_coverage+3))
            if query.empty:
                break
            query = query.sort_values('real_coverage', ascending=False)
            current_layout = query.iloc[0]['layout']
            current_coverage = query.iloc[0]['real_coverage']
        return current_layout

    def getRootBaseLayout(self, layout):
        """
        Searches the state log, starting from the last record, to find the
        root base_layout that was used to get to the last record.

        Returns a layout that has no base layout, which the last record was
        derived from it
        """
        current_layout = layout
        base_layout = current_layout
        while base_layout != 'none':
            current_layout = base_layout
            base_layout = self.getBaseLayout(current_layout)
        return current_layout

    def getNewBaseLayoutName(self):
        """
        Returns a new layout to be used as a base for scanning the space
        and closing the gap between the right and left layouts of current
        state.
        The new base_layout is found by looking for a layout with the
        maximal gap that is greater than 2.5%
        """
        #self.writeRealCoverage()
        diffs = self._df.sort_values('real_coverage', ascending=True)
        diffs['diff'] = diffs['real_coverage'].diff().abs()

        idx_label = diffs['diff'].idxmax()
        idx = diffs.index.get_loc(idx_label)
        right = diffs.iloc[idx-1]
        left = diffs.iloc[idx]
        if max(right['diff'], left['diff']) <= 2.5:
            return None, None
        return right['layout'], left['layout']

class LayoutGenerator():
    def __init__(self, pebs_df, results_df, layout, exp_dir):
        self.pebs_df = pebs_df
        self.results_df = results_df
        self.layout = layout
        self.exp_dir = exp_dir
        self.groups_log = GroupsLog(exp_dir, results_df)
        self.state_log = None

    def generateLayout(self):
        if self.layout == 'layout1':
            # 1.1. create nine layouts statically (using PEBS output):
            self.createGroups()
        else:
            # 1.2. create other layouts dynamically
            self.createNextLayoutDynamically()

    def _buildGroupsSequentially(self, desired_weights, all_pages):
        pebs_df = self.pebs_df[['PAGE_NUMBER', 'TLB_COVERAGE']]
        pebs_df = pebs_df.sort_values('TLB_COVERAGE', ascending=False)
        groups = []
        i = 0
        for index, row in pebs_df.iterrows():
            current_total_weight = 0
            current_group = []

            page_number = int(row['PAGE_NUMBER'])
            if page_number in all_pages:
                continue

            weight = row['TLB_COVERAGE']

            epsilon = desired_weights[i] * 0.1
            if weight > (desired_weights[i] + epsilon):
                continue

            group_max_pages = 50
            max_page = page_number + int(group_max_pages/2)
            min_page = page_number - int(group_max_pages/2)
            query = pebs_df.query(
                'PAGE_NUMBER <= {max_page} and PAGE_NUMBER >= {min_page} and PAGE_NUMBER not in {all_pages}'.format(
                    max_page=max_page,
                    min_page=min_page,
                    all_pages=all_pages))
            if query['TLB_COVERAGE'].sum() < (desired_weights[i] - epsilon):
                continue
            query_df = query.sort_values('PAGE_NUMBER', ascending=True).reset_index()
            query_df = query_df[['PAGE_NUMBER', 'TLB_COVERAGE']]

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

    def createGroups(self, write_layouts=True):
        i = 1
        desired_weights = [56, 28, 14]
        groups = []
        groups_pages = []
        # 1.1.1. create three groups of pages that are responsible for (50%, 20%, 10%)
        while len(groups) != 3:
            g = self._buildGroupsSequentially(desired_weights, groups_pages)
            groups += g
            desired_weights = desired_weights[len(g):len(desired_weights)]
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
                pebs_coverage = LayoutGeneratorUtils.calculateTlbCoverage(pebs_df, windows)
                print(layout_name)
                print('#hugepages: '+ str(len(windows)))
                print('weight: ' + str(pebs_coverage))
                print('hugepages: ' + str(windows))
                print('---------------')
                if write_layouts:
                    LayoutGeneratorUtils.writeLayout(layout_name, windows, self.exp_dir)
                self.groups_log.addRecord(layout_name, pebs_coverage)
        # 1.1.3. create additional layout in which all pages are backed with 2MB
        layout_name = 'layout' + str(i)
        print(layout_name)
        print('weight: 100%')
        print('hugepages: all pages')
        if write_layouts:
            LayoutGeneratorUtils.writeLayoutAll2mb(layout_name, self.exp_dir)
        self.groups_log.addRecord(layout_name, 100)
        self.groups_log.writeLog()

    def _updateLogs(self):
        # calculate the real-coverage for each group and update the log
        # if the groups-log was not created yet then create it based on the
        # current results (this could happen if we started with the static
        # method and then decided to move to the dynamic method due to irregual
        # layouts real coverage, i.e. increasing the coverage causes to increasing
        # the walk cycles)
        if self.groups_log.empty():
            results_df_sorted = results_df.sort_values('walk_cycles',
                                                       ascending=False)
            for index, row in results_df_sorted.iterrows():
                self.groups_log.addRecord(row['layout'], -1)
            self.groups_log.writeRealCoverage()
            # filter out all layouts that already have small gaps
            self.groups_log._df = self.groups_log._df.query('real_coverage > 2.5')
            self.groups_log._df = self.groups_log._df.sort_values('real_coverage')
            self.groups_log.writeLog()
        else:
            self.groups_log.writeRealCoverage()
        # calculate the budget that will be given for each group
        self.groups_log.calculateBudget()

        extra_budget = 0
        # find the first group that still has a remaining budget
        for i in range(len(self.groups_log._df)-1):
            right_layout = self.groups_log._df.iloc[i]
            left_layout = self.groups_log._df.iloc[i+1]
            # if already consumed the total budget then move to next group
            remaining_budget = left_layout['remaining_budget']
            if remaining_budget == 0:
                continue
            # if there is an extra budget that remained---and not used---from
            # previous group, then add it to current group
            if extra_budget > 0:
                self.groups_log.addExtraBudget(left_layout['layout'], extra_budget)
                extra_budget = 0
            # initialize the state-log for the current group
            self.state_log = StateLog(self.exp_dir,
                                      self.results_df,
                                      right_layout['layout'],
                                      left_layout['layout'])
            # if the state log is empty then it seems just now we are
            # about to start scanning this group
            if self.state_log.empty():
                break
            # else, this is not the first layout in this group
            next_layout = self.state_log.getNextLayoutToIncrement(
                right_layout['layout'])
            # if we already closed all gaps in this group then move the
            # left budget to the next group
            if next_layout == left_layout['layout']:
                print('[DEBUG] closed all gaps before consuming all available budget, moving the remaining budget to the next group')
                extra_budget += remaining_budget
                self.groups_log.zeroBudget(left_layout['layout'])
                continue
            else:
                break

        assert left_layout['remaining_budget'] > 0, 'already consumed all groups budgest but still have additional layouts to create!'


        # if the state was not created yet then create it and add all
        # layouts that in the range [left_layout - right_layout]
        if self.state_log.empty():
            # if the state was not created before then this layout should
            # have a full budget (its budget should still unused)
            assert(left_layout['remaining_budget'] == left_layout['total_budget'])
            state_layouts = results_df.query(
                'walk_cycles >= {left} and walk_cycles <= {right}'.format(
                    left=left_layout['walk_cycles'],
                    right=right_layout['walk_cycles']))
            for index, row in state_layouts.iterrows():
                layout_name = row['layout']
                pages, offset = LayoutGeneratorUtils.getLayoutHugepages(
                    layout_name, self.exp_dir)
                pebs_coverage = LayoutGeneratorUtils.calculateTlbCoverage(
                    self.pebs_df, pages)
                self.state_log.addRecord(layout_name,
                                         'none', 'none', -1, 'none',
                                         pebs_coverage, pages, offset)
            self.state_log.writeLog()
            self.state_log.writeRealCoverage()

    def _addTailPages(self, base_layout, desired_coverage):
        # TODO get the base pages from the state log instead of reading them
        # get the base
        start_from_tail = True
        base_layout_pages, offset = LayoutGeneratorUtils.getLayoutHugepages(
            base_layout, self.exp_dir)
        new_layout_pages, actual_pebs_coverage = LayoutGeneratorUtils.findTlbCoverageWindows(
            self.pebs_df, desired_coverage, start_from_tail, base_layout_pages)
        return new_layout_pages, actual_pebs_coverage

    def createNextLayoutDynamically(self):
        assert self.results_df is not None,'results mean file does not exist'
        # fill or update GroupsLog and StateLog
        self._updateLogs()
        print('==============================================')
        print(self.state_log._df)
        print('----------------------------------------------')

        # initialize required values with None
        base_layout = desired_coverage = pages = pebs_coverage = how = None

        # is this the first layout to be generated for the current group
        if self.state_log.hasOnlyBaseLayouts():
            base_layout = self.state_log.getNextLayoutToIncrement(
                self.state_log.getRightLayoutName())
            desired_coverage = self.state_log.getPebsCoverage(base_layout) + 2.5
            how = 'increment'
        else:
            last_layout = self.state_log.getLastLayoutName()
            last_layout_pebs = self.state_log.getPebsCoverage(last_layout)
            last_increment = self.state_log.getGapBetweenLastRecordAndBase()

            # last laout was incremented by < 3%
            # there are two cases here: less than 2% or btween 2% and 3%
            if last_increment <= 3:
                base_layout = last_layout
                how = 'increment'
                # find next base layout by start looking from the last layout
                # until finding the first layout with a gap > 3
                next_layout = self.state_log.getNextLayoutToIncrement(last_layout)
                if next_layout == last_layout:
                    # last laout was incremented by < 2%
                    if last_increment < 2:
                        desired_coverage =  last_layout_pebs + (2.5 - last_increment) + 2.5
                    # last laout was incremented by 2%-3%
                    else:
                        desired_coverage = last_layout_pebs + 2.5
                # the last layout seems to have next layout(s) with gap
                # less than 3%, then we should move to the last one of
                # these layouts as our new base layout
                else:
                    base_layout = next_layout
                    base_layout_pebs = self.state_log.getPebsCoverage(base_layout)
                    desired_coverage = base_layout_pebs + 2.5
            # last laout was incremented by > 3%
            else:
                last_layout_base = self.state_log.getBaseLayout(last_layout)
                base_layout = last_layout_base
                base_layout_pebs = self.state_log.getPebsCoverage(base_layout)
                delta = last_layout_pebs - base_layout_pebs
                delta = 1 if delta < 1 else delta
                desired_coverage =  base_layout_pebs + (delta / 2)
                how = 'decrement'

        pages, pebs_coverage = self._addTailPages(
            base_layout, desired_coverage)
        assert base_layout is not None
        assert desired_coverage is not None
        assert pages is not None
        assert pebs_coverage is not None
        assert how is not None
        self.state_log.addRecord(self.layout,
                                 'tail', how, desired_coverage, base_layout,
                                 pebs_coverage, pages, 0)
        print('----------------------------------------------')
        print(self.state_log._df)
        print('==============================================')
        print(self.layout)
        print('#hugepages: '+ str(len(pages)))
        print('weight: ' + str(pebs_coverage))
        print('==============================================')
        # write the layout configuration file
        LayoutGeneratorUtils.writeLayout(self.layout, pages, self.exp_dir)
        # decrease current group's budget by 1
        self.groups_log.decreaseRemainingBudget(
            self.state_log.getLeftLayoutName())

class LayoutGeneratorUtils(metaclass=Singleton):
    def __init__(self):
        pass

    def loadDataframe(mean_file):
        if not os.path.isfile(mean_file):
            return None
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

    def findTlbCoverageWindows(
            pebs_df, tlb_coverage_percentage, start_from_tail, base_pages=[]):

        # start from the given base layout
        windows = base_pages.copy()
        total_weight = LayoutGeneratorUtils.calculateTlbCoverage(pebs_df, windows)
        assert tlb_coverage_percentage >= total_weight,'findTlbCoverageWindows: the required tlb-coverage is less than base pages coverage'
        remainder_coverage = tlb_coverage_percentage - total_weight
        # filter the PEBS dataframe to contain only relevant pages, i.e.,
        # pages that are not in the base-layout and their weight/coverage
        # is less than the desired weight/coverage
        df = pebs_df.query(
            'TLB_COVERAGE <= {target_coverage} and PAGE_NUMBER not in {pages}'.format(
                target_coverage=remainder_coverage,
                pages=windows))
        # sort ascendingly if we need to find tail pages
        df = df.sort_values('TLB_COVERAGE', ascending=start_from_tail)

        epsilon = 0.1
        pages = None
        coverage = 0
        while pages is None:
            pages, coverage = LayoutGeneratorUtils._findTlbCoverageWindows(
                df, remainder_coverage, epsilon)
            epsilon += 0.1
            if epsilon > 0.5:
                break
        assert pages is not None,'could not find hugepages that covers the required percentage'
        windows += pages
        total_weight += coverage
        return windows, total_weight

    def _findTlbCoverageWindows(
            df, tlb_coverage_percentage, epsilon):
        total_weight = 0
        windows = []
        for index, row in df.iterrows():
            weight = row['TLB_COVERAGE']
            page_number = row['PAGE_NUMBER']
            if (total_weight + weight) <= (tlb_coverage_percentage + epsilon):
                total_weight += weight
                windows.append(page_number)
            if total_weight >= (tlb_coverage_percentage - epsilon):
                break

        if total_weight > (tlb_coverage_percentage + epsilon) \
                or total_weight < (tlb_coverage_percentage - epsilon):
            return None, 0
        return windows, total_weight

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

    def writeLayout(layout, windows, output, sliding_index=0):
        page_size = 1 << 21
        hugepages_start_offset = sliding_index * 4096
        brk_pool_size = Utils.round_up(brk_footprint, page_size) + hugepages_start_offset
        configuration = Configuration()
        configuration.setPoolsSize(
                brk_size=brk_pool_size,
                file_size=1*Utils.GB,
                mmap_size=mmap_footprint)
        for w in windows:
            configuration.addWindow(
                    type=configuration.TYPE_BRK,
                    page_size=page_size,
                    start_offset=(w * page_size) + hugepages_start_offset,
                    end_offset=((w+1) * page_size) + hugepages_start_offset)
        configuration.exportToCSV(output, layout)

    def getLayoutHugepages(layout_name, exp_dir):
        layout_file = str.format('{exp_root}/layouts/{layout_name}.csv',
                exp_root=exp_dir,
                layout_name=layout_name)
        df = pd.read_csv(layout_file)
        df = df[df['type'] == 'brk']
        df = df[df['pageSize'] == 2097152]
        pages = []
        offset_deviation = 0
        for index, row in df.iterrows():
            start_page = int(row['startOffset'] / 2097152)
            end_page = int(row['endOffset'] / 2097152)
            offset_deviation = int(row['startOffset'] % 2097152)
            for i in range(start_page, end_page, 1):
                pages.append(i)
        start_deviation = offset_deviation / 4096
        return pages, start_deviation

    def calculateTlbCoverage(pebs_df, pages):
        total_weight = pebs_df.query(
                'PAGE_NUMBER in {pages}'.format(pages=pages))\
                        ['TLB_COVERAGE'].sum()
        return total_weight

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
        pebs_df['TLB_COVERAGE'] = pebs_df['NUM_ACCESSES'].mul(100).divide(total_access)
        pebs_df = pebs_df.sort_values('TLB_COVERAGE', ascending=False)
        return pebs_df


import argparse
def __parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--memory_footprint', default='memory_footprint.txt')
    parser.add_argument('-p', '--pebs_mem_bins', default='mem_bins_2mb.csv')
    parser.add_argument('-l', '--layout', required=True)
    parser.add_argument('-d', '--exp_dir', required=True)
    parser.add_argument('-n', '--mean_file', required=True)
    return parser.parse_args()

if __name__ == "__main__":
    args = __parseArguments()

    # read memory-footprints
    footprint_df = pd.read_csv(args.memory_footprint)
    mmap_footprint = footprint_df['anon-mmap-max'][0]
    brk_footprint = footprint_df['brk-max'][0]

    results_df = LayoutGeneratorUtils.loadDataframe(args.mean_file)

    pebs_df = LayoutGeneratorUtils.normalizePebsAccesses(args.pebs_mem_bins)

    layout_generator = LayoutGenerator(pebs_df, results_df, args.layout, args.exp_dir)
    layout_generator.generateLayout()
