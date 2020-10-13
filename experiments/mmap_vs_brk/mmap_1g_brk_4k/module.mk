MODULE_NAME := experiments/mmap_vs_brk/mmap_1g_brk_4k
SUBMODULES :=

include $(ROOT_DIR)/common.mk

include $(MMAP_VS_BRK_COMMON_INCLUDE)

$(EXPERIMENT_DIRS): ARGS_FOR_MOSALLOC_TOOL := -fps $(FILE_POOL_SIZE) \
	-bps $(BRK_POOL_SIZE) \
   	-aps $(MMAP_POOL_SIZE) --anon_end_1gb $(MMAP_POOL_SIZE) \
	-l $(MOSALLOC_TOOL)

