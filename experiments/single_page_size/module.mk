MODULE_NAME := experiments/single_page_size
LAYOUTS := layout2mb layout4kb layout1gb

EXTRA_ARGS_FOR_MOSALLOC := --analyze

#include $(ROOT_DIR)/common.mk
include $(EXPERIMENTS_TEMPLATE)

CREATE_SINGLE_PAGE_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUTS_FILE): $(BENCHMARK_MAX_RES_MEMORY_FILE)
	$(CREATE_SINGLE_PAGE_LAYOUTS_SCRIPT) --max_res_memory_kb=`cat $<` --mmap_pool_limit=$(MMAP_POOL_LIMIT) --output=$@

# undefine LAYOUTS to allow next makefiles to use the defaults LAYOUTS
undefine EXTRA_ARGS_FOR_MOSALLOC
undefine LAYOUTS
