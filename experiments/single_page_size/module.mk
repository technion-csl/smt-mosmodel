MODULE_NAME := experiments/single_page_size
LAYOUTS := layout2mb layout4kb

EXTRA_ARGS_FOR_MOSALLOC := --analyze

include $(EXPERIMENTS_TEMPLATE)

CREATE_SINGLE_PAGE_LAYOUTS := $(MODULE_NAME)/createLayouts.py
$(LAYOUTS_FILE): $(MEMORY_FOOTPRINT_FILE)
	$(CREATE_SINGLE_PAGE_LAYOUTS) --memory_footprint=$< --output=$@

# undefine LAYOUTS to allow next makefiles to use the defaults LAYOUTS
undefine EXTRA_ARGS_FOR_MOSALLOC
undefine LAYOUTS
