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

$(PEBS_TLB_MISS_TRACE_OUTPUT): $(ROOT_DIR)/experiments/single_page_size/layouts/layout4kb.csv | experiments-prerequisites 
	experiment_dir=$$(realpath -m $@/../../..)
	$(bind_second_sibling) $(run_benchmark) --directory "$$experiment_dir/2" --loop_until $(measure_timeout) $(BENCHMARK2) &
	$(bind_first_sibling) $(run_benchmark) --directory "$$experiment_dir/1" --loop_until $(measure_timeout) \
		--submit_command "$(PERF_MEM_RECORD_CMD) -- $(RUN_MOSALLOC_TOOL) --library $(MOSALLOC_TOOL) --analyze -cpf $< --library $(MOSALLOC_TOOL)" \
		$(BENCHMARK1)

DELETE_TARGETS := $(addsuffix /delete,$(PEBS_TLB_MISS_TRACE_OUTPUT))

$(MODULE_NAME)/clean:
	rm -rf $(PEBS_OUT_DIR1) $(PEBS_OUT_DIR2)

