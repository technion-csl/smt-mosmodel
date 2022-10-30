#! /usr/bin/env python3

import pandas as pd
import my_models
import utility

l2_tlb_misses = 'l2_tlb_misses_completed'

def calculateYanivError(df, yaniv_A, yaniv_B, conf):
    y_pred = yaniv_A * df.loc[conf][l2_tlb_misses] + yaniv_B
    y_true = df.loc[conf]['cycles']
    return utility.relativeError(y_true, y_pred)

def print_coefficients(model, features, output_file):
    poly_features = ['1'] + model['poly'].get_feature_names(features)
    poly_coefficients = [model['linear'].intercept_] + list(model['linear'].coef_)
    poly_df = pd.DataFrame([poly_features, poly_coefficients])
    poly_df.to_csv(output_file, index=False, header=False)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-t', '--train_dataset', default='train_mean.csv')
parser.add_argument('-v', '--test_dataset', default='test_mean.csv')
parser.add_argument('-c', '--coeffs_file', default='linear_models_coeffs.csv')
parser.add_argument('-o', '--output', required=True)
parser.add_argument('-p', '--poly',  default='poly.csv',
        help='the coefficients of the polynomial models')
args = parser.parse_args()

train_df = utility.loadDataframe(args.train_dataset)
test_df = utility.loadDataframe(args.test_dataset)

coeffs = pd.read_csv(args.coeffs_file)

res_df = pd.DataFrame(index=test_df.index.values,
        columns=['yaniv_error', 'poly1_error', 'poly2_error', 'poly3_error', 'mosmodel_error'])
for i in test_df.index.values:
    yaniv_err = calculateYanivError(test_df, coeffs['yaniv_A'][0], coeffs['yaniv_B'][0], i)
    res_df.loc[i] = {
            'yaniv_error':yaniv_err,
            'poly1_error': -1,
            'poly2_error': -1,
            'poly3_error': -1,
            'mosmodel_error': -1}

poly1_err = my_models.calculateModelError(my_models.poly1, train_df, test_df, [l2_tlb_misses])
poly2_err = my_models.calculateModelError(my_models.poly2, train_df, test_df, [l2_tlb_misses])
poly3_err = my_models.calculateModelError(my_models.poly3, train_df, test_df, [l2_tlb_misses])
print_coefficients(my_models.poly3, [l2_tlb_misses], args.poly)
res_df['poly1_error'] = poly1_err
res_df['poly2_error'] = poly2_err
res_df['poly3_error'] = poly3_err

res_df.to_csv(args.output)

