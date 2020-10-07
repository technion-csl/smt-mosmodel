MODULE_NAME := analysis/memory_footprint

MEMORY_FOOTPRINT_FILE := $(MODULE_NAME)/memory_footprint.csv

$(MEMORY_FOOTPRINT_FILE): | experiments/single_page_size/layout4kb
	$(COLLECT_MEMORY_FOOTPRINT) $| --output=$@

DELETE_TARGETS := $(addsuffix /delete,$(MEMORY_FOOTPRINT_FILE))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)


