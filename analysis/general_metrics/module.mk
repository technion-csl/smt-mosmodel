MODULE_NAME := analysis/general_metrics
SUBMODULES := 

include $(ROOT_DIR)/common.mk

ALL_BENCHMARKS_LIST := $(call array_to_comma_separated,$(INTERESTING_BENCHMARKS))

CALCULATE_WALK_OVERHEAD := $(ROOT_DIR)/$(MODULE_NAME)/calculateWalkOverhead.py
COMPARE_METRICS := $(ROOT_DIR)/$(MODULE_NAME)/compareMetrics.py
CALCULATE_TLB_MISSES := $(ROOT_DIR)/$(MODULE_NAME)/calculateTlbMisses.py
CALCULATE_SLOPE := $(ROOT_DIR)/$(MODULE_NAME)/calculateSlope.py

CSV_FILES := $(addprefix $(MODULE_NAME)/,$(GENERAL_METRICS_SUBMODULES))
CSV_FILES := $(addsuffix /mean.csv,$(CSV_FILES))
WALK_OVERHEAD_FILES := $(CSV_FILES:mean.csv=walk_overhead.txt)
COMPARISON_FILES := $(addsuffix .txt,\
	$(addprefix $(MODULE_NAME)/comparison_,libhugetlbfs_1gb glibc_malloc_no_mmap))
TLB_MISSES_FILE := $(MODULE_NAME)/tlb_misses.txt
SLOPE := $(MODULE_NAME)/slope.txt
SUMMARY_FILES := $(WALK_OVERHEAD_FILES) $(COMPARISON_FILES) \
   $(TLB_MISSES_FILE) $(SLOPE) $(CSV_FILES)

$(MODULE_NAME): $(SUMMARY_FILES)

$(SLOPE): $(MODULE_NAME)/glibc_malloc/mean.csv $(MODULE_NAME)/libhugetlbfs_2mb/mean.csv
	cd $(dir $@)
	$(CALCULATE_SLOPE)

$(TLB_MISSES_FILE): $(CSV_FILES)
	cd $(dir $@)
	$(CALCULATE_TLB_MISSES)

$(WALK_OVERHEAD_FILES): $(MODULE_NAME)/%/walk_overhead.txt: \
	$(MODULE_NAME)/%/mean.csv $(CALCULATE_WALK_OVERHEAD)
	$(CALCULATE_WALK_OVERHEAD) --input=$< --output=$@

$(COMPARISON_FILES): $(MODULE_NAME)/comparison_%.txt: \
	$(MODULE_NAME)/glibc_malloc/mean.csv $(MODULE_NAME)/%/mean.csv $(COMPARE_METRICS)
	$(COMPARE_METRICS) --input1=$(word 1,$^) --input2=$(word 2,$^) \
		--output=$@ --benchmarks=$(ALL_BENCHMARKS_LIST)

$(CSV_FILES): $(MODULE_NAME)/%/mean.csv: | experiments/general_metrics/%
	$(COLLECT_RESULTS) --experiments_root=$(dir $|) \
		--configurations=$* --benchmarks=$(ALL_BENCHMARKS_LIST) \
		--repeats $(NUM_OF_REPEATS) --output_dir=$(dir $@)

DELETE_TARGETS := $(addsuffix /delete,$(SUMMARY_FILES))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

