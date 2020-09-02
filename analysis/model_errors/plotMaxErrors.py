#! /usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--max_errors', required=True,
        help='the max errors file path to plot')
parser.add_argument('-t', '--plot_title', default="Undefined", type=str,
        help='the plot title: the machine architecture which used to gain the model errors')
parser.add_argument('-o', '--output_dir',  default='./')
args = parser.parse_args()

import pandas as pd
df = pd.read_csv(args.max_errors, index_col='benchmark')
# convert errors to absolute values
df = df.abs()*100

import sys
import os
sys.path.append(os.path.dirname(sys.argv[0])+"/..")
from shortenBenchmarkName import shortenBenchmarkName
benchmarks = df.index.map(shortenBenchmarkName)

def plotModels(df, benchmarks, models, output):
    ind = np.arange(len(benchmarks))  # the x locations for the groups
    num_models = len(models) # the df columns contain benchmark name and max-errors for all models
    width = 1 / (num_models + 1)  # the width of the bars

    fig, ax = plt.subplots(figsize=(16,9))
    pos = int(-num_models/2)

    bar_top = 10
    for model in models:
        ax.bar(ind + pos*width, df[model + '-max-error'], width, label=model)
        pos += 1
        err = df[model + '-max-error'].max()
        if err > bar_top:
            bar_top = err
    bar_top *= 0.1
    bar_step = bar_top / 5

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('max absolute errors [%]')
    ax.set_title('model max errors - ' + args.plot_title)
    ax.set_xticks(ind)
    ax.set_xlim(left=-0.5, right=len(benchmarks)+0.5)
    ax.set_xticklabels(benchmarks, rotation=-30, ha='left')
    ax.grid(axis='y')
    ax.legend(bbox_to_anchor=(.9, 1), loc='upper right')
    ax.set_yticks(np.arange(0, 176, 25))
    ax.set_ylim(0, 175)
    fig.tight_layout()
    #plt.show()
    plt.savefig(output)

plotModels(df, benchmarks, ['basu', 'pham', 'gandhi', 'yaniv'], args.output_dir + '/linear_models.pdf')
plotModels(df, benchmarks, ['poly1', 'poly2', 'poly3', 'mosmodel'], args.output_dir + '/polynomial_models.pdf')
