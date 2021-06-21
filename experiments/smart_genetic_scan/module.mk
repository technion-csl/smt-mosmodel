MODULE_NAME := experiments/smart_genetic_scan
SMART_GENETIC_SCAN_EXP_DIR := $(MODULE_NAME)

NUM_LAYOUTS := 33
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

CREATE_SMART_GENETIC_SCAN_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(SMART_GENETIC_SCAN_EXP_DIR)/layouts/%.csv: $(MEMORY_FOOTPRINT_FILE) \
	experiments/single_page_size/layout4kb \
	experiments/single_page_size/layout2mb \
	analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv
	mkdir -p results/single_page_size
	$(COLLECT_RESULTS_SCRIPT) --experiments_root=experiments/single_page_size --repeats=$(NUM_OF_REPEATS) \
		--layouts=layout4kb,layout2mb --output_dir=results/single_page_size
	mkdir -p results/smart_genetic_scan
	layouts=''
	-layouts=`ls -dm experiments/smart_genetic_scan/layout*[!s] | sed 's,experiments/smart_genetic_scan/,,g' | tr -d ' \n'`
	$(COLLECT_RESULTS_SCRIPT) --experiments_root=experiments/smart_genetic_scan --repeats=$(NUM_OF_REPEATS) \
		--layouts=$$layouts --output_dir=results/smart_genetic_scan
	$(CREATE_SMART_GENETIC_SCAN_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--single_page_size_results=results/single_page_size/mean.csv \
		--smart_genetic_results=results/smart_genetic_scan/mean.csv \
		--pebs_mem_bins=analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv \
		--layout=$* \
		--layouts_dir=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine LAYOUTS
