MODULE_NAME := experiments/subgroups_windows

NUM_LAYOUTS := 33

include $(EXPERIMENTS_TEMPLATE)

CREATE_SUBGROUPS_WINDOWS_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(MEMORY_FOOTPRINT_FILE) $(HOT_REGION_FILE)
	$(CREATE_SUBGROUPS_WINDOWS_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--hot_region=$(HOT_REGION_FILE) \
		--num_layouts=$(NUM_LAYOUTS) \
		--output=$(dir $@)/..

override undefine NUM_LAYOUTS
