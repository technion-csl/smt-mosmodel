#! /usr/bin/env python3

import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('experiments_root')
args = parser.parse_args()

perf_file = args.experiments_root + '/1/repeat0/perf.time'
df = pd.read_csv(perf_file)
print(df['instructions'].sum())

