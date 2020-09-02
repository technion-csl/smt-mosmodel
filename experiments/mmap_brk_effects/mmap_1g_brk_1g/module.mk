MODULE_NAME := experiments/mmap_brk_effects/mmap_1g_brk_1g
SUBMODULES :=

include $(ROOT_DIR)/common.mk

include $(MMAP_BRK_EFFECTS_COMMON_INCLUDE)

$(EXPERIMENT_DIRS): ARGS_FOR_MOSALLOC_TOOL := -fps $(FILE_POOL_SIZE) \
	-bps $(BRK_POOL_SIZE) -be1 $(BRK_POOL_SIZE) \
   	-aps $(MMAP_POOL_SIZE) -ae1 $(MMAP_POOL_SIZE) \
	-l $(MOSALLOC_TOOL)

