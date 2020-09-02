#!/usr/bin/env python3

input_files = {}
input_files['4kb'] = 'glibc_malloc/mean.csv'
input_files['2mb'] = 'libhugetlbfs_2mb/mean.csv'
input_files['1gb'] = 'libhugetlbfs_1gb/mean.csv'

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from performance_statistics import PerformanceStatistics

data_frames = {}
columns = {}
for page_size, input_file in input_files.items():
    data_frame = pd.read_csv(input_file, index_col=False)
    ps = PerformanceStatistics(input_file)
    benchmarks = data_frame['benchmark']
    columns[page_size] = 1000.0 / data_frame['instructions'] * \
            ps.getStlbMisses()

columns['benchmark'] = benchmarks
data_frame = pd.DataFrame(columns)
reordered_columns = ['benchmark', '4kb', '2mb', '1gb']
data_frame = data_frame[reordered_columns]

def formatDataFrame(data_frame):
    formatter = {'4kb': '{:.1f}'.format,
                 '2mb': '{:.1f}'.format,
                 '1gb': '{:.1f}'.format}
    html_string = data_frame.style.format(formatter).render()
    formatted_data_frame = pd.read_html(html_string, index_col=0)[0]
    return formatted_data_frame

formatted_data_frame = formatDataFrame(data_frame)
with open('tlb_misses.txt', 'w') as output_fid:
    print(formatted_data_frame.to_string(), file=output_fid)

