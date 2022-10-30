#! /usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mean_file', default='mean.csv', nargs='+',
        help='the input CSV file containing mean values')
parser.add_argument('-o', '--output', help='the output file name')
parser.add_argument('-n', '--normalize', choices=[None, 'by-y', 'separate'],
        default=None, help='how to normalize the data columns')
args = parser.parse_args()

import pandas as pd

def readSingle(mean_file):
    df = pd.read_csv(mean_file, index_col='layout')
    df.fillna(0, inplace=True)
    df = df[['MPKI', 'CPI']]
    df.sort_values('MPKI', inplace=True)
    return df

output_dfs = []
for mean_file in args.mean_file:
    output_df = readSingle(mean_file)
    output_dfs.append(output_df)

output_df = pd.concat(output_dfs)

if args.normalize:
    max_metric = output_df['CPI'].max()
    max_x_metric = output_df['MPKI'].max()
    if args.normalize == 'by-y':
        output_df = output_df / max_metric
        # we normalized the entire DataFrame, including the std columns
    elif args.normalize == 'separate':
        output_df['CPI'] = output_df['CPI'] / max_metric
        output_df['MPKI'] = output_df['MPKI'] / max_x_metric

output_df.to_csv(args.output, float_format='%.3f')

