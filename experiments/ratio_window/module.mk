MODULE_NAME := experiments/ratio_window

NUM_LAYOUTS := 33
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

#FIXME: MEM_BINS_2MB_CSV_FILE is not defined at this stage
CREATE_RATIO_WINDOW_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(MEMORY_FOOTPRINT_FILE) $(MEM_BINS_2MB_CSV_FILE)
	$(CREATE_RATIO_WINDOW_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--input_file=$(MEM_BINS_2MB_CSV_FILE) \
		--num_layouts=$(NUM_LAYOUTS) \
		--output=$(dir $@)/..

override undefine NUM_LAYOUTS
override undefine LAYOUTS
