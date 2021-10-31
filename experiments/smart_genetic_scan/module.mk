MODULE_NAME := experiments/smart_genetic_scan
SMART_GENETIC_SCAN_EXP_DIR := $(MODULE_NAME)

NUM_LAYOUTS := 33
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

CREATE_SMART_GENETIC_SCAN_LAYOUTS := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(SMART_GENETIC_SCAN_EXP_DIR)/layouts/%.csv: $(MEMORY_FOOTPRINT_FILE) $(SINGLE_PAGE_SIZE_EXPERIMENT) analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv
	mkdir -p results/smart_genetic_scan
	$(COLLECT_RESULTS) --experiments_root=experiments/smart_genetic_scan --repeats=$(NUM_OF_REPEATS) \
		--output_dir=results/smart_genetic_scan --remove_outliers
	$(CREATE_SMART_GENETIC_SCAN_LAYOUTS) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--results_root_dir=results/ \
		--experiments_root_dir=experiments/ \
		--pebs_mem_bins=analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv \
		--layout=$* \
		--layouts_dir=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine LAYOUTS
