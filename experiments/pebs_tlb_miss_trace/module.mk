MODULE_NAME := experiments/pebs_tlb_miss_trace
SUBMODULES :=

PERF_RECORD_FREQUENCY ?= $$(( 2**6 ))
STLB_MISS_LOADS_PEBS_EVENT = $(shell perf list | grep retired | grep mem | grep stlb_miss_loads | tr -d ' ')
STLB_MISS_STORES_PEBS_EVENT = $(shell perf list | grep retired | grep mem | grep stlb_miss_stores | tr -d ' ')
PERF_MEM_STLB_MISSES_EVENTS = $(STLB_MISS_LOADS_PEBS_EVENT):p,$(STLB_MISS_STORES_PEBS_EVENT):p
PERF_MEM_RECORD_CMD = perf record --data --count=$(PERF_RECORD_FREQUENCY) --event=$(PERF_MEM_STLB_MISSES_EVENTS)

PEBS_OUT_DIR1 := $(MODULE_NAME)/1
PEBS_OUT_DIR2 := $(MODULE_NAME)/2
PEBS_TLB_MISS_TRACE_OUTPUT := $(PEBS_OUT_DIR1)/repeat0/perf.data

$(MODULE_NAME): $(PEBS_TLB_MISS_TRACE_OUTPUT)

$(PEBS_TLB_MISS_TRACE_OUTPUT): experiments/single_page_size/layouts/layout4kb.csv | experiments-prerequisites 
	$(RUN_BENCHMARK) --exclude_files=$(notdir $@) --directory "$(PEBS_OUT_DIR1)" --submit_command \
		"$(PERF_MEM_RECORD_CMD) -- $(RUN_MOSALLOC_TOOL) --analyze -cpf $(ROOT_DIR)/experiments/single_page_size/layouts/layout4kb.csv --library $(MOSALLOC_TOOL)" \
		$(BENCHMARK)

DELETE_TARGETS := $(addsuffix /delete,$(PEBS_TLB_MISS_TRACE_OUTPUT))

$(MODULE_NAME)/clean:
	rm -rf $(PEBS_OUT_DIR1) $(PEBS_OUT_DIR2)

