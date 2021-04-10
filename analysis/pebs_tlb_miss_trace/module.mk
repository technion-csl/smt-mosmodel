MODULE_NAME := analysis/pebs_tlb_miss_trace
SUBMODULES := test_findHalfWeightWindow
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

#******** scripts ********
COUNT_MEMORY_ACCESSES_SCRIPT := $(MODULE_NAME)/countMemoryAccesses.py
PARSE_PERF_MEM_RAW_FILE_SCRIPT := $(MODULE_NAME)/parsePerfMem.py 
BIN_ADDRESSES_SCRIPT := $(MODULE_NAME)/binAddresses.py
PLOT_BINS_SCRIPT := $(MODULE_NAME)/plotBins.py
FIND_WINDOW_SCRIPT := $(MODULE_NAME)/findWeightedWindow.py

#******** constants ********
PERF_MEM_REPORT_PREFIX := perf mem -D --field-separator=';'
FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER := sed '1s/,/;/g'

WINDOW_2MB_FILE := $(MODULE_NAME)/hot_region_2mb.txt
WINDOW_4KB_FILE := $(MODULE_NAME)/hot_region_4kb.txt

MEM_ACCESSES_FILE := $(MODULE_NAME)/mem_accesses.csv
MEM_ACCESS_COUNT_FILE := $(MODULE_NAME)/mem_access_count.csv
MEM_BINS_2MB_CSV_FILE := $(MODULE_NAME)/mem_bins_2mb.csv
MEM_BINS_2MB_CHART_FILE := $(MODULE_NAME)/mem_bins_2mb.pdf
MEM_BINS_4KB_CSV_FILE := $(MODULE_NAME)/mem_bins_4kb.csv

PEBS_TARGET_FILES := $(MEM_ACCESSES_FILE) $(MEM_ACCESS_COUNT_FILE) $(MEM_BINS_4KB_CSV_FILE) $(MEM_BINS_2MB_CSV_FILE) $(MEM_BINS_2MB_CHART_FILE) $(WINDOW_2MB_FILE) $(WINDOW_4KB_FILE)
PEBS_EXP_DIR := $(MODULE_NAME:analysis%=experiments%)

$(HOT_REGION_FILE): $(WINDOW_4KB_FILE)
	diff $< $@ > /dev/null 2>&1 || cp --update $< $@

$(MODULE_NAME): $(PEBS_TARGET_FILES)

$(WINDOW_2MB_FILE): $(MEMORY_FOOTPRINT_FILE) $(MEM_BINS_2MB_CSV_FILE)
	echo $<
	mem_footprint=$(shell tail -n1 $< | cut -d ',' -f 4)
	$(FIND_WINDOW_SCRIPT) --input_file=$(MEM_BINS_2MB_CSV_FILE) --output_file=$@ --memory_footprint=$$mem_footprint --page_size=2MB

$(WINDOW_4KB_FILE): $(MEMORY_FOOTPRINT_FILE) $(MEM_BINS_4KB_CSV_FILE)
	mem_footprint=$(shell tail -n1 $< | cut -d ',' -f 4)
	$(FIND_WINDOW_SCRIPT) --input_file=$(MEM_BINS_4KB_CSV_FILE) --output_file=$@ --memory_footprint=$$mem_footprint --page_size=4KB

$(MEM_BINS_2MB_CHART_FILE): $(MEM_BINS_2MB_CSV_FILE)
	$(PLOT_BINS_SCRIPT) --input=$^ --output=$@ \
		--figure_y_label="tlb misses" --time_windows=1

$(MEM_BINS_4KB_CSV_FILE): $(PEBS_EXP_DIR)
	$(PERF_MEM_REPORT_PREFIX) -i $^/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(BIN_ADDRESSES_SCRIPT) --width=4096 --output=$@ \
		--pools_range_file=$^/pools_base_pointers.out

$(MEM_BINS_2MB_CSV_FILE): $(PEBS_EXP_DIR)
	$(PERF_MEM_REPORT_PREFIX) -i $^/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(BIN_ADDRESSES_SCRIPT) --width=$$(( 2**21 )) --output=$@ \
		--pools_range_file=$^/pools_base_pointers.out

$(MEM_ACCESS_COUNT_FILE): $(PEBS_EXP_DIR)
	$(PERF_MEM_REPORT_PREFIX) -i $^/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(COUNT_MEMORY_ACCESSES_SCRIPT) -o $@ -p $^/pools_base_pointers.out

$(MEM_ACCESSES_FILE): $(PEBS_EXP_DIR)
	$(PERF_MEM_REPORT_PREFIX) -i $^/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(PARSE_PERF_MEM_RAW_FILE_SCRIPT) -o $@ -p $^/pools_base_pointers.out

$(MODULE_NAME)/clean:
	rm -rf $(PEBS_TARGET_FILES)
	cd $(dir $@) && rm -f *csv*

