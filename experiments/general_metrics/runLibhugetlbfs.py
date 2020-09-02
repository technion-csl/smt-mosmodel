#! /usr/bin/env python3

import sys
import os

import argparse
parser = argparse.ArgumentParser(description='A tool to run applications under\
         libhugetlbfs library (by preloading it)')
parser.add_argument('-d', '--debug', action='store_true',
        help="run in debug mode to disable set-thp and reserve-huge-pages")
parser.add_argument('-l', '--library',
        default='software/libhugetlbfs/untarred/obj64/libhugetlbfs.so',
        help="libhugetlbfs library path to preload.")
parser.add_argument('-r', '--reserve_hugepages',
        default='experiments/reserveHugePages.sh',
        help="path to reserveHugePages.sh scripts")
parser.add_argument('-s', '--set_thp',
        default='experiments/setTransparentHugePages.sh',
        help="path to setTransparentHugePages.sh scripts")
parser.add_argument('-lp', '--large_pages', default=0,
        help="number of large (2MB) pages to reserve")
parser.add_argument('-hp', '--huge_pages', default=0,
        help="number of huge (1GB) pages to reserve")
parser.add_argument('-m', '--morecore', choices=['thp', '1gb', '2mb'],
        default='never', help="specify the libhugetlbfs morecore method")
parser.add_argument('dispatch_program', help="program to execute")
parser.add_argument('dispatch_args', nargs=argparse.REMAINDER,
        help="program arguments")
args = parser.parse_args()

# validate the command-line arguments
if not os.path.isfile(args.library):
    sys.exit("Error: the libhugetlbfs library cannot be found")

# build the environment variables
environ = {}
environ["HUGETLB_NO_RESERVE"] = 'yes'
environ["HUGETLB_MORECORE"] = args.morecore
environ["LD_PRELOAD"] = args.library
environ.update(os.environ)

large_pages= args.large_pages
huge_pages = args.huge_pages

# dispatch the program with the environment we just set
import subprocess
try:
    if not args.debug:
        thp_value = 'madvise' if args.morecore == 'thp' else 'never'
        # set THP and reserve hugepages before start running the workload
        subprocess.check_call([args.set_thp, thp_value])
        subprocess.check_call([args.reserve_hugepages, '-l'+str(large_pages), '-h'+str(huge_pages)])

    command_line = [args.dispatch_program] + args.dispatch_args
    p = subprocess.Popen(command_line, env=environ, shell=False)
    p.wait()
    sys.exit(p.returncode)
except Exception as e:
    sys.exit("Caught an exception: " + str(e))

print("Execution completed....")

