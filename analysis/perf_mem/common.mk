PERF_MEM_FIGURE_TITLE := "PEBS trace"
PERF_MEM_REPORT_PREFIX := perf mem -D --field-separator=';'
FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER := sed '1s/,/;/g'

PERF_MEM_WORKLOADS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
MEM_ACCESSES_FILE := mem_accesses.csv
MEM_ACCESSES_FILES := $(addsuffix /$(MEM_ACCESSES_FILE),$(PERF_MEM_WORKLOADS))
MEM_ACCESS_COUNT_FILE := mem_access_count.csv
MEM_ACCESS_COUNT_FILES := $(addsuffix /$(MEM_ACCESS_COUNT_FILE),$(PERF_MEM_WORKLOADS))
MEM_BINS_2MB_CSV_FILE := mem_bins_2mb.csv
MEM_BINS_2MB_CSV_FILES := $(addsuffix /$(MEM_BINS_2MB_CSV_FILE),$(PERF_MEM_WORKLOADS))
MEM_BINS_2MB_CHART_FILE := mem_bins_2mb.pdf
MEM_BINS_2MB_CHART_FILES := $(addsuffix /$(MEM_BINS_2MB_CHART_FILE),$(PERF_MEM_WORKLOADS))
MEM_BINS_4KB_CSV_FILE := mem_bins_4kb.csv
MEM_BINS_4KB_CSV_FILES := $(addsuffix /$(MEM_BINS_4KB_CSV_FILE),$(PERF_MEM_WORKLOADS))

PER_BENCHMARK_FILE_NAMES := $(MEM_ACCESSES_FILE) $(MEM_ACCESS_COUNT_FILE) $(MEM_BINS_4KB_CSV_FILE) $(MEM_BINS_2MB_CSV_FILE) $(MEM_BINS_2MB_CHART_FILE)
PER_BENCHMARK_TARGETS := $(foreach f,$(PER_BENCHMARK_FILE_NAMES),$(addsuffix /$(f),$(PERF_MEM_WORKLOADS)))

PERF_MEM_EXP_DIR := $(MODULE_NAME:analysis%=experiments%)

PER_BENCHMARK_TARGETS_PATTERN := $(foreach f,$(PER_BENCHMARK_FILE_NAMES),$(MODULE_NAME)/%/$(f))
$(PERF_MEM_WORKLOADS): $(MODULE_NAME)/%: $(PER_BENCHMARK_TARGETS_PATTERN)

$(MEM_BINS_2MB_CHART_FILES): $(MODULE_NAME)/%/$(MEM_BINS_2MB_CHART_FILE): $(MODULE_NAME)/%/$(MEM_BINS_2MB_CSV_FILE)
	$(PLOT_BINS_SCRIPT) --input=$^ --output=$@ \
		--figure_y_label=$(PERF_MEM_FIGURE_Y_LABEL) --time_windows=1

$(MEM_BINS_4KB_CSV_FILES): $(MODULE_NAME)/%/$(MEM_BINS_4KB_CSV_FILE): $(PERF_MEM_EXP_DIR)/%
	mkdir -p $(@D)
	$(PERF_MEM_REPORT_PREFIX) -i $^/repeat0/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(BIN_ADDRESSES_SCRIPT) --width=4096 --output=$@ \
		--pools_range_file=$^/repeat0/pools_base_pointers.out

$(MEM_BINS_2MB_CSV_FILES): $(MODULE_NAME)/%/$(MEM_BINS_2MB_CSV_FILE): $(PERF_MEM_EXP_DIR)/%
	mkdir -p $(@D)
	$(PERF_MEM_REPORT_PREFIX) -i $^/repeat0/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(BIN_ADDRESSES_SCRIPT) --width=$$(( 2**21 )) --output=$@ \
		--pools_range_file=$^/repeat0/pools_base_pointers.out

$(MEM_ACCESS_COUNT_FILES): $(MODULE_NAME)/%/$(MEM_ACCESS_COUNT_FILE): $(PERF_MEM_EXP_DIR)/%
	mkdir -p $(@D)
	$(PERF_MEM_REPORT_PREFIX) -i $^/repeat0/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(COUNT_MEMORY_ACCESSES_SCRIPT) -o $@ -p $^/repeat0/pools_base_pointers.out

$(MEM_ACCESSES_FILES): $(MODULE_NAME)/%/$(MEM_ACCESSES_FILE): $(PERF_MEM_EXP_DIR)/%
	mkdir -p $(@D)
	$(PERF_MEM_REPORT_PREFIX) -i $^/repeat0/perf.data report | \
		$(FIX_DELIM_IN_PERF_MEM_OUTPUT_HEADER) | \
		$(PARSE_PERF_MEM_RAW_FILE_SCRIPT) -o $@ -p $^/repeat0/pools_base_pointers.out

CLEAN_TARGETS := $(addsuffix /delete,$(PERF_MEM_WORKLOADS))
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)

