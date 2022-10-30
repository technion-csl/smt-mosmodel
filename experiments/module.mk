MODULE_NAME := experiments
SUBMODULES := \
	memory_footprint \
	single_page_size \
	pebs_tlb_miss_trace \
	moselect \
	growing_window_2m \
	random_window_2m \
	sliding_window
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

###### global constants

export EXPERIMENTS_ROOT := $(ROOT_DIR)/$(MODULE_NAME)
export EXPERIMENTS_TEMPLATE := $(EXPERIMENTS_ROOT)/template.mk
export OMP_NUM_THREADS := 1
export OMP_THREAD_LIMIT := 1
memory_node := 0
first_sibling := 2
second_sibling := 26
measure_timeout := 600
MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/src/libmosalloc.so

##### mosalloc paths
RUN_MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/runMosalloc.py
RESERVE_HUGE_PAGES := $(ROOT_DIR)/mosalloc/reserveHugePages.sh
MOSALLOC_MAKEFILE := $(ROOT_DIR)/mosalloc/CMakeLists.txt

##### scripts

COLLECT_RESULTS := $(SCRIPTS_ROOT_DIR)/collectResults.py
CHECK_PARANOID := $(SCRIPTS_ROOT_DIR)/checkParanoid.sh
SET_THP := $(SCRIPTS_ROOT_DIR)/setTransparentHugePages.sh
SET_CPU_MEMORY_AFFINITY := $(SCRIPTS_ROOT_DIR)/setCpuMemoryAffinity.sh
COLLECT_MEMORY_FOOTPRINT := $(SCRIPTS_ROOT_DIR)/collectMemoryFootprint.py
run_benchmark := /csl/benchmarks/ubuntu20/runBenchmark.py --num_threads=1 --exclude_files perf.out perf.time perf.data
measure_perf_events := $(SCRIPTS_ROOT_DIR)/measure_perf_events.py -r 2
bind_first_sibling := numactl -m $(memory_node) taskset -c $(first_sibling)
bind_second_sibling := numactl -m $(memory_node) taskset -c $(second_sibling)

define configuration_array
$(addprefix configuration,$(shell seq 1 $1))
endef

#### recipes and rules for prerequisites

.PHONY: experiments-prerequisites perf numactl mosalloc test-run-mosalloc-tool

mosalloc: $(MOSALLOC_TOOL)
$(MOSALLOC_TOOL): $(MOSALLOC_MAKEFILE)
	$(APT_INSTALL) cmake libgtest-dev
	cd $(dir $<)
	cmake .
	if [[ $$SKIP_MOSALLOC_TEST == 0 ]]; then \
		make -j && ctest -VV; \
	else \
		make -j; \
	fi

$(MOSALLOC_MAKEFILE):
	git submodule update --init --progress

experiments-prerequisites: perf numactl mosalloc

PERF_PACKAGES := linux-tools
KERNEL_VERSION := $(shell uname -r)
PERF_PACKAGES := $(addsuffix -$(KERNEL_VERSION),$(PERF_PACKAGES))
APT_INSTALL := sudo apt install -y
perf:
	$(CHECK_PARANOID)
	$(APT_INSTALL) "$(PERF_PACKAGES)"

numactl:
	$(APT_INSTALL) $@

TEST_RUN_MOSALLOC_TOOL := $(SCRIPTS_ROOT_DIR)/testRunMosallocTool.sh
test-run-mosalloc-tool: $(RUN_MOSALLOC_TOOL) $(MOSALLOC_TOOL)
	$(TEST_RUN_MOSALLOC_TOOL) $<

#### calculating the total number of instructions

INSTRUCTION_COUNT_FILE := $(MODULE_NAME)/instruction_count.csv

$(INSTRUCTION_COUNT_FILE): | experiments/memory_footprint/layout4kb
	$(SCRIPTS_ROOT_DIR)/countInstructions.py $| > $@

#### calculating the benchmark memory footprint

MEMORY_FOOTPRINT_FILE := $(MODULE_NAME)/memory_footprint.csv

$(MEMORY_FOOTPRINT_FILE): | experiments/memory_footprint/layout4kb
	$(COLLECT_MEMORY_FOOTPRINT) $| --output=$@

$(MODULE_NAME)/clean:
	rm -f $(MEMORY_FOOTPRINT_FILE)

### include common makefile

### define RESULT_DIRS to hold all created result directories
RESULT_DIRS :=

include $(ROOT_DIR)/common.mk

