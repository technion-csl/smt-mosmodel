#! /usr/bin/env python3

import sys
import pandas as pd
from experiment_list import ExperimentList

def writeDataframeToCsv(df, file_name):
    df.to_csv(file_name, na_rep='NaN')

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--experiments_root', default='experiments/',
                    help='the directory containing results in a tree '+\
                    'structure of configuration/benchmark/repeat')
parser.add_argument('-b', '--benchmarks', required=True,
                    help='a comma-separated list of benchmarks')
parser.add_argument('-c', '--configurations', required=True,
                    help='a comma-separated list of configurations')
parser.add_argument('-r', '--repeats', default=1, type=int,
                    help='repeats number of each benchmark')
parser.add_argument('-o', '--output_dir', required=True,
                    help='the directory for all output files')
args = parser.parse_args()

try:
    benchmark_list = args.benchmarks.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --benchmarks argument')

try:
    configuration_list = args.configurations.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --configurations argument')

# build the output directory
import os
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
output_dir = args.output_dir + '/'

# collect the results, one dataframe for each repetition
dataframe_list = []
for repeat in range(args.repeats):
    experiment_list = ExperimentList(configuration_list, benchmark_list,
                                     args.experiments_root)
    df = experiment_list.collect(repeat)
    csv_file_name = 'repeat' + str(repeat) + '.csv'
    writeDataframeToCsv(df, output_dir + csv_file_name)
    dataframe_list.append(df)

df = pd.concat(dataframe_list)
mean_df = df.groupby(df.index).mean()
std_df = df.groupby(df.index).std()

# detect outliers
index_column = mean_df.index
interesting_metrics = ['seconds-elapsed', 'ref-cycles', 'cpu-cycles']
interesting_metrics = [metric for metric in interesting_metrics if metric in mean_df.columns]
variation = std_df[interesting_metrics] / mean_df[interesting_metrics]
outlier_threshold = 0.05
outliers = variation > outlier_threshold
if outliers.any().any():
    print("Error: the results in", args.experiments_root, "showed considerable variation:")
    print(outliers)
    sys.exit('Cells marked with True are the outliers.')

# if there are no outliers, write the aggregated results
writeDataframeToCsv(df, output_dir + 'all_repeats.csv')
writeDataframeToCsv(mean_df, output_dir + 'mean.csv')
writeDataframeToCsv(std_df, output_dir + 'std.csv')

