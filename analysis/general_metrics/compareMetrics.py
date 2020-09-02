#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-b', '--benchmarks', required=True,
                    help='a comma-separated list of benchmarks')
parser.add_argument('-i1', '--input1', required=True, help='csv file #1')
parser.add_argument('-i2', '--input2', required=True, help='csv file #2')
parser.add_argument('-o', '--output', default='comparison.txt')
args = parser.parse_args()

try:
    benchmark_list = args.benchmarks.strip().split(',')
except KeyError:
    sys.exit('Error: could not parse the --benchmarks argument')

import pandas as pd
data_frame1 = pd.read_csv(args.input1, index_col=False)
data_frame2 = pd.read_csv(args.input2, index_col=False)
metrics = ['max-resident-memory-kb', 'seconds-elapsed']

comparison_data_frame = data_frame1[['benchmark']]
print(comparison_data_frame)
for metric in metrics:
    x1 = data_frame1[metric]
    x2 = data_frame2[metric]
    comparison_data_frame.loc[:, metric] = (x2 - x1) / x1
interesting_rows = ((data_frame1['max-resident-memory-kb'] > 10*1024) &
        (data_frame1['seconds-elapsed'] > 10))
comparison_data_frame = comparison_data_frame[interesting_rows]

def formatDataFrame(data_frame):
    formatter = {metric: '{:.0%}'.format for metric in metrics}
    html_string = data_frame.style.format(formatter).render()
    formatted_data_frame = pd.read_html(html_string, index_col=0)[0]
    return formatted_data_frame

formatted_data_frame = formatDataFrame(comparison_data_frame)
with open(args.output, 'w') as output_fid:
    print(formatted_data_frame.to_string(), file=output_fid)

