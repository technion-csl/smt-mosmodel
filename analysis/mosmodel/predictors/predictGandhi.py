#! /usr/bin/env python3

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/..')
import my_models
import utility

def predictGandhiRuntime(A, B, tlb_misses):
    '''
    runtime = B + A*stlb_misses
    Where:
    B = runtime[2mb] - walk_cycles[2mb]
    A = walk_cycles / stlb_misses
    '''
    y_pred = B + A*tlb_misses
    return y_pred

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--tlb_misses', type=float, required=True)
parser.add_argument('-f', '--coeffs_file', default='../../linear_models_coeffs/coeffs.csv')
args = parser.parse_args()

import pandas as pd
coeffs = pd.read_csv(args.coeffs_file)
gandhi_runtime = predictGandhiRuntime(coeffs['gandhi_A'][0], coeffs['gandhi_B'][0], args.tlb_misses)

print('Gandhi model prediction:')
print('------------------------')
print('tlb-misses = ',args.tlb_misses,' --> runtime = ',gandhi_runtime)
