MODULE_NAME := experiments/perf_mem
PERF_MEM_SUBMODULES := pebs_address_trace \
	pebs_tlb_miss_trace
SUBMODULES := $(PERF_MEM_SUBMODULES)
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

PERF_MEM_EXP_COMMON_MAKEFILE := $(ROOT_DIR)/$(MODULE_NAME)/common.mk

#TODO: just a temporary workaround to run benchmark for all configurations
CONFIGURATIONS := configuration1 configuration2 configuration3 configuration4
PER_BENCHMARK_TARGETS_PATTERN := $(foreach M,$(SUBMODULES),$(foreach C,$(CONFIGURATIONS),$(M)/$(C)/%))
PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
$(PER_BENCHMARK_TARGETS): $(MODULE_NAME)/%: $(PER_BENCHMARK_TARGETS_PATTERN)
	echo "Finished running all configurations of benchmark $*: $^"


include $(ROOT_DIR)/common.mk

