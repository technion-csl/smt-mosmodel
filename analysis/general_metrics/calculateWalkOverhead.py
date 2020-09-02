#!/usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', default='data.csv')
parser.add_argument('-o', '--output', default='output.csv')
args = parser.parse_args()

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from performance_statistics import PerformanceStatistics

ps = PerformanceStatistics(args.input)
data_frame = ps.getDataFrame()

data_frame['walk_cycles'] = ps.getWalkDuration()
data_frame['walk_overhead'] = data_frame['walk_cycles'] / ps.getRuntime()
data_frame['runtime_minutes'] = data_frame['seconds-elapsed'] / 60.0
data_frame['max_memory_GB'] = data_frame['max-resident-memory-kb'] / 1024.0 / 1024.0
interesting_columns = ['benchmark', 'runtime_minutes', 'walk_overhead', 'max_memory_GB']
walk_overhead_threshold = 0.1
interesting_rows = (data_frame['walk_overhead'] > walk_overhead_threshold)
interesting_data_frame = data_frame.loc[interesting_rows, interesting_columns]

def formatDataFrame(data_frame):
    formatter = {'walk_overhead': '{:.0%}'.format,
                 'runtime_minutes': '{:.0f}'.format,
                 'max_memory_GB': '{:.1f}'.format}
    html_string = data_frame.style.format(formatter).render()
    formatted_data_frame = pd.read_html(html_string, index_col=0)[0]
    return formatted_data_frame

formatted_data_frame = formatDataFrame(interesting_data_frame)
with open(args.output, 'w') as output_fid:
    print(formatted_data_frame.to_string(), file=output_fid)
