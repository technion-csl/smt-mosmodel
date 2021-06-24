#! /usr/bin/env python3

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log2_length', default=24, help='log2 of the array length')
parser.add_argument('-r', '--repeats', default=1, help='number of repeats')
args = parser.parse_args()

import numpy as np
array_length = 2**(args.log2_length)
array = np.arange(array_length)
# the array memory footprint is typically 2**(args.log2_length+3) because sizeof(int)==8

array_sum = 0
import random
for i in range(args.repeats * array_length):
    r = random.randrange(array_length)
    array_sum += array[r]

print(array_sum)

