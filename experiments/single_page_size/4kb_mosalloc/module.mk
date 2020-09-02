MODULE_NAME := experiments/single_page_size/4kb_mosalloc
SUBMODULES := 

include $(ROOT_DIR)/common.mk

include $(SINGLE_PAGE_SIZE_COMMON_INCLUDE)

$(EXPERIMENT_DIRS): ARGS_FOR_MOSALLOC_TOOL := -fps $(FILE_POOL_SIZE) \
	-bps $(MEMORY_FOOTPRINT) -aps $(MEMORY_FOOTPRINT) -l $(MOSALLOC_TOOL)

