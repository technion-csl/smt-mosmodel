MODULE_NAME := experiments/general_metrics/libhugetlbfs_1gb
SUBMODULES := 

include $(ROOT_DIR)/common.mk

include $(GENERAL_METRICS_LIBHUGETLBFS_COMMON_INCLUDE)

$(EXPERIMENT_DIRS): REQUESTED_LARGE_PAGES := 0
$(EXPERIMENT_DIRS): REQUESTED_HUGE_PAGES := $(HUGE_PAGES_FOOTPRINT)
$(EXPERIMENT_DIRS): HUGETLB_MORECORE := 1gb

$(EXPERIMENT_DIRS): $(LIBHUGETLBFS_LIB)

MOUNT_SCRIPT := software/libhugetlbfs/mount1gbHugetlbfs.sh
MOUNT_POINT_1GB_FILE_SYSTEM := /mnt/hugetlbfs_1GB_pages
MOUNT_POINT_EMPTY_FILE := $(MOUNT_POINT_1GB_FILE_SYSTEM)/mounted
$(EXPERIMENT_DIRS): | $(MOUNT_POINT_EMPTY_FILE)
$(MOUNT_POINT_EMPTY_FILE):
	$(MOUNT_SCRIPT) $(MOUNT_POINT_1GB_FILE_SYSTEM)
	touch $@	# the empty file will be deleted on reboot,
				# and thus we will have to mount again hugetlbs

BIG_MEMORY_EXPERIMENT_DIRS := $(addprefix $(MODULE_NAME)/,$(BIG_MEMORY_BENCHMARKS))
$(BIG_MEMORY_EXPERIMENT_DIRS): | reserve-max-1gb-pages

