MODULE_NAME := experiments/perf_mem/pebs_tlb_miss_trace/configuration4
SUBMODULES :=

include $(PERF_MEM_EXP_COMMON_MAKEFILE)

$(MODULE_NAME)%: MOSALLOC_POOLS_ARGS := -fps 1GB -bps 1GB -aps 10GB -ae1 10GB

