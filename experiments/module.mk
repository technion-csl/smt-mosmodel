MODULE_NAME := experiments
SUBMODULES := \
	without_mosalloc \
	single_page_size \
	pebs_tlb_miss_trace \
	growing_window_2m \
	random_window_2m \
	sliding_window
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

##### mosalloc paths
RUN_MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/runMosalloc.py
RESERVE_HUGE_PAGES := $(ROOT_DIR)/mosalloc/reserveHugePages.sh
MOSALLOC_MAKEFILE := $(ROOT_DIR)/mosalloc/CMakeLists.txt
export MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/src/libmosalloc.so

##### scripts

COLLECT_RESULTS_SCRIPT := $(SCRIPTS_ROOT_DIR)/collectResults.py
CHECK_PARANOID := $(SCRIPTS_ROOT_DIR)/checkParanoid.sh
SET_THP := $(SCRIPTS_ROOT_DIR)/setTransparentHugePages.sh
SET_CPU_MEMORY_AFFINITY := $(SCRIPTS_ROOT_DIR)/setCpuMemoryAffinity.sh
MEASURE_GENERAL_METRICS := $(SCRIPTS_ROOT_DIR)/measureGeneralMetrics.sh
RUN_BENCHMARK_SCRIPT := $(SCRIPTS_ROOT_DIR)/runBenchmark.py
COLLECT_MEMORY_FOOTPRINT_SCRIPT := $(SCRIPTS_ROOT_DIR)/collectMemoryFootprint.py

###### global constants

export EXPERIMENTS_ROOT := $(ROOT_DIR)/$(MODULE_NAME)
export EXPERIMENTS_TEMPLATE := $(EXPERIMENTS_ROOT)/template.mk
NUMBER_OF_SOCKETS := $(shell ls -d /sys/devices/system/node/node*/ | wc -w)
export BOUND_MEMORY_NODE := $$(( $(NUMBER_OF_SOCKETS) - 1 ))

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
	make -j && ctest -VV

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

#### recipes and rules for calculating the benchmark memory footprint

MEMORY_FOOTPRINT_FILE := $(MODULE_NAME)/memory_footprint.csv

$(MEMORY_FOOTPRINT_FILE): | experiments/single_page_size/layout4kb
	$(COLLECT_MEMORY_FOOTPRINT_SCRIPT) $| --output=$@

$(MODULE_NAME)/clean:
	rm -f $(MEMORY_FOOTPRINT_FILE)

### include common makefile

### define RESULT_DIRS to hold all created result directories
RESULT_DIRS :=

include $(ROOT_DIR)/common.mk

