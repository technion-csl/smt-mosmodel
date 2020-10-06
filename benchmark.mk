export BENCHMARK := /home/idanyani/csl-benchmarks/my_gups/sequential-2GB/sequential

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

export MMAP_POOL_LIMIT := $$(( 100 * $(MIBI) ))
