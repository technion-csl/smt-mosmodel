#! /usr/bin/env python3

import sys, os
sys.path.append(os.path.abspath('..'))
import my_models
import utility

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--page_walk_cycles', type=float, required=True)
parser.add_argument('-d', '--poly_degree', type=int, choices=[1,2,3], default=3)
parser.add_argument('-t', '--train_dataset', default='../train/mean.csv')
args = parser.parse_args()

import pandas as pd
#train_df = pd.read_csv(args.train_dataset)
train_df = utility.loadDataframe(args.train_dataset)

model = my_models.poly3
if args.poly_degree == 1:
    model = my_models.poly1
elif args.poly_degree == 2:
    model = my_models.poly2

runtime = my_models.predictRuntime(model, train_df, ['walk_cycles'], [[args.page_walk_cycles]])

print(str.format('Polynomial (degree=${degree}) model prediction:', degree=args.poly_degree))
print('------------------------')
print('page-walk-cycles = ',args.page_walk_cycles,' --> runtime = ',runtime)
