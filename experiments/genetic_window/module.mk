MODULE_NAME := experiments/genetic_window
GENETIC_WINDOW_EXP_DIR := $(MODULE_NAME)

NUM_LAYOUTS := 33
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

#FIXME: MEM_BINS_2MB_CSV_FILE is not defined at this stage
GENETIC_WINDOW_INTERMEDIATE_RESULTS := results/genetic_window/phony results/single_page_size/phony
.PHONY: $(GENETIC_WINDOW_INTERMEDIATE_RESULTS)
$(GENETIC_WINDOW_INTERMEDIATE_RESULTS): results/%/phony:
	layouts=`ls -dm experiments/$*/layout*[!s] | sed 's,experiments/$*/,,g' | tr -d ' \n'`
	#echo "ls -dm experiments/$*/layout*[!s] | sed 's,experiments/$*/,,g' | tr -d ' \n'"
	#echo '******************************** $$layouts ********************************'
	mkdir -p $(dir $@)
	$(COLLECT_RESULTS_SCRIPT) --experiments_root=experiments/$* --repeats=$(NUM_OF_REPEATS) \
		--layouts=$$layouts --output_dir=$(dir $@)

CREATE_GENETIC_WINDOW_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(MEMORY_FOOTPRINT_FILE) experiments/single_page_size/layout4kb/repeat1/perf.out experiments/single_page_size/layout2mb/repeat1/perf.out $(GENETIC_WINDOW_INTERMEDIATE_RESULTS) analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv
	$(CREATE_GENETIC_WINDOW_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--single_page_size_results=results/single_page_size/mean.csv \
		--genetic_results=results/genetic_window/mean.csv \
		--pebs_mem_bins=$(MEM_BINS_2MB_CSV_FILE) \
		--layout=$@ \
		--layouts_dir=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine LAYOUTS
