#!/usr/bin/env python3
import os
import pandas as pd
from ast import literal_eval
import os.path

MAX_GAP = 4
MAX_TRIALS = 50

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class Log():

    def __init__(self,
                 exp_dir, results_df, log_name,
                 default_columns, converters=None):
        self.exp_dir = exp_dir
        self.results_df = results_df
        self.log_file = self.exp_dir + '/' + log_name
        self.default_columns = default_columns
        self.df = self.readLog(converters)

    def readLog(self, converters=None):
        if not os.path.isfile(self.log_file):
            self.df = pd.DataFrame(columns=self.default_columns)
        else:
            self.df = pd.read_csv(self.log_file, converters=converters)
        return self.df

    def writeLog(self):
        self.df.to_csv(self.log_file, index=False)

    def clear(self):
        self.df = pd.DataFrame(columns=self.default_columns)

    def empty(self):
        return self.df.empty

    def getField(self, layout_name, field_name):
        field_val = self.df.loc[self.df['layout'] == layout_name, field_name]
        field_val = field_val.to_list()
        if field_val == []:
            return None
        else:
            return field_val[0]

    def getRealCoverage(self, layout):
        return self.getField(layout, 'real_coverage')

    def getExpectedRealCoverage(self, layout):
        return self.getField(layout, 'expected_real_coverage')

    def getPebsCoverage(self, layout):
        return self.getField(layout, 'pebs_coverage')

    def getLastRecord(self):
        if self.empty():
            return None
        return self.df.iloc[len(self.df)-1]

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
        record = self.df.query('{key} == "{value}"'.format(
            key=key_name,
            value=key_value))
        if record.empty:
            return None
        else:
            return record.iloc[0]

    def writeRealCoverage(self):
        max_walk_cycles = self.results_df['walk_cycles'].max()
        min_walk_cycles = self.results_df['walk_cycles'].min()
        delta_walk_cycles = max_walk_cycles - min_walk_cycles
        self.df['real_coverage'] = self.df['real_coverage'].astype(float)
        query = self.df.query('real_coverage == (-1)')
        for index, row in query.iterrows():
            layout = row['layout']
            walk_cycles = self.results_df.loc[self.results_df['layout'] == layout, 'walk_cycles'].iloc[0]
            real_coverage = (max_walk_cycles - walk_cycles) / delta_walk_cycles
            real_coverage *= 100
            self.df.loc[self.df['layout'] == layout, 'real_coverage'] = real_coverage
            self.df.loc[self.df['layout'] == layout, 'walk_cycles'] = walk_cycles
        self.writeLog()


class SubgroupsLog(Log, metaclass=Singleton):
    def __init__(self, exp_dir, results_df):
        default_columns = [
            'layout', 'total_budget', 'remaining_budget',
            'pebs_coverage', 'real_coverage', 'walk_cycles']
        super().__init__(exp_dir, results_df, 'subgroups.log', default_columns)

    def addRecord(self,
                  layout, pebs_coverage, writeLog=False):
        self.df = self.df.append({
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
        query = self.df.query('real_coverage == (-1)')
        assert len(query) == 0, 'SubgroupsLog.calculateBudget was called before updating the subgroups real_coverage.'
        query = self.df.query('total_budget < 0')
        if len(query) == 0:
            return
        # sort the group layouts by walk-cycles/real_coverage
        self.df = self.df.sort_values('real_coverage', ascending=True)
        # calculate the diff between each two adjacent layouts
        # (call it delta[i] for the diff between group[i] and group[i+1])
        self.df['delta'] = self.df['real_coverage'].diff().abs()
        self.df['delta'] = self.df['delta'].fillna(0)
        total_deltas = self.df.query(f'delta > {MAX_GAP}')['delta'].sum()
        # budgest = 50-9: num_layouts(50) - subgroups_layouts(9)
        total_budgets = MAX_TRIALS - 9
        for index, row in self.df.iterrows():
            delta = row['delta']
            # for each delta < MAX_GAP assign budget=0
            if delta <= MAX_GAP:
                budget = 0
            else:
                budget = round((delta / total_deltas) * total_budgets)
                # we have 41 layouts in total to create dynamically (each can get 2.5 in the best case)
                budget = max(budget, int(delta / 2.5))
            self.df.at[index, 'total_budget'] = budget
            self.df.at[index, 'remaining_budget'] = budget
        # fix total budgets due to rounding
        rounded_total_budgets = self.df['total_budget'].sum()
        delta_budget = total_budgets - rounded_total_budgets
        self.df.at[index, 'total_budget'] = budget + delta_budget
        self.df.at[index, 'remaining_budget'] = budget + delta_budget

        self.writeLog()

    def decreaseRemainingBudget(self, layout):
        self.df.loc[self.df['layout'] == layout, 'remaining_budget'] = self.df.loc[self.df['layout'] == layout, 'remaining_budget']-1
        self.writeLog()

    def zeroBudget(self, layout):
        total = self.getField(layout, 'total_budget')
        remaining = self.getField(layout, 'remaining_budget')
        self.df.loc[self.df['layout'] == layout, 'total_budget'] = total - remaining
        self.df.loc[self.df['layout'] == layout, 'remaining_budget'] = 0
        self.writeLog()

    def addExtraBudget(self, layout, extra_budget):
        self.df.loc[self.df['layout'] == layout, 'remaining_budget'] = self.df.loc[self.df['layout'] == layout, 'remaining_budget']+extra_budget
        self.df.loc[self.df['layout'] == layout, 'total_budget'] = self.df.loc[self.df['layout'] == layout, 'total_budget']+extra_budget
        self.writeLog()

    def getRightmostLayout(self):
        self.writeRealCoverage()
        df = self.df.sort_values('walk_cycles', ascending=False)
        return df.iloc[0]

    def getLeftmostLayout(self):
        self.writeRealCoverage()
        df = self.df.sort_values('walk_cycles', ascending=True)
        return df.iloc[0]

    def getTotalRemainingBudget(self):
        return self.df['remaining_budget'].sum()

    def getTotalBudget(self):
        return self.df['total_budget'].sum()


class StateLog(Log):
    def __init__(self, exp_dir, results_df, right_layout, left_layout):
        default_columns = [
            'layout', 'scan_base', 'increment_base',
            'scan_direction', 'scan_order', 'scan_factor',
            'pebs_coverage', 'increment_real_coverage',
            'expected_real_coverage', 'real_coverage',
            'walk_cycles']
        self.right_layout = right_layout
        self.left_layout = left_layout
        state_name = right_layout + '_' + left_layout
        super().__init__(exp_dir, results_df,
                         state_name + '_state.log', default_columns)
        super().writeRealCoverage()
        self.pages_log_name = self.exp_dir + '/layout_pages.log'
        if not os.path.isfile(self.pages_log_name):
            self.pages_df = pd.DataFrame(columns=[
                'layout', 'base_layout',
                'added_pages', 'pages'])
        else:
            self.pages_df = pd.read_csv(self.pages_log_name, converters={
                "pages": literal_eval, "added_pages": literal_eval})

    def addRecord(self,
                  layout,
                  scan_direction,
                  scan_order,
                  scan_factor, scan_base,
                  pebs_coverage, expected_real_coverage, increment_base,
                  pages,
                  writeLog=True):
        base_pages = []
        if scan_base != 'none' and scan_base != 'other':
            base_pages = self.getLayoutPages(scan_base)
        added_pages = list(set(pages) - set(base_pages))
        added_pages.sort()
        self.df = self.df.append({
            'layout': layout,
            'scan_direction': scan_direction,
            'scan_order': scan_order,
            'scan_factor': scan_factor,
            'scan_base': scan_base,
            'pebs_coverage': pebs_coverage,
            'expected_real_coverage': expected_real_coverage,
            'increment_base': increment_base,
            'increment_real_coverage': self.getRealCoverage(increment_base),
            'real_coverage': -1,
            'walk_cycles': -1
            }, ignore_index=True)
        if writeLog:
            self.writeLog()
        if layout not in self.pages_df['layout']:
            self.pages_df = self.pages_df.append({
                'layout': layout,
                'base_layout': scan_base,
                'added_pages': added_pages,
                'pages': pages
                }, ignore_index=True)
            self.pages_df.to_csv(self.pages_log_name, index=False)

    def getLayoutPages(self, layout):
        pages = self.pages_df.loc[self.pages_df['layout'] == layout, 'pages'].iloc[0]
        return pages

    def getLayoutAddedPages(self, layout):
        return self.getField(layout, 'added_pages')

    def hasOnlyBaseLayouts(self):
        df = self.df.query(f'scan_base != "none" and scan_base != "other"')
        return len(df) == 0

    def hasOnlyOneNewLayout(self):
        df = self.df.query(f'scan_base != "none" and scan_base != "other"')
        return len(df) == 1

    def getRightLayoutName(self):
        return self.right_layout

    def getLeftLayoutName(self):
        return self.left_layout

    def getRigthRecord(self):
        assert(not self.empty())
        return self.getRecord('layout', self.getRightLayoutName())

    def getLeftRecord(self):
        assert(not self.empty())
        return self.getRecord('layout', self.getLeftLayoutName())

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

    def getGapBetweenLastRecordAndIncrementBase(self):
        #self.writeRealCoverage()
        last_layout = self.getLastRecord()
        base_layout = last_layout['increment_base']
        return self.getGapFromBase(last_layout['layout'], base_layout)

    def getBaseLayout(self, layout_name):
        return self.getField(layout_name, 'scan_base')

    def getIncBaseLayout(self, layout_name):
        return self.getField(layout_name, 'increment_base')

    def getLayoutScanFactor(self, layout_name):
        return self.getField(layout_name, 'scan_factor')

    def getNextLayoutToIncrement(self, start_layout):
        start_layout_coverage = self.getRealCoverage(start_layout)
        max_coverage = self.getRealCoverage(self.getLeftLayoutName())
        df = self.df.query(f'real_coverage >= {start_layout_coverage}')
        df = df.sort_values('real_coverage', ascending=True)
        base_layout = start_layout
        current_coverage = start_layout_coverage
        current_layout = start_layout
        print(start_layout)
        for index, row in df.iterrows():
            if row['real_coverage'] <= (current_coverage + MAX_GAP):
                current_layout = row['layout']
                if row['scan_base'] != 'other':
                    base_layout = current_layout
                current_coverage = row['real_coverage']
                if current_coverage >= max_coverage:
                    return None, None
            else:
                break
        return current_layout, base_layout

    def getMaxGapLayouts(self):
        left_coverage = self.getRealCoverage(self.getLeftLayoutName())
        right_coverage = self.getRealCoverage(self.getRightLayoutName())
        query = self.df.query(f'{right_coverage} <= real_coverage <= {left_coverage}')
        diffs = query.sort_values('real_coverage', ascending=True)
        diffs['diff'] = diffs['real_coverage'].diff().abs()

        idx_label = diffs['diff'].idxmax()
        idx = diffs.index.get_loc(idx_label)
        right = diffs.iloc[idx-1]
        left = diffs.iloc[idx]
        return right['layout'], left['layout']

    def isLastLayoutIrregular(self, layout):
        assert len(self.df) > 2
        last_record = self.df.iloc[len(self.df)-1]
        last_layout_base = self.getBaseLayout(last_record['layout'])
        prev_last_record = self.df.iloc[len(self.df)-2]
        if last_record['scan_base'] == prev_last_record['scan_base'] and last_record['scan_direction'] == 'add':
            if last_record['pebs_coverage'] > prev_last_record['pebs_coverage'] and last_record['real_coverage'] < prev_last_record['real_coverage']:
                new_pebs_coverage = last_record['pebs_coverage'] + last_record['scan_factor'] * MAX_GAP
                return new_pebs_coverage
            if last_record['pebs_coverage'] < prev_last_record['pebs_coverage'] and last_record['real_coverage'] > prev_last_record['real_coverage']:
                new_pebs_coverage = (last_record['pebs_coverage'] + self.getPebsCoverage(last_layout_base)) / 2
                return new_pebs_coverage
        return None
