MODULE_NAME := experiments
SUBMODULES := \
	memory_footprint \
	single_page_size \
	growing_window_2m \
	random_window_2m
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

##### mosalloc paths
RUN_MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/runMosalloc.py
RESERVE_HUGE_PAGES := $(ROOT_DIR)/mosalloc/reserveHugePages.sh
export MOSALLOC_TOOL := $(ROOT_DIR)/mosalloc/src/libmosalloc.so


##### scripts

COLLECT_RESULTS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/collectResults.py
CHECK_PARANOID := $(ROOT_DIR)/$(MODULE_NAME)/checkParanoid.sh
SET_THP := $(ROOT_DIR)/$(MODULE_NAME)/setTransparentHugePages.sh
SET_CPU_MEMORY_AFFINITY := $(ROOT_DIR)/$(MODULE_NAME)/setCpuMemoryAffinity.sh
MEASURE_GENERAL_METRICS := $(ROOT_DIR)/$(MODULE_NAME)/measureGeneralMetrics.sh
RUN_BENCHMARK_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/runBenchmark.py

###### global constants

export EXPERIMENTS_ROOT := $(ROOT_DIR)/$(MODULE_NAME)
export EXPERIMENTS_TEMPLATE := $(EXPERIMENTS_ROOT)/experiments_template.mk
MOSALLOC_TEMPLATE := $(MODULE_NAME)/mosalloc_template.mk
export NUMBER_OF_SOCKETS := $(shell ls -d /sys/devices/system/node/node*/ | wc -w)
export NUMBER_OF_CORES_PER_SOCKET := $(shell ls -d /sys/devices/system/node/node0/cpu*/ | wc -w)
export MEMORY_PER_SOCKET_KB := $(shell cat /sys/devices/system/node/node0/meminfo | \grep MemTotal | cut -d":" -f 2 | tr -d "[ kB]")
export MEMORY_PER_SOCKET_MB := $(shell echo $$(( $(MEMORY_PER_SOCKET_KB) / 1024 )) )
export NUM_OF_REPEATS := $$((2 * $(NUMBER_OF_SOCKETS)))
BOUND_MEMORY_NODE := 1

define configuration_array
$(addprefix configuration,$(shell seq 1 $1))
endef

#### export env. variables

export MMAP_POOL_SIZE := $$(( $(MEMORY_FOOTPRINT) ))
export BRK_POOL_SIZE := $$(( $(MEMORY_FOOTPRINT) ))
export FILE_POOL_SIZE := $$(( 1 * $(GIBI) ))
export TOTAL_SIZE_POOLS := $$(( $(MMAP_POOL_SIZE) + $(BRK_POOL_SIZE) ))
export LARGE_PAGES_FOR_POOLS := $$(( $(TOTAL_SIZE_POOLS) / $(LARGE_PAGE_SIZE) ))
export HUGE_PAGES_FOR_POOLS := $$(( $(TOTAL_SIZE_POOLS) / $(HUGE_PAGE_SIZE) ))
export MMAP_LARGE_PAGES := $$(( $(MMAP_POOL_SIZE) / $(LARGE_PAGE_SIZE) ))
export MMAP_HUGE_PAGES := $$(( $(MMAP_POOL_SIZE) / $(HUGE_PAGE_SIZE) ))
export BRK_LARGE_PAGES := $$(( $(BRK_POOL_SIZE) / $(LARGE_PAGE_SIZE) ))
export BRK_HUGE_PAGES := $$(( $(BRK_POOL_SIZE) / $(HUGE_PAGE_SIZE) ))

#### recipes and rules for prerequisites

.PHONY: experiments-prerequisites perf numactl

experiments-prerequisites: perf numactl

PERF_PACKAGES := linux-tools
KERNEL_VERSION := $(shell uname -r)
PERF_PACKAGES := $(addsuffix -$(KERNEL_VERSION),$(PERF_PACKAGES))
perf:
	$(CHECK_PARANOID)
	sudo apt install -y "$(PERF_PACKAGES)"

numactl:
	sudo apt install -y $@

TEST_RUN_MOSALLOC_TOOL := $(ROOT_DIR)/$(MODULE_NAME)/testRunMosallocTool.sh
.PHONY: test-run-mosalloc-tool
test-run-mosalloc-tool: $(RUN_MOSALLOC_TOOL) $(MOSALLOC_TOOL)
	$(TEST_RUN_MOSALLOC_TOOL) $<

.PHONY: reserve-max-1gb-pages
reserve-max-1gb-pages:
ifndef SKIP_RESERVE_MAX_1GB
	for i in $$(seq 0 $$(( $(NUMBER_OF_SOCKETS)-1 ))); do
		$(RESERVE_HUGE_PAGES) --node=$$i --huge=$(HUGE_PAGES_FOOTPRINT) --large=0
	done
else
	echo "Skipping reserve-max-1gb-pages..."
endif

include $(ROOT_DIR)/common.mk

