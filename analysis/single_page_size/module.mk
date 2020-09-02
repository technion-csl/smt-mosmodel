MODULE_NAME := analysis/single_page_size
SUBMODULES := 

$(MODULE_NAME)/%: NUM_OF_REPEATS := $(SINGLE_PAGE_SIZE_NUM_OF_REPEATS)
$(MODULE_NAME)/%: CONFIGURATION_LIST := \
	$(call array_to_comma_separated,$(SINGLE_PAGE_SIZE_CONFIGURATIONS))

include $(COMMON_ANALYSIS_MAKEFILE)

MEMORY_FOOTPRINTS_FILE := $(MODULE_NAME)/memory_footprints.csv

SINGLE_PAGE_SIZE_CSV_FILES := $(addprefix $(MODULE_NAME)/,$(SINGLE_PAGE_SIZE_SUBMODULES))
SINGLE_PAGE_SIZE_CSV_FILES := $(addsuffix /mean.csv,$(SINGLE_PAGE_SIZE_CSV_FILES))

BUILD_LINEAR_MODELS_COEFFS := $(ROOT_DIR)/$(MODULE_NAME)/buildLinearModelsCoeffs.py
LINEAR_MODELS_COEFFS := $(MODULE_NAME)/linear_models_coeffs.csv
MEAN_2MB_CSV_FILE := $(MODULE_NAME)/2mb_mosalloc/mean.csv
MEAN_4KB_CSV_FILE := $(MODULE_NAME)/4kb_mosalloc/mean.csv

SUMMARY_FILES := $(SINGLE_PAGE_SIZE_CSV_FILES) $(LINEAR_MODELS_COEFFS) $(MEMORY_FOOTPRINTS_FILE)

$(LINEAR_MODELS_COEFFS): $(SINGLE_PAGE_SIZE_CSV_FILES)
	$(BUILD_LINEAR_MODELS_COEFFS) --benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--mean_2mb_file=$(MEAN_2MB_CSV_FILE) --mean_4kb_file=$(MEAN_4KB_CSV_FILE) \
		--output=$(LINEAR_MODELS_COEFFS)

$(SINGLE_PAGE_SIZE_CSV_FILES): $(MODULE_NAME)/%/mean.csv: | experiments/single_page_size/%
	$(COLLECT_RESULTS) --experiments_root=$(dir $|) \
		--configurations=$* --benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--repeats $(NUM_OF_REPEATS) --output_dir=$(dir $@)

$(MEMORY_FOOTPRINTS_FILE): | experiments/single_page_size/4kb_mosalloc
	$(COLLECT_MEMORY_FOOTPRINTS) $| \
		--output=$@ --benchmarks=$(INTERESTING_BENCHMARKS_LIST)

DELETE_TARGETS := $(addsuffix /delete,$(SUMMARY_FILES))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

