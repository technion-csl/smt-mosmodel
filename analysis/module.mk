MODULE_NAME := analysis
SUBMODULES := \
	memory_footprint \
	growing_window_2m \
	sliding_window random_window_2m \
	sliding_window_50 random_window_1g \
	sliding_window_20 sliding_window_40 sliding_window_60 sliding_window_80 \
	train_mosmodel test_mosmodel all_data \
	tlb_misses_vs_table_walks \
	single_page_size model_errors perf_mem
	# general_metrics
	# mmap_brk_effects growing_window_with_offset
	# user_defined_window mosalloc_overhead energy_vs_runtime
	# test_collect strace_memory perf_mem
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

COLLECT_RESULTS := $(ROOT_DIR)/$(MODULE_NAME)/collectResults.py
ARRANGE_DATA_TO_PLOT_SCRIPT := $(MODULE_NAME)/arrangeDataToPlot.py
SCATTER_PLOT_SCRIPT := $(MODULE_NAME)/plotScatter.gp
WHISKER_PLOT_SCRIPT := $(MODULE_NAME)/plotWhisker.gp
POLY_PLOT_SCRIPT := $(MODULE_NAME)/assessPolynomialModels.py
BUILD_OVERHEAD_SCRIPT := $(MODULE_NAME)/buildOverheadSummary.py
COLLECT_MEMORY_FOOTPRINT := $(ROOT_DIR)/$(MODULE_NAME)/collectMemoryFootprint.py

COMMON_ANALYSIS_MAKEFILE := $(MODULE_NAME)/common.mk

include $(ROOT_DIR)/common.mk

