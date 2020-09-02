MODULE_NAME := analysis/perf_mem/pebs_tlb_miss_trace
SUBMODULES :=

PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))

WINDOW_2MB_FILE_NAME := hot_region_2mb.txt
WINDOW_2MB_FILES := $(addsuffix /$(WINDOW_2MB_FILE_NAME),$(INTERESTING_BENCHMARKS))
SLIDING_WINDOW_2MB_FILES := $(addprefix $(HOT_REGION_ROOT_DIR)/,$(WINDOW_2MB_FILES))
WINDOW_2MB_FILES := $(addprefix $(MODULE_NAME)/,$(WINDOW_2MB_FILES))

WINDOW_4KB_FILE_NAME := hot_region_4kb.txt
WINDOW_4KB_FILES := $(addsuffix /$(WINDOW_4KB_FILE_NAME),$(INTERESTING_BENCHMARKS))
SLIDING_WINDOW_4KB_FILES := $(addprefix $(HOT_REGION_ROOT_DIR)/,$(WINDOW_4KB_FILES))
WINDOW_4KB_FILES := $(addprefix $(MODULE_NAME)/,$(WINDOW_4KB_FILES))

$(MODULE_NAME)%: PERF_MEM_FIGURE_Y_LABEL := "tlb misses"
$(MODULE_NAME): $(WINDOW_FILES)  

$(WINDOW_2MB_FILES): $(MODULE_NAME)/%/$(WINDOW_2MB_FILE_NAME): $(MODULE_NAME)/%
	mkdir -p $(dir $@)
	mem_footprint=`grep $*  analysis/single_page_size/memory_footprints.csv | cut -d ',' -f 5`
	$(FIND_WINDOW_SCRIPT) --input_file=$^/$(MEM_BINS_2MB_CSV_FILE) --output_file=$@ --memory_footprint=$$mem_footprint --page_size=2MB

$(WINDOW_4KB_FILES): $(MODULE_NAME)/%/$(WINDOW_4KB_FILE_NAME): $(MODULE_NAME)/%
	mkdir -p $(dir $@)
	mem_footprint=`grep $*  analysis/single_page_size/memory_footprints.csv | cut -d ',' -f 5`
	$(FIND_WINDOW_SCRIPT) --input_file=$^/$(MEM_BINS_4KB_CSV_FILE) --output_file=$@ --memory_footprint=$$mem_footprint --page_size=4KB

.PHONY: copy-weighted-window
copy-weighted-window: $(SLIDING_WINDOW_4KB_FILES)

ifeq ($(MAKECMDGOALS),copy-weighted-window)
$(SLIDING_WINDOW_4KB_FILES): $(HOT_REGION_ROOT_DIR)/%/$(WINDOW_4KB_FILE_NAME): $(MODULE_NAME)/%/$(WINDOW_4KB_FILE_NAME)
	mkdir -p $(dir $@)
	cp -f $< $@
endif

include $(PERF_MEM_ANALYSIS_COMMON_MAKEFILE)
include $(ROOT_DIR)/common.mk


