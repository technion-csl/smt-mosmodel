export BENCHMARKS_ROOT := #TODO: the benchmarks source root directory

INTERESTING_BENCHMARKS := #TODO: add your benchmarks list to build the Mosmodel for them (separated by spaces).
								# For example: INTERESTING_BENCHMARKS := gups/32GB gups/16GB gups/8GB
	
INTERESTING_BENCHMARKS_LIST := $(call array_to_comma_separated,$(INTERESTING_BENCHMARKS))
.PHONY: print-benchmarks
print-benchmarks:
	echo $(INTERESTING_BENCHMARKS)

# some constants
export KIBI := $$(( 1024 ))
export MIBI := $$(( 1024 * 1024 ))
export GIBI := $$(( 1024 * 1024 * 1024 ))
export BASE_PAGE_SIZE := $$(( 4 * $(KIBI) ))
export LARGE_PAGE_SIZE := $$(( 2 * $(MIBI) ))
export HUGE_PAGE_SIZE := $$(( 1 * $(GIBI) ))
#TODO: MEMORY_FOOTPRINT can be modified to hold the memory footprint of the largest workload
		# this os required to make the first run which analyzes the pools sizes.
export MEMORY_FOOTPRINT := $$(( 38 * $(GIBI) ))
export LARGE_PAGES_FOOTPRINT := $$(( $(MEMORY_FOOTPRINT) / $(LARGE_PAGE_SIZE) ))
export HUGE_PAGES_FOOTPRINT := $$(( $(MEMORY_FOOTPRINT) / $(HUGE_PAGE_SIZE) ))

