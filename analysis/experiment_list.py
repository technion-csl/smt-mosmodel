#! /usr/bin/env python3

import pandas as pd
from experiment import Experiment

class ExperimentList:
    def __init__(self, configurations, benchmarks, experiments_root):
        if (not configurations) or (not benchmarks):
            raise ValueError('one of configurations and benchmarks is empty')

        if len(configurations) > 1 and len(benchmarks) > 1:
            raise ValueError('both configurations and benchmarks are lists')

        if len(benchmarks) == 1:
            self._experiments = [
                    Experiment(configuration, benchmarks[0], experiments_root)
                    for configuration in configurations]
            self._index_label = 'configuration'
        else: # len(configurations) == 1
            self._experiments = [
                    Experiment(configurations[0], benchmark, experiments_root)
                    for benchmark in benchmarks]
            self._index_label = 'benchmark'

    def collect(self, repeat):
        dataframe_list = []
        for experiment in self._experiments:
            try:
                df = experiment.collect(repeat)
            except:
                raise ValueError('Could not collect the results of ' + \
                        str(experiment))
            if self._index_label == 'benchmark':
                df.index = [experiment._benchmark]
            elif self._index_label == 'configuration':
                df.index = [experiment._configuration]
            else:
                raise ValueError('invalid index_label ' + self._index_label)
            dataframe_list.append(df)
        df = pd.concat(dataframe_list, sort=False)
        df.index.name = self._index_label
        return df

