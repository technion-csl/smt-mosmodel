MODULE_NAME := experiments/growing_window_2m

include $(EXPERIMENTS_TEMPLATE)

CREATE_GROWING_WINDOW_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUTS_FILE): $(MEMORY_FOOTPRINT_FILE)
	$(CREATE_GROWING_WINDOW_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) --num_layouts=$(NUM_LAYOUTS) \
		--output=$@


