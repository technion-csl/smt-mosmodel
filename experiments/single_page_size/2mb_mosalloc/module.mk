MODULE_NAME := experiments/single_page_size/2mb_mosalloc
SUBMODULES := 

include $(ROOT_DIR)/common.mk

include $(SINGLE_PAGE_SIZE_COMMON_INCLUDE)

$(EXPERIMENT_DIRS): ARGS_FOR_MOSALLOC_TOOL := -fps $(FILE_POOL_SIZE) \
	-bps $(MEMORY_FOOTPRINT) -be2 $(MEMORY_FOOTPRINT) \
   	-aps $(GIBI) -ae2 $(GIBI) \
	-l $(MOSALLOC_TOOL)

