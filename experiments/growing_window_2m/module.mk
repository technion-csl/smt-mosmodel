MODULE_NAME := experiments/growing_window_2m

CREATE_GROWING_WINDOW_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
GROWING_WINDOW_LAYOUTS_FILE := $(MODULE_NAME)/layouts.txt
$(GROWING_WINDOW_LAYOUTS_FILE):
	$(CREATE_GROWING_WINDOW_LAYOUTS_SCRIPT) --memory_footprints=$(MEMORY_FOOTPRINTS_FILE) \
		--num_layouts=$(NUM_OF_GROWING_WINDOW_LAYOUTS) \
		--output_dir=$@

#include $(ROOT_DIR)/common.mk
include $(ROOT_DIR)/experiments/experiments_template.mk
