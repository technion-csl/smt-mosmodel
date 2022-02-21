#!/usr/bin/env python3
import sys
import os
import pandas as pd
import itertools
import os.path
from logs import *

sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from Utils.utils import Utils
from Utils.ConfigurationFile import Configuration

sys.path.append(os.path.dirname(sys.argv[0])+"/../../analysis")
from performance_statistics import PerformanceStatistics

INCREMENT = (MAX_GAP / 2)
LOW_GAP = (MAX_GAP / 4)
DEFAULT_FACTOR = 1.5

class LayoutGenerator():
    def __init__(self, pebs_df, results_df, layout, exp_dir):
        self.pebs_df = pebs_df
        self.results_df = results_df
        self.layout = layout
        self.exp_dir = exp_dir
        self.subgroups_log = SubgroupsLog(exp_dir, results_df)
        self.state_log = None

    def generateLayout(self):
        if self.layout == 'layout1':
            # 1.1. create nine layouts statically (using PEBS output):
            self.createInitialLayoutsStatically()
        else:
            # 1.2. create other layouts dynamically
            self.createNextLayoutDynamically()

    def createInitialLayoutsStatically(self):
        group = self.createGroup()
        self.createSubgroups(group)

    def createGroup(self):
        # desired weights for each group layout
        desired_weights = [56, 28, 14]
        df = self.pebs_df.sort_values('TLB_COVERAGE', ascending=False)
        return self.fillBuckets(df, desired_weights, False)
        '''
        g1 = self.fillBuckets(df, desired_weights, True)
        g1_pages = g1[0] + g1[1] + g1[2]

        df = df.query(f'PAGE_NUMBER not in {g1_pages}')
        df = df.sort_values('TLB_COVERAGE', ascending=True)
        g2 = self.fillBuckets(df, desired_weights, False)

        group = [g1[i]+g2[i] for i in range(len(g1))]

        return group
        '''

    def fillBuckets(self, df, buckets, fill_only_one_slot=False):
        group = [[], [], []]
        i = 0
        for index, row in df.iterrows():
            page = row['PAGE_NUMBER']
            weight = row['TLB_COVERAGE']
            completed_buckets = [0, 0, 0]
            for k in range(3):
                # skip and count buckets that already filled out
                if buckets[i] <= 0:
                    completed_buckets[i] = 1
                    i = (i + 1) % 3
                # if current page can be added to current bucket then add it
                elif buckets[i] - weight >= -2:
                    if fill_only_one_slot:
                        if completed_buckets[i] == 1:
                            continue
                        completed_buckets[i] = 1
                    group[i].append(page)
                    buckets[i] -= weight
                    i = (i + 1) % 3
                    break
            if sum(completed_buckets) == 3:
                break
        return group

    def createSubgroups(self, group):
        total_pages = len(self.pebs_df)
        i = 1
        # 1.1.2. create eight layouts as all subgroups of these three group layouts
        for subset_size in range(len(group)+1):
            for subset in itertools.combinations(group, subset_size):
                windows = []
                for l in subset:
                    windows += l
                layout_name = f'layout{i}'
                i += 1
                pebs_coverage = LayoutGeneratorUtils.calculateTlbCoverage(self.pebs_df, windows)
                print(layout_name)
                print('#hugepages: {num} (~{percent}%) out of {total}'.format(
                    num=len(windows),
                    percent=round(len(windows)/total_pages * 100),
                    total=total_pages))
                print(f'weight: {pebs_coverage}')
                print(f'hugepages: {windows}')
                print('---------------')
                LayoutGeneratorUtils.writeLayout(layout_name, windows, self.exp_dir)
                self.subgroups_log.addRecord(layout_name, pebs_coverage)
        # 1.1.3. create additional layout in which all pages are backed with 2MB
        layout_name = f'layout{i}'
        print(layout_name)
        print('weight: 100%')
        print('hugepages: all pages')
        LayoutGeneratorUtils.writeLayoutAll2mb(layout_name, self.exp_dir)
        self.subgroups_log.addRecord(layout_name, 100)
        self.subgroups_log.writeLog()

    def updateSubgroupsLog(self):
        # calculate the real-coverage for each group and update the log
        # if the subgroups-log was not created yet then create it based on the
        # current results
        subgroups_layouts = ['layout1', 'layout2','layout3', 'layout4','layout5','layout6','layout7','layout8','layout9']
        if self.subgroups_log.empty():
            results_df_sorted = self.results_df.query(
                    f'layout in {subgroups_layouts}').sort_values(
                            'walk_cycles', ascending=False)
            for index, row in results_df_sorted.iterrows():
                #TODO update pebs coverage for subgroups
                self.subgroups_log.addRecord(row['layout'], -1)
            self.subgroups_log.writeRealCoverage()
            self.subgroups_log.df = self.subgroups_log.df.sort_values('real_coverage')
            self.subgroups_log.writeLog()
        else:
            self.subgroups_log.writeRealCoverage()
        # calculate the budget that will be given for each group
        self.subgroups_log.calculateBudget()

    def findNextSubgroup(self):
        found = False
        # find the first group that still has a remaining budget
        for i in range(len(self.subgroups_log.df)-1):
            right_layout = self.subgroups_log.df.iloc[i]
            left_layout = self.subgroups_log.df.iloc[i+1]
            # initialize the state-log for the current group
            self.state_log = StateLog(self.exp_dir,
                                      self.results_df,
                                      right_layout['layout'],
                                      left_layout['layout'])
            # if the state log is empty then it seems just now we are
            # about to start scanning this group
            if self.state_log.empty():
                self.initializeStateLog(right_layout, left_layout)
            # update state log real coverage for current and previous completed subsubgroups
            else:
                self.state_log.writeRealCoverage()
            # if we already closed all gaps in this group then move the
            # left budget to the next group
            next_layout, base_layout = self.state_log.getNextLayoutToIncrement(
                right_layout['layout'])
            if next_layout is None and base_layout is None:
                print('===========================================================')
                print(f'[DEBUG] closed all gaps for subgroup: {right_layout["layout"]} - {left_layout["layout"]}')
                print('===========================================================')
                self.subgroups_log.zeroBudget(left_layout['layout'])
                continue
            extra_budget = MAX_TRIALS - (self.subgroups_log.getTotalBudget() + 9)
            # if already consumed the total budget then move to next group
            remaining_budget = left_layout['remaining_budget']
            if (remaining_budget + extra_budget) == 0:
                print('===========================================================')
                print(f'[DEBUG] consumed all budget (but still have gaps to close) for subgroup: {right_layout["layout"]} - {left_layout["layout"]}')
                print('===========================================================')
                continue
            # if there is an extra budget that remained---and not used---from
            # previous group, then add it to current group
            if extra_budget > 0:
                self.subgroups_log.addExtraBudget(left_layout['layout'], extra_budget)
            found = True
            break
        print('===========================================================')
        if found:
            print(f'[DEBUG] start closing gaps for subgroup: {right_layout["layout"]} - {left_layout["layout"]}')
        else:
            print('[DEBUG] could not find subgroup to close its gaps')
        print('===========================================================')

        return found

    def updateLogs(self):
        self.updateSubgroupsLog()
        found = self.findNextSubgroup()
        if not found:
            # second trial to make sure that passed remaining budget
            # can be reused again for some previous subgroup
            found = self.findNextSubgroup()
        if not found:
            extra_budget = MAX_TRIALS - (self.subgroups_log.getTotalBudget() + 9)
            print(f'finished the last group but there is still ({extra_budget}) remaining budget.')
            print('using the remaining budget to look for previous groups that have more gaps to close')
            right = self.subgroups_log.getRightmostLayout()
            left = self.subgroups_log.getLeftmostLayout()

            if extra_budget > 0:
                self.subgroups_log.addExtraBudget(left['layout'], 1)

            self.state_log = StateLog(self.exp_dir,
                                      self.results_df,
                                      right['layout'], left['layout'])
            if self.state_log.empty():
                self.initializeStateLog(right, left)
            self.improveMaxGapFurthermore()
            return False
        # return True, which means that there is some subgroup to be improved (close its gaps)
        return True

    def improveMaxGapFurthermore(self):
        print(self.state_log.df)
        how = 'reduce-max'
        right, left = self.state_log.getMaxGapLayouts()
        max_gap = abs(self.state_log.getRealCoverage(right) - self.state_log.getRealCoverage(left))
        print(f'[DEBUG]: >>>>>>>>>> current max-gap: {max_gap} <<<<<<<<<<')
        base_layout = right
        last_record = self.state_log.getLastRecord()
        if last_record['scan_direction'] == 'reduce-max' and abs(last_record['expected_real_coverage'] - last_record['real_coverage']) >= max_gap:
            factor = last_record['scan_factor'] * 2
        else:
            factor = self.state_log.getLayoutScanFactor(base_layout) + 1
        expected_real_coverage = (self.state_log.getRealCoverage(right) + self.state_log.getRealCoverage(left)) / 2
        pages, pebs_coverage = self.addPagesByFactor(left, base_layout, factor)
        if pages is None:
            desired_real_coverage = (self.state_log.getRealCoverage(right) + self.state_log.getRealCoverage(left)) / 2
            pages, pebs_coverage = self.removePagesV2(left, None, desired_real_coverage)
            how = f'remove'
        assert pages is not None
        LayoutGeneratorUtils.writeLayout(self.layout, pages, self.exp_dir)
        self.state_log.addRecord(self.layout, how,
                                 factor, base_layout,
                                 pebs_coverage, expected_real_coverage,
                                 base_layout, pages)
        # decrease current group's budget by 1
        self.subgroups_log.decreaseRemainingBudget(
            self.state_log.getLeftLayoutName())

    def initializeStateLog(self, right_layout, left_layout):
        # if the state was not created yet then create it and add all
        # layouts that in the range [left_layout - right_layout]
        if self.state_log.empty():
            # if the state was not created before then this layout should
            # have a full budget (its budget should still unused)
            #assert(left_layout['remaining_budget'] == left_layout['total_budget'])
            state_layouts = self.results_df.query(
                'walk_cycles >= {left} and walk_cycles <= {right}'.format(
                    left=left_layout['walk_cycles'],
                    right=right_layout['walk_cycles']))
            state_layouts = state_layouts.sort_values('walk_cycles', ascending=False)
            #for layout_name in [right_layout['layout'], left_layout['layout']]:
            for index, row in state_layouts.iterrows():
                layout_name = row['layout']
                pages = LayoutGeneratorUtils.getLayoutHugepages(
                    layout_name, self.exp_dir)
                pebs_coverage = LayoutGeneratorUtils.calculateTlbCoverage(
                    self.pebs_df, pages)
                base = 'other'
                if layout_name == self.state_log.getRightLayoutName() or layout_name == self.state_log.getLeftLayoutName():
                    base = 'none'
                self.state_log.addRecord(layout_name,
                                         'none', 1, base,
                                         pebs_coverage, -1, 'none',
                                         pages)
            self.state_log.writeLog()
            self.state_log.writeRealCoverage()

    def getWorkingSetPages(self):
        right_layout = self.state_log.getRigthRecord()['layout']
        left_layout = self.state_log.getLeftRecord()['layout']

        right = LayoutGeneratorUtils.getLayoutHugepages(right_layout, self.exp_dir)
        right_set = set(right)
        left = LayoutGeneratorUtils.getLayoutHugepages(left_layout, self.exp_dir)
        left_set = set(left)

        pebs_set = set(self.pebs_df['PAGE_NUMBER'].to_list())
        all_set = left_set | right_set | pebs_set

        union_set = left_set | right_set
        union = list(union_set)
        intersection = list(left_set & right_set)
        only_in_left = list(left_set - right_set)
        only_in_right = list(right_set - left_set)
        not_in_right = list(all_set - right_set)

        #assert (len(only_in_left) == 0 and len(only_in_right) > 0), f'Unexpected behavior: the left layout ({left["layout"]}) is included in the right layout ({right["layout"]})'
        #print('******************************************')

        not_in_pebs = list(all_set - pebs_set)
        out_union_based_on_pebs = list(pebs_set - union_set)
        out_union = list(all_set - union_set)


        return out_union, only_in_left, not_in_right

    def getNextFactor(self):
        last_increment = self.state_log.getGapBetweenLastRecordAndIncrementBase()
        last_record = self.state_log.getLastRecord()
        last_factor = last_record['scan_factor']

        if last_record['scan_direction'] == 'add':
            if last_increment < 0.1:
                factor = 3
            elif last_increment < LOW_GAP:
                factor = min(3, (INCREMENT / last_increment))
            elif last_increment <= MAX_GAP:
                factor = 1
            else:
                factor = max(0.5, (INCREMENT / last_increment))
            factor = last_factor * factor
        else:
            if last_increment < LOW_GAP:
                factor = min(3, (INCREMENT / last_increment))
                factor = last_factor / factor
            elif last_increment <= MAX_GAP:
                factor = max(last_factor - 2, 1)
            else:
                factor = min(2, (last_increment / INCREMENT))
                factor = last_factor * factor
        return factor

    def addPagesFromWorkingSet(self, base_layout, working_set, desired_pebs_coverage, tail=True):
        pages = None
        max_epsilon = 0.5

        base_layout_pebs = self.state_log.getPebsCoverage(base_layout)
        base_layout_pages = LayoutGeneratorUtils.getLayoutHugepages(base_layout, self.exp_dir)

        working_set_df = self.pebs_df.query(f'PAGE_NUMBER in {working_set} and PAGE_NUMBER not in {base_layout_pages}')
        if len(working_set_df) == 0:
            print(f'[DEBUG]: there is no more pages in pebs that can be added to {base_layout}')
            return None, 0

        candidate_pebs_coverage = working_set_df['TLB_COVERAGE'].sum()
        print(f'[DEBUG]: trying to add pages to {base_layout} from a working-set of {len(working_set)} pages')
        print(f'[DEBUG]: working-set length after fitering out base pages is {len(working_set_df)} pages')
        print(f'[DEBUG]: working-set total coverage: {candidate_pebs_coverage} and desired coverage is: {desired_pebs_coverage:.3f}')

        tail_head_order='tail' if tail else 'head'
        print(f'[DEBUG]: addPagesFromWorkingSet: trying to add {tail_head_order} pages to {base_layout} to get a coverage of : {desired_pebs_coverage:.3f}')

        candidate_pebs_coverage = working_set_df['TLB_COVERAGE'].sum()
        if candidate_pebs_coverage + base_layout_pebs < desired_pebs_coverage - max_epsilon:
            return None, 0

        epsilon = 0
        while pages is None or self.pagesSetExist(pages):
            epsilon += 0.1
            if epsilon > max_epsilon:
                break
            max_pebs = desired_pebs_coverage + epsilon
            min_pebs = desired_pebs_coverage
            pages, pebs = self.__addPagesFromWorkingSet(base_layout, working_set_df, min_pebs, max_pebs, tail)
        epsilon = 0
        while pages is None or self.pagesSetExist(pages):
            epsilon += 0.1
            if epsilon > max_epsilon:
                break
            min_pebs = desired_pebs_coverage - epsilon
            if min_pebs <= base_layout_pebs:
                min_pebs = desired_pebs_coverage
            max_pebs = desired_pebs_coverage
            pages, pebs = self.__addPagesFromWorkingSet(base_layout, working_set_df, min_pebs, max_pebs, tail)

        if pages is not None:
            added_pages_len = len(set(pages) - set(base_layout_pages))
            print(f'[DEBUG]: total added pages to {base_layout}: {added_pages_len}')
            print(f'[DEBUG]: new layout coverage: {pebs}')

        return pages, pebs

    def __addPagesFromWorkingSet(self, base_layout, working_set_df, min_pebs_coverage, max_pebs_coverage, tail=True):
        base_layout_pages = LayoutGeneratorUtils.getLayoutHugepages(base_layout, self.exp_dir)
        base_layout_pebs_coverage = self.state_log.getPebsCoverage(base_layout)

        assert min_pebs_coverage > base_layout_pebs_coverage

        df = working_set_df.sort_values('TLB_COVERAGE', ascending=tail)

        added_pages = []
        total_weight = base_layout_pebs_coverage
        for index, row in df.iterrows():
            page = row['PAGE_NUMBER']
            weight = row['TLB_COVERAGE']
            updated_total_weight = total_weight + weight
            if updated_total_weight < max_pebs_coverage:
                added_pages.append(page)
                total_weight = updated_total_weight
            if max_pebs_coverage >= total_weight >= min_pebs_coverage:
                break
        if len(added_pages) == 0:
            return None, 0
        new_pages = base_layout_pages + added_pages
        new_pages.sort()
        new_pebs_coverage = self.pebs_df.query(f'PAGE_NUMBER in {new_pages}')['TLB_COVERAGE'].sum()

        return new_pages, new_pebs_coverage

    def removePagesByFactor(self, right, left, factor):
        factor = int(factor)
        print(f'[DEBUG]: removing pages from {left} to get close to {right} by a factor: {factor}')
        assert factor >= 2

        left_pages = LayoutGeneratorUtils.getLayoutHugepages(left, self.exp_dir)
        right_pages = LayoutGeneratorUtils.getLayoutHugepages(right, self.exp_dir)

        candidate_pages = list(set(left_pages) - set(right_pages))
        candidate_pages.sort()
        remove_pages = candidate_pages[::factor]
        for p in remove_pages:
            candidate_pages.remove(p)
        new_pages = right_pages + candidate_pages
        #new_pages = list(set(left_pages) - set(remove_pages))
        new_coverage = LayoutGeneratorUtils.calculateTlbCoverage(self.pebs_df, new_pages)
        return new_pages, new_coverage

    def removePagesRecursively(self):
        right, left = self.state_log.getMaxGapLayouts()

        last_record = self.state_log.getLastRecord()
        last_inc_base = last_record['increment_base']
        last_inc_base_real = self.state_log.getRealCoverage(last_inc_base)
        last_base = last_record['scan_base']
        last_base_real = self.state_log.getRealCoverage(last_base)
        # check if last scan was done using this method and worked out
        if last_record['scan_direction'] != 'remove':
            left = self.state_log.getLeftLayoutName()
            factor = 2
        elif last_inc_base_real < last_record['real_coverage'] < last_base_real:
            factor = 2
        elif last_record['real_coverage'] <= last_inc_base_real:
            left = last_base
            right = last_inc_base
            factor = last_record['scan_factor'] * 2
        elif last_record['real_coverage'] >= last_base_real:
            left = last_record['layout']
            right = last_inc_base
            factor = 2

        left_pebs_coverage = self.state_log.getPebsCoverage(left)
        left_real_coverage = self.state_log.getRealCoverage(left)
        right_pebs_coverage = self.state_log.getPebsCoverage(right)
        right_real_coverage = self.state_log.getRealCoverage(right)

        base_layout = left
        inc_base = right

        new_pages, new_coverage = self.removePagesByFactor(inc_base, base_layout, factor)
        return base_layout, inc_base, factor, new_pages, new_coverage

    def addPagesByFactor(self, left, right, factor):
        factor = int(factor)
        assert factor >= 2

        left_pages = LayoutGeneratorUtils.getLayoutHugepages(left, self.exp_dir)
        right_pages = LayoutGeneratorUtils.getLayoutHugepages(right, self.exp_dir)

        candidate_pages = list(set(left_pages) - set(right_pages))
        candidate_pages.sort()
        remove_pages = candidate_pages[::factor]
        for p in remove_pages:
            candidate_pages.remove(p)
        new_pages = right_pages + candidate_pages
        new_coverage = LayoutGeneratorUtils.calculateTlbCoverage(self.pebs_df, new_pages)
        return new_pages, new_coverage

    def addPagesFromLeftLayout(self):
        last_layout = self.state_log.getLastLayoutName()
        last_layout_base = self.state_log.getBaseLayout(last_layout)
        right, left = self.state_log.getMaxGapLayouts()
        base_layout = right
        factor = 2
        if base_layout == last_layout_base:
            factor = self.state_log.getLayoutScanFactor(last_layout) + 1
            factor = max(factor, 2)
        pages, pebs_coverage = self.addPagesByFactor(left, base_layout, factor)
        return pages, pebs_coverage

    def addPagesV2(self, base_layout, working_set, desired_pebs_coverage, extra_pages=[]):
        if desired_pebs_coverage >= 100:
            return self.addPagesFromLeftLayout()

        if len(working_set) == 0:
            print('[DEBUG]: the working set (pages) is empty, skipping adding pages')
            return None, 0

        pages, pebs_coverage = self.addPagesFromWorkingSet(base_layout, working_set, desired_pebs_coverage, tail=True)
        #if pages is None or self.pagesSetExist(pages):
        #    pages, pebs_coverage = self.addPagesFromWorkingSet(base_layout, working_set, desired_pebs_coverage, tail=False)
        if pages is None:
            return None, 0
        if self.pagesSetExist(pages):
            if desired_pebs_coverage > pebs_coverage:
                desired_pebs_coverage += 0.5
            else:
                desired_pebs_coverage -= 0.5
            pages, pebs_coverage = self.addPagesFromWorkingSet(base_layout, working_set, desired_pebs_coverage, tail=True)
            if self.pagesSetExist(pages):
                return None, 0
        return pages, pebs_coverage

    def removePagesBasedOnRealCoverage(self, base_layout, desired_real_coverage):
        base_layout_real_coverage = self.state_log.getRealCoverage(base_layout)
        base_layout_pebs_coverage = self.state_log.getPebsCoverage(base_layout)
        base_layout_real_to_pebs_scale = base_layout_pebs_coverage / base_layout_real_coverage
        scaled_desired_coverage = base_layout_real_to_pebs_scale * desired_real_coverage

        print(f'[DEBUG]: desired real coverage: {desired_real_coverage}')
        print(f'[DEBUG]: scaled desired pebs coverage: {scaled_desired_coverage}')

        return self.removePagesV2(base_layout, None, scaled_desired_coverage)

    def removePagesV2(self, base_layout, working_set, desired_pebs_coverage):
        base_layout_pages = LayoutGeneratorUtils.getLayoutHugepages(base_layout, self.exp_dir)
        base_layout_coverage = self.state_log.getPebsCoverage(base_layout)
        if working_set is None:
            working_set = base_layout_pages
        df = self.pebs_df.query(f'PAGE_NUMBER in {working_set}')
        df = df.sort_values('TLB_COVERAGE', ascending=True)
        print(f'[DEBUG]: removePagesV2: {base_layout} has {len(base_layout_pages)} total pages, and {len(df)} pages in pebs as candidates to be removed')

        removed_pages = []
        total_weight = base_layout_coverage
        epsilon = 0.2
        max_coverage = desired_pebs_coverage
        min_coverage = desired_pebs_coverage - epsilon
        for index, row in df.iterrows():
            page = row['PAGE_NUMBER']
            weight = row['TLB_COVERAGE']
            updated_total_weight = total_weight - weight
            if updated_total_weight > min_coverage:
                removed_pages.append(page)
                total_weight = updated_total_weight
            if max_coverage >= total_weight >= min_coverage:
                break
        if len(removed_pages) == 0:
            return None, 0
        new_pages = list(set(base_layout_pages) - set(removed_pages))
        new_pages.sort()
        new_pebs_coverage = self.pebs_df.query(f'PAGE_NUMBER in {new_pages}')['TLB_COVERAGE'].sum()

        print(f'[DEBUG]: total removed pages from {base_layout}: {len(removed_pages)}')
        print(f'[DEBUG]: new layout coverage: {new_pebs_coverage}')

        return new_pages, new_pebs_coverage


    def tryToConcludeNextCoverage(self, base_layout, desired_real_coverage, scan_direction):
        base_layout_pages = LayoutGeneratorUtils.getLayoutHugepages(base_layout, self.exp_dir)
        selected_layouts = []
        # get all layouts that have the same scan direction (add/remove)
        query = self.state_log.df.query(f'scan_base != "other" and scan_direction == "{scan_direction}"')
        for l in query['layout']:
            pages = LayoutGeneratorUtils.getLayoutHugepages(l, self.exp_dir)
            # check if one pages set is included in the other
            common_pages = set(pages) & set(base_layout_pages)
            if common_pages == set(pages) or common_pages == set(base_layout_pages):
                selected_layouts.append(l)
        # add the right/left layouts if the current scan range
        if scan_direction == 'add':
            selected_layouts.append(self.state_log.getRightLayoutName())
        else:
            selected_layouts.append(self.state_log.getLeftLayoutName())

        # keep only the previous selected layouts
        query = self.state_log.df.query(f'layout in {selected_layouts} or scan_base == "{base_layout}"')

        # select all layouts that are in the right side if the desired coverage
        # and then select the one with the maximal pebs coverage
        right_layouts = query.query(f'real_coverage < {desired_real_coverage}').sort_values('pebs_coverage')
        if len(right_layouts) > 0:
            right = right_layouts.iloc[-1]
            right_pebs = right['pebs_coverage']
        else:
            right = None
            right_pebs = 0

        # select all layouts that are in the left side if the desired coverage
        # with a pebs coverage greater than the selected right layout
        # and then select from them the layout with the least pebs coverage
        left_layouts = query.query(f'real_coverage > {desired_real_coverage} and pebs_coverage > {right_pebs}').sort_values('pebs_coverage')
        if len(left_layouts) > 0:
            left = left_layouts.iloc[0]
        else:
            left = None

        right_layout = None if right is None else right['layout']
        left_layout = None if left is None else left['layout']
        print(f'[DEBUG]: tryToConcludeNextCoverage - the surrounding layouts:  {right_layout} < {desired_real_coverage} < {left_layout}')
        # initialize the desired_coverage to None so if we cannot predict the pebs coverage
        # then to fall back to the regular search method
        desired_coverage = None
        if right is not None and left is not None:
            right_pebs = right['pebs_coverage']
            right_real = right['real_coverage']
            left_pebs = left['pebs_coverage']
            left_real = left['real_coverage']

            right_pebs_real_scale = right_pebs / (right_real + 0.01) # add 0.01 to prevent zero div
            left_pebs_real_scale = left_pebs / left_real
            pebs_real_scale_avg = (right_pebs_real_scale / left_pebs_real_scale) / 2
            scaled_pebs_coverage = desired_real_coverage * pebs_real_scale_avg
            if left_pebs < scaled_pebs_coverage < right_pebs:
                desired_coverage = scaled_pebs_coverage
            else:
                pebs_avg = (right_pebs + left_pebs) / 2
                desired_coverage = pebs_avg
            '''
            # check if should prefer moving towards one of the two layouts
            if self.state_log.getLastLayoutName() == left_layout:
                desired_coverage = (pebs_avg + right_pebs) / 2
            elif self.state_log.getLastLayoutName() == right_layout:
                desired_coverage = (pebs_avg + left_pebs) / 2
            else:
                desired_coverage = pebs_avg
            '''
            print(f'[DEBUG]: predicting next pebs coverage based on {right_layout} and {left_layout} to: {desired_coverage}')
        elif right_layout is not None and right_layout != self.state_log.getLastLayoutName():
            desired_coverage = right['pebs_coverage'] + DEFAULT_FACTOR * INCREMENT
            # fix the desired coverage in case it exceeds the interval bounds
            mostleft_layout_pebs = self.state_log.getPebsCoverage(self.state_log.getLeftLayoutName())
            if scan_direction == 'remove' and desired_coverage > mostleft_layout_pebs:
                desired_coverage = (right['pebs_coverage'] + mostleft_layout_pebs) / 2
            print(f'[DEBUG]: predicting next pebs coverage based on right layout: {right_layout} to: {desired_coverage}')
        elif left_layout is not None and left_layout != self.state_log.getLastLayoutName():
            desired_coverage = left['pebs_coverage'] - DEFAULT_FACTOR * INCREMENT
            # fix the desired coverage in case it exceeds the interval bounds
            mostright_layout_pebs = self.state_log.getPebsCoverage(self.state_log.getRightLayoutName())
            if scan_direction == 'add' and desired_coverage < mostright_layout_pebs:
                desired_coverage = (left['pebs_coverage'] + mostright_layout_pebs) / 2
            print(f'[DEBUG]: predicting next pebs coverage based on left layout: {left_layout} to: {desired_coverage}')

        return desired_coverage

    def pagesSetExist(self, pages_to_find):
        for index, row in self.state_log.df.iterrows():
            pages = LayoutGeneratorUtils.getLayoutHugepages(row['layout'], self.exp_dir)
            if set(pages) == set(pages_to_find):
                return True
        return False

    def getScanParameters(self, increment_base, base_layout, expected_real_coverage):
        right_layout = self.state_log.getRightLayoutName()
        left_layout = self.state_log.getLeftLayoutName()
        left_pebs_coverage = self.state_log.getPebsCoverage(left_layout)

        last_record = self.state_log.getLastRecord()
        inc_base_real_coverage = self.state_log.getRealCoverage(increment_base)
        expected_real_coverage = inc_base_real_coverage + MAX_GAP
        base_real_coverage = self.state_log.getRealCoverage(base_layout)
        base_pebs_coverage = self.state_log.getPebsCoverage(base_layout)

        '''
        elif self.state_log.hasOnlyOneNewLayout() and increment_base == last_record['increment_base']:
            # if the first layout in the current interval did not succeed to
            # close the next gap, then try to remove the delta between pebs and
            # real coverage for the first layout hoping that it is a fixed delta
            real_pebs_diff = last_record['pebs_coverage'] - last_record['real_coverage']
            desired_pebs_coverage = expected_real_coverage + real_pebs_diff
            factor = (desired_pebs_coverage - base_pebs_coverage) / INCREMENT
            scan_direction = 'add'
        '''
        scan_direction = None
        if self.state_log.hasOnlyBaseLayouts():
            # aggressive start with the first layout in the current subgroup/interval
            factor = (2 * MAX_GAP) / INCREMENT
            desired_pebs_coverage =  inc_base_real_coverage - base_real_coverage + base_pebs_coverage + factor * INCREMENT
            scan_direction = 'add'
        else:
            factor = self.getNextFactor()
            scan_direction = last_record['scan_direction']
            if scan_direction == 'add':
                old_base_layout = base_layout

                base_layout = self.state_log.getBaseLayout(base_layout)
                if base_layout == 'none':
                    base_layout = right_layout
                # try to predict the desired pebs coverage based on previous runs
                predicted_coverage = self.tryToConcludeNextCoverage(base_layout, expected_real_coverage, scan_direction)
                if predicted_coverage is None:
                    print('[DEBUG]: could not predict next coverage...')
                    base_layout = old_base_layout
                    # if the base layout was changed then reset the factor
                    if base_layout != last_record['scan_base'] and self.state_log.getGapBetweenLastRecordAndIncrementBase() > 0.1:
                        #factor = DEFAULT_FACTOR TODO: check if this change makes the scan better
                        factor = MAX_GAP / INCREMENT
                    desired_pebs_coverage =  base_pebs_coverage + factor * INCREMENT + (inc_base_real_coverage - base_real_coverage)
                else:
                    desired_pebs_coverage = predicted_coverage
                    print(f'[DEBUG]: predicting next pebs coverage as {predicted_coverage} to get real coverage of {expected_real_coverage}')
                    base_layout_coverage = self.state_log.getPebsCoverage(base_layout)
                    factor = (desired_pebs_coverage - base_layout_coverage) / INCREMENT
            else:
                base_layout = left_layout
                predicted_coverage = self.tryToConcludeNextCoverage(base_layout, expected_real_coverage, scan_direction)
                if predicted_coverage is None:
                    print('[DEBUG]: could not predict next coverage...')
                    desired_pebs_coverage =  left_pebs_coverage - factor * INCREMENT
                else:
                    print(f'[DEBUG]: predicting next pebs coverage as {predicted_coverage} to get real coverage of {expected_real_coverage}')
                    desired_pebs_coverage = predicted_coverage
                    factor = (left_pebs_coverage - desired_pebs_coverage) / INCREMENT
        return scan_direction, factor, desired_pebs_coverage, base_layout

    def applyScanParameters(self, scan_direction, factor, desired_pebs_coverage, expected_real_coverage, base_layout):
        pages = None
        pebs_coverage = -1

        left_layout = self.state_log.getLeftLayoutName()
        left_pebs_coverage = self.state_log.getPebsCoverage(left_layout)
        out_union, only_in_left, not_in_right = self.getWorkingSetPages()
        if scan_direction == 'add':
            pages, pebs_coverage = self.addPagesV2(base_layout, out_union, desired_pebs_coverage)
            if pages is None:
                pages, pebs_coverage = self.addPagesV2(base_layout, not_in_right, desired_pebs_coverage)

        # if cannot find pages to add, try to remove pages from the left layout
        if scan_direction == 'add' and pages is None:
            print('[DEBUG]: could not add pages to get the desired coverage, moving to remove pages from the left layout')
            scan_direction = 'remove'
            base_layout = left_layout
            #factor = DEFAULT_FACTOR
            #desired_pebs_coverage =  left_pebs_coverage - factor * INCREMENT
            desired_pebs_coverage = left_pebs_coverage - (self.state_log.getRealCoverage(left_layout) - expected_real_coverage)
            factor = (left_pebs_coverage - desired_pebs_coverage) / INCREMENT

        if scan_direction == 'remove':
            if abs(left_pebs_coverage - 100) < 0.5:
                pages, pebs_coverage = self.removePagesV2(left_layout, None, desired_pebs_coverage)
            else:
                min_pebs_coverage = left_pebs_coverage - LayoutGeneratorUtils.calculateTlbCoverage(self.pebs_df, only_in_left)
                if desired_pebs_coverage < min_pebs_coverage:
                    desired_pebs_coverage = min_pebs_coverage
                    factor = (left_pebs_coverage - desired_pebs_coverage) / INCREMENT
                pages, pebs_coverage = self.removePagesV2(left_layout, only_in_left, desired_pebs_coverage)

        assert pages is not None
        return pages, pebs_coverage, scan_direction, factor, base_layout

    def createNextLayoutDynamically(self):
        assert self.results_df is not None,'results file does not exist'
        # fill or update SubgroupsLog and StateLog
        if not self.updateLogs():
            return
        print('==============================================')
        print(self.state_log.df)
        print('----------------------------------------------')

        right_layout = self.state_log.getRightLayoutName()

        increment_base, base_layout = self.state_log.getNextLayoutToIncrement(right_layout)
        expected_real_coverage = self.state_log.getRealCoverage(increment_base) + MAX_GAP
        assert increment_base is not None

        scan_direction, factor, desired_pebs_coverage, base_layout = \
            self.getScanParameters(increment_base, base_layout, expected_real_coverage)
        assert scan_direction is not None
        assert base_layout is not None
        assert factor is not None, 'factor should be defined'

        pages, pebs_coverage, scan_direction, factor, base_layout = \
                self.applyScanParameters(scan_direction, factor, desired_pebs_coverage, expected_real_coverage, base_layout)
        assert pages is not None, 'cannot find pages to remove'
        assert pebs_coverage is not None, 'pebs coverage should be calculated'

        self.state_log.addRecord(self.layout, scan_direction,
                                 factor, base_layout,
                                 pebs_coverage, expected_real_coverage,
                                 increment_base, pages)
        print('----------------------------------------------')
        print(self.state_log.df)
        print('==============================================')
        print(self.layout)
        print('#hugepages: '+ str(len(pages)))
        print('weight: ' + str(pebs_coverage))
        print('==============================================')
        # write the layout configuration file
        LayoutGeneratorUtils.writeLayout(self.layout, pages, self.exp_dir)
        # decrease current group's budget by 1
        self.subgroups_log.decreaseRemainingBudget(
            self.state_log.getLeftLayoutName())

class LayoutGeneratorUtils(metaclass=Singleton):
    HUGE_PAGE_2MB_SIZE = 2097152
    BASE_PAGE_4KB_SIZE = 4096

    brk_footprint = None
    mmap_footprint = None

    def __init__(self):
        pass

    def setPoolsFootprints(brk_footprint, mmap_footprint):
        LayoutGeneratorUtils.brk_footprint = brk_footprint
        LayoutGeneratorUtils.mmap_footprint = mmap_footprint

    def loadDataframe(results_file):
        if not os.path.isfile(results_file):
            return None
        results_ps = PerformanceStatistics(results_file)
        results_df = results_ps.getDataFrame()
        results_df['cpu-cycles'] = results_ps.getRuntime()
        results_df['walk_cycles'] = results_ps.getWalkDuration()
        results_df['stlb_hits'] = results_ps.getStlbHits()
        results_df['stlb_misses'] = results_ps.getStlbMisses()
        df = results_df[['layout', 'walk_cycles', 'stlb_hits', 'stlb_misses', 'cpu-cycles']]
        # drop duplicated rows
        important_columns = list(df.columns)
        important_columns.remove('layout')
        #df.drop_duplicates(inplace=True, subset=important_columns)
        df = df.drop_duplicates(subset=important_columns)
        return df

    def writeLayoutAll2mb(layout, output):
        assert LayoutGeneratorUtils.brk_footprint is not None
        assert LayoutGeneratorUtils.mmap_footprint is not None

        brk_pool_size = Utils.round_up(
            LayoutGeneratorUtils.brk_footprint,
            LayoutGeneratorUtils.HUGE_PAGE_2MB_SIZE)
        configuration = Configuration()
        configuration.setPoolsSize(
                brk_size=brk_pool_size,
                file_size=1*Utils.GB,
                mmap_size=LayoutGeneratorUtils.mmap_footprint)
        configuration.addWindow(
                type=configuration.TYPE_BRK,
                page_size=LayoutGeneratorUtils.HUGE_PAGE_2MB_SIZE,
                start_offset=0,
                end_offset=brk_pool_size)
        configuration.exportToCSV(output, layout)

    def writeLayout(layout, windows, output, sliding_index=0):
        page_size= LayoutGeneratorUtils.HUGE_PAGE_2MB_SIZE
        hugepages_start_offset = sliding_index * LayoutGeneratorUtils.BASE_PAGE_4KB_SIZE
        brk_pool_size = Utils.round_up(LayoutGeneratorUtils.brk_footprint, page_size) + hugepages_start_offset
        configuration = Configuration()
        configuration.setPoolsSize(
                brk_size=brk_pool_size,
                file_size=1*Utils.GB,
                mmap_size=LayoutGeneratorUtils.mmap_footprint)
        for w in windows:
            configuration.addWindow(
                    type=configuration.TYPE_BRK,
                    page_size=page_size,
                    start_offset=(w * page_size) + hugepages_start_offset,
                    end_offset=((w+1) * page_size) + hugepages_start_offset)
        configuration.exportToCSV(output, layout)

    def getLayoutHugepages(layout_name, exp_dir):
        page_size = LayoutGeneratorUtils.HUGE_PAGE_2MB_SIZE
        layout_file = str.format('{exp_root}/layouts/{layout_name}.csv',
                exp_root=exp_dir,
                layout_name=layout_name)
        df = pd.read_csv(layout_file)
        df = df[df['type'] == 'brk']
        df = df[df['pageSize'] == page_size]
        pages = []
        offset = 0
        for index, row in df.iterrows():
            start_page = int(row['startOffset'] / page_size)
            end_page = int(row['endOffset'] / page_size)
            offset = int(row['startOffset'] % page_size)
            pages += list(range(start_page, end_page))
        start_offset = offset / LayoutGeneratorUtils.BASE_PAGE_4KB_SIZE
        return pages

    def calculateTlbCoverage(pebs_df, pages):
        selected_pages = pebs_df.query(
                'PAGE_NUMBER in {pages}'.format(pages=pages))
        return selected_pages['TLB_COVERAGE'].sum()

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
