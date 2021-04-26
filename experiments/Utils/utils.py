import math

kb = 1024
mb = 1024*kb
gb = 1024*mb

def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)

def isPowerOfTwo(number):
    return (number != 0) and ((number & (number - 1)) == 0)

    