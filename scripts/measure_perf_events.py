#! /usr/bin/env python3

import argparse
import subprocess
import pandas as pd
import sys

def searchEventInList(event: str, event_list: list) -> str:
    # search for strings that contain "event"
    events = [x for x in event_list if event in x]
    if len(events) == 0:
        raise KeyError(f'{event} is not a valid perf event')
    elif len(events) == 1:
        return events[0]
    else: # there are multiple candidates, search for an exact match
        exact_match = [x for x in events if x==event]
        return exact_match[0]

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=str, default='perf.time', help='a CSV file containing the measured perf events over time')
parser.add_argument('subcommand', nargs=argparse.REMAINDER, help='the script will run this subcommand and collect its perf counters')
args = parser.parse_args()

# Find the perf hardware events available on this machine
perf_events_string = subprocess.check_output('perf list', shell=True, text=True)
perf_events = perf_events_string.split(' ')
all_loads = searchEventInList('retired.all_loads', perf_events)
all_stores = searchEventInList('retired.all_stores', perf_events)

# L2 TLB hits
l2_tlb_load_hits_speculative = searchEventInList('dtlb_load_misses.stlb_hit', perf_events)
l2_tlb_store_hits_speculative = searchEventInList('dtlb_store_misses.stlb_hit', perf_events)

# L2 TLB misses
l2_tlb_load_misses_retired = searchEventInList('retired.stlb_miss_loads', perf_events)
l2_tlb_store_misses_retired = searchEventInList('retired.stlb_miss_stores', perf_events)

l2_tlb_load_misses_completed = searchEventInList('dtlb_load_misses.walk_completed', perf_events)
l2_tlb_store_misses_completed = searchEventInList('dtlb_store_misses.walk_completed', perf_events)

mispredicted_branch_instructions = 'br_misp_retired.all_branches'
branch_instructions = 'br_inst_retired.all_branches'


# Define the list of hardware events to monitor
events = ['cycles', 'instructions', all_loads, all_stores,
        l2_tlb_load_misses_retired, l2_tlb_store_misses_retired,
        l2_tlb_load_misses_completed, l2_tlb_store_misses_completed]

event_names = {all_loads: 'all_loads',
        all_stores: 'all_stores',
        l2_tlb_load_misses_retired: 'l2_tlb_load_misses_retired',
        l2_tlb_store_misses_retired: 'l2_tlb_store_misses_retired',
        l2_tlb_load_misses_completed: 'l2_tlb_load_misses_completed',
        l2_tlb_store_misses_completed: 'l2_tlb_store_misses_completed',
        }

# Run the process and collect the measurements in perf.out
perf_tmp_file = 'perf.out'
user_space_events = [e + ':u' for e in events]
events_string = ','.join(user_space_events)
subcommand = " ".join(args.subcommand)
perf_command = f'perf stat --interval-print=1000 --field-separator=, --output={perf_tmp_file} --event={events_string} {subcommand}'
completed_process = subprocess.run(perf_command, shell=True) 

# Organize perf_tmp_file in a dataframe
df = pd.read_csv(perf_tmp_file, skiprows=(0, 1), usecols=[0, 1, 3],
        names=['time', 'counter_value', 'counter_name'], na_values='<not counted>')
df = df.pivot(index='time', columns='counter_name', values='counter_value')
df.columns = [col.replace(':u', '') for col in df.columns]
df.rename(columns=event_names, inplace=True)  

# Calculate a few more statistics from the existing events
df['l1_tlb_accesses'] = df['all_loads'] + df['all_stores']

df['l2_tlb_misses_retired'] = df['l2_tlb_load_misses_retired'] + df['l2_tlb_store_misses_retired']
df['l2_tlb_misses_completed'] = df['l2_tlb_load_misses_completed'] + df['l2_tlb_store_misses_completed']

# Print the dataframe to the output file
df.to_csv(args.output, index=True, float_format='%#10.4g')

sys.exit(completed_process.returncode)

