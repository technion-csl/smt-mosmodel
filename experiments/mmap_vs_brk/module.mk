MODULE_NAME := experiments/mmap_vs_brk
MMAP_VS_BRK_SUBMODULES := \
	mmap_1g_brk_1g \
	mmap_1g_brk_4k \
	mmap_4k_brk_1g \
	mmap_4k_brk_4k
SUBMODULES := $(MMAP_VS_BRK_SUBMODULES)
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

MMAP_VS_BRK_COMMON_INCLUDE := $(ROOT_DIR)/$(MODULE_NAME)/common.mk

export MMAP_POOL_SIZE := $$(( $(MEMORY_FOOTPRINT) ))
export BRK_POOL_SIZE := $$(( 1 * $(GIBI) ))
export FILE_POOL_SIZE := $$(( 1 * $(GIBI) ))
export TOTAL_SIZE_POOLS := $$(( $(MMAP_POOL_SIZE) + $(BRK_POOL_SIZE) ))
export LARGE_PAGES_FOR_POOLS := $$(( $(TOTAL_SIZE_POOLS) / $(LARGE_PAGE_SIZE) ))
export HUGE_PAGES_FOR_POOLS := $$(( $(TOTAL_SIZE_POOLS) / $(HUGE_PAGE_SIZE) ))
export MMAP_LARGE_PAGES := $$(( $(MMAP_POOL_SIZE) / $(LARGE_PAGE_SIZE) ))
export MMAP_HUGE_PAGES := $$(( $(MMAP_POOL_SIZE) / $(HUGE_PAGE_SIZE) ))
export BRK_LARGE_PAGES := $$(( $(BRK_POOL_SIZE) / $(LARGE_PAGE_SIZE) ))
export BRK_HUGE_PAGES := $$(( $(BRK_POOL_SIZE) / $(HUGE_PAGE_SIZE) ))

include $(ROOT_DIR)/common.mk

.PHONY: find-interesting
WALK_OVERHEAD_ANALYSIS := analysis/general_metrics/glibc_malloc/walk_overhead.txt
find-interesting: $(WALK_OVERHEAD_ANALYSIS)
	cat $< | tr -s " " | cut -f2 -d" " | tail -n +2 > $(INTERESTING_BENCHMARKS_FILE)

