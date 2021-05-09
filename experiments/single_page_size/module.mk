MODULE_NAME := experiments/single_page_size
LAYOUTS := layout1gb layout2mb layout4kb

EXTRA_ARGS_FOR_MOSALLOC := --analyze


include $(EXPERIMENTS_TEMPLATE)

CREATE_SINGLE_PAGE_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(BENCHMARK_MAX_RES_MEMORY_FILE)
	$(CREATE_SINGLE_PAGE_LAYOUTS_SCRIPT) --max_res_memory_kb=`cat $<` --mmap_pool_limit=$(MMAP_POOL_LIMIT) --output=$@


$(MODULE_NAME)/clean:
	rm -rf experiments/single_page_size/layouts

# undefine LAYOUTS to allow next makefiles to use the defaults LAYOUTS
undefine EXTRA_ARGS_FOR_MOSALLOC
undefine LAYOUTS
