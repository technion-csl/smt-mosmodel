#! /bin/bash

if (( $# < 1 )); then
    echo "Usage: $0 \"command_to_execute\""
    exit -1
fi

command="$@"

general_events="ref-cycles,cpu-cycles,instructions,"

# We no longer measure the cache events because we want to reduce sampling and improve the measuring accuracy.
general_events+="L1-dcache-loads,L1-dcache-stores,L1-dcache-load-misses,L1-dcache-store-misses"
general_events+=",LLC-loads,LLC-stores,LLC-load-misses,LLC-store-misses,"

#page_walker_events="page_walker_loads.dtlb_l1,page_walker_loads.dtlb_l2,page_walker_loads.dtlb_l3,page_walker_loads.dtlb_memory"
#page_walker_events+=",page_walker_loads.itlb_l1,page_walker_loads.itlb_l2,page_walker_loads.itlb_l3,page_walker_loads.itlb_memory,"
page_walker_events=`perf list | \grep -o "page_walker_loads\.[id]tlb\w*" | sort -u | tr '\n' ','`

itlb_events=`perf list | \grep -o "itlb.*misses\.\w*" | sort -u | tr '\n' ','`

prefix_perf_command="perf stat --field-separator=, --output=perf.out"
dtlb_events=`perf list | \grep -o "dtlb_.*_misses\.\w*" | sort -u | tr '\n' ','`
dtlb_events=${dtlb_events%?} # remove the trailing , charachter
#dtlb_events=dtlb_load_misses.miss_causes_a_walk,dtlb_load_misses.walk_duration,dtlb_store_misses.miss_causes_a_walk,dtlb_store_misses.walk_duration

perf_command="$prefix_perf_command --event $general_events$page_walker_events$itlb_events$dtlb_events -- "

time_format="seconds-elapsed,%e\nuser-time-seconds,%U\n"
time_format+="kernel-time-seconds,%S\nmax-resident-memory-kb,%M"
time_command="time --format=$time_format --output=time.out"

submit_command="$perf_command $time_command"
echo "Running the following command:"
echo "$submit_command $command"
$submit_command $command


