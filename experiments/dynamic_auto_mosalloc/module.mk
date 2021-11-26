MODULE_NAME := experiments/dynamic_auto_mosalloc
DYNAMIC_AUTO_MOSALLOC_EXPERIMENT := $(MODULE_NAME)

DYNAMIC_AUTO_MOSALLOC_NUM_OF_REPEATS := $(NUMBER_OF_SOCKETS)
NUM_LAYOUTS := 55
NUM_OF_REPEATS := $(DYNAMIC_AUTO_MOSALLOC_NUM_OF_REPEATS)
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

CREATE_DYNAMIC_AUTO_MOSALLOC_LAYOUTS := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(DYNAMIC_AUTO_MOSALLOC_EXPERIMENT)/layouts/%.csv: $(MEMORY_FOOTPRINT_FILE) $(AUTO_MOSALLOC_EXPERIMENT) analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv results/single_page_size/mean.csv
	mkdir -p results/dynamic_auto_mosalloc
	$(COLLECT_RESULTS) --experiments_root=experiments/dynamic_auto_mosalloc --repeats=$(NUM_OF_REPEATS) \
		--output_dir=results/dynamic_auto_mosalloc --remove_outliers
	$(CREATE_DYNAMIC_AUTO_MOSALLOC_LAYOUTS) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--single_page_size_mean=results/single_page_size/mean.csv \
		--pebs_mem_bins=$(MEM_BINS_2MB_CSV_FILE) \
		--results_mean_file=results/dynamic_auto_mosalloc/mean.csv \
		--layout=$* \
		--layouts_dir=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine NUM_OF_REPEATS
override undefine LAYOUTS
