#! /usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log2_length', default=27, help='log2 of the array size') # 128 MB
parser.add_argument('-r', '--repeats', default=1, help='number of repeats')
args = parser.parse_args()

import numpy as np
array_length = 2**(args.log2_length - 3) # subtract 3 because log2(sizeof(int))==3
array = np.arange(array_length, dtype=int)

array_sum = 0
import random
for i in range(args.repeats * array_length):
    r = random.randrange(array_length)
    array_sum += array[r]

print(array_sum)

