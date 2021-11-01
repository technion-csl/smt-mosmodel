MODULE_NAME := experiments/ratio_window

RATIO_WINDOW_NUM_OF_REPEATS := $(NUMBER_OF_SOCKETS)
NUM_LAYOUTS := 33
NUM_OF_REPEATS := $(RATIO_WINDOW_NUM_OF_REPEATS)
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

CREATE_RATIO_WINDOW_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(MEMORY_FOOTPRINT_FILE) analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv
	$(CREATE_RATIO_WINDOW_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--input_file=$(MEM_BINS_2MB_CSV_FILE) \
		--num_layouts=$(NUM_LAYOUTS) \
		--output=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine NUM_OF_REPEATS
override undefine LAYOUTS
