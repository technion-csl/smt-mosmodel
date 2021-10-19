BENCHMARK_PATH ?= $(ROOT_DIR)/toy_benchmark

# some constants
KIBI := $$(( 1024 ))
MIBI := $$(( 1024 * 1024 ))
GIBI := $$(( 1024 * 1024 * 1024 ))

MMAP_POOL_LIMIT ?= $$(( 100 * $(MIBI) ))

