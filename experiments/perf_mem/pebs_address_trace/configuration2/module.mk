MODULE_NAME := experiments/perf_mem/pebs_address_trace/configuration2
SUBMODULES :=

include $(PERF_MEM_EXP_COMMON_MAKEFILE)

$(MODULE_NAME)%: MOSALLOC_POOLS_ARGS := -fps 1GB -bps 1GB -aps 10GB -ae2=2MB

