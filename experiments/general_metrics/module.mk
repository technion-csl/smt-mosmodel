MODULE_NAME := experiments/general_metrics
GENERAL_METRICS_SUBMODULES := \
	libhugetlbfs_1gb \
	libhugetlbfs_2mb \
	glibc_malloc \
	glibc_malloc_no_mmap
	#dlmalloc libhugetlbfs_thp thp
SUBMODULES := $(GENERAL_METRICS_SUBMODULES)
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

GENERAL_METRICS_COMMON_INCLUDE := $(ROOT_DIR)/$(MODULE_NAME)/common.mk
GENERAL_METRICS_LIBHUGETLBFS_COMMON_INCLUDE := $(ROOT_DIR)/$(MODULE_NAME)/libhugetlbfs_common.mk
RUN_LIBHUGETLBFS_TOOL := $(ROOT_DIR)/$(MODULE_NAME)/runLibhugetlbfs.py

include $(ROOT_DIR)/common.mk

