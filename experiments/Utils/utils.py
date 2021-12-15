import math

# TODO: go over all files that import Utils and modify them to use 
# the Utils class
kb = 1024
mb = 1024*kb
gb = 1024*mb

def round_up(x, base):
    return int(base * math.ceil(x/base))

def round_down(x, base):
    return (int(x / base) * base)

def isPowerOfTwo(number):
    return (number != 0) and ((number & (number - 1)) == 0)


class Utils:
    KB = 1024
    MB = 1024*kb
    GB = 1024*mb
    
    def round_up(x, base):
        return int(base * math.ceil(x/base))
    
    def round_down(x, base):
        return (int(x / base) * base)
    
    def isPowerOfTwo(number):
        return (number != 0) and ((number & (number - 1)) == 0)

    