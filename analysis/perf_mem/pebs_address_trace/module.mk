MODULE_NAME := analysis/perf_mem/pebs_address_trace
SUBMODULES :=

$(MODULE_NAME)%: PERF_MEM_FIGURE_Y_LABEL := "memory accesses"

include $(PERF_MEM_ANALYSIS_COMMON_MAKEFILE)
include $(ROOT_DIR)/common.mk

