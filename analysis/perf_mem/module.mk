MODULE_NAME := analysis/perf_mem
PERF_MEM_SUBMODULES := pebs_address_trace \
	pebs_tlb_miss_trace test_findHalfWeightWindow
SUBMODULES := $(PERF_MEM_SUBMODULES)
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

PERF_MEM_ANALYSIS_COMMON_MAKEFILE := $(ROOT_DIR)/$(MODULE_NAME)/common.mk

COUNT_MEMORY_ACCESSES_SCRIPT := $(MODULE_NAME)/countMemoryAccesses.py
PARSE_PERF_MEM_RAW_FILE_SCRIPT := $(MODULE_NAME)/parsePerfMem.py 
BIN_ADDRESSES_SCRIPT := $(MODULE_NAME)/binAddresses.py
PLOT_BINS_SCRIPT := $(MODULE_NAME)/plotBins.py
FIND_WINDOW_SCRIPT := $(MODULE_NAME)/findWeightedWindow.py

include $(ROOT_DIR)/common.mk


