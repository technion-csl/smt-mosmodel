#! /usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log2_length', default=25,
        help='log2 of the array size')
parser.add_argument('-r', '--repeats', default=1,
        help='log2 of the array size')
args = parser.parse_args()

import numpy as np
array_length = 2**args.log2_length
array = np.arange(array_length, dtype=int)

array_sum = 0
import random
for i in range(args.repeats * array_length):
    r = random.randrange(array_length)
    array_sum += array[r]

print(array_sum)

