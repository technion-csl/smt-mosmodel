#!/usr/bin/env python3

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from performance_statistics import PerformanceStatistics
glibc_ps = PerformanceStatistics('glibc_malloc/mean.csv')
x1 = glibc_ps.getWalkDuration()
y1 = glibc_ps.getRuntime()

interesting = pd.read_csv('glibc_malloc/walk_overhead.txt',
        delim_whitespace=True)['benchmark']

huge_page_configurations = ['libhugetlbfs_2mb']
slope_series = []
speedup_series = []
for configuration in huge_page_configurations:
    huge_ps = PerformanceStatistics(configuration+'/mean.csv')
    x2 = huge_ps.getWalkDuration()
    y2 = huge_ps.getRuntime()

    slope = (y2-y1)/(x2-x1)
    slope.name = configuration
    slope_series.append(slope[interesting.index])
    speedup = 1 - y2/y1
    speedup.name = configuration
    speedup_series.append(speedup[interesting.index])

slope_data_frame = pd.concat([interesting]+slope_series, axis=1)
with open('slope.txt', 'w') as output_fid:
    print(slope_data_frame, file=output_fid)

speedup_data_frame = pd.concat([interesting]+speedup_series, axis=1)
print(speedup_data_frame)

