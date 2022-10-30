#! /usr/bin/env python3

def maxError(error_column):
    max_err = error_column.max()
    min_err = error_column.min()
    abs_max_err = max_err
    if abs(min_err) > abs(max_err):
        abs_max_err = min_err
    #max_err_str = '{:.1%}'.format(abs_max_err)
    #return max_err_str
    return abs_max_err

def relativeError(y_true, y_pred):
    return (y_pred-y_true)/y_true

import pandas as pd
def loadDataframe(mean_file):
    df = pd.read_csv(mean_file, index_col='layout')
    df.fillna(0, inplace=True)
    df = df.drop_duplicates()
    df = df.sort_values('MPKI')

    return df

