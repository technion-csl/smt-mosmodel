MODULE_NAME := experiments/perf_mem
PERF_MEM_SUBMODULES := pebs_address_trace \
	pebs_tlb_miss_trace
SUBMODULES := $(PERF_MEM_SUBMODULES)
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

PERF_MEM_EXP_COMMON_MAKEFILE := $(ROOT_DIR)/$(MODULE_NAME)/common.mk

include $(ROOT_DIR)/common.mk

