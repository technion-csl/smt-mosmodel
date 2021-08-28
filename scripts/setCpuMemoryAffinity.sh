#! /bin/bash

if (( $# < 2 )); then
    echo "Usage: $0 \"node_number\" \"command_to_execute\""
    exit -1
fi

node_number="$1"
shift
command="$@"

bound_cpu_core=$(cat /sys/devices/system/node/node${node_number}/cpulist | rev | cut -d ',' -f 1 | cut -d '-' -f 1 | rev)
echo "Binding the process to memory node: $node_number,"
echo "and its local CPU core: $bound_cpu_core"
taskset_command="taskset --cpu-list $bound_cpu_core"
numactl_command="numactl --membind $node_number"
submit_command="$taskset_command $numactl_command"

isolated_cpus_list=$(cat /sys/devices/system/cpu/isolated)
isolated_cpus=$(echo {1..100} | { cut -d" " -f"${isolated_cpus_list// /,}"; })
if `echo ${isolated_cpus} | grep -w -q ${bound_cpu_core}`; then
    echo "cpu $bound_cpu_core is isolated"
    echo "Move the following cores to online-->offline: $bound_cpu_core"
    sudo bash -c "echo 0 > /sys/devices/system/cpu/cpu${bound_cpu_core}/online"
    sleep 1
    sudo bash -c "echo 1 > /sys/devices/system/cpu/cpu${bound_cpu_core}/online"
    sleep 1
else
    echo "$isolated_cpus_list does not contain cpu number: $bound_cpu_core"
    echo "skipping moving the bounded core to offline->online..."
fi

$submit_command $command

