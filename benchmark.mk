export BENCHMARK_ROOT_DIR := $(ROOT_DIR)/benchmark
export BENCHMARK := $(BENCHMARK_ROOT_DIR)/run.sh
ifndef BENCHMARK
	$(error "BENCHMARK environment variable is not defined!")
endif

# some constants
export KIBI := $$(( 1024 ))
export MIBI := $$(( 1024 * 1024 ))
export GIBI := $$(( 1024 * 1024 * 1024 ))
export BASE_PAGE_SIZE := $$(( 4 * $(KIBI) ))
export LARGE_PAGE_SIZE := $$(( 2 * $(MIBI) ))
export HUGE_PAGE_SIZE := $$(( 1 * $(GIBI) ))

export MMAP_POOL_LIMIT := $$(( 100 * $(MIBI) ))
