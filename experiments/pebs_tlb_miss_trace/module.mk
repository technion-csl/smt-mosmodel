MODULE_NAME := experiments/pebs_tlb_miss_trace
SUBMODULES :=

PERF_RECORD_FREQUENCY := $$(( 2**15 ))
STLB_MISS_LOADS_PEBS_EVENT := $(shell perf list | grep retired | grep mem | grep stlb_miss_loads | tr -d ' ')
STLB_MISS_STORES_PEBS_EVENT := $(shell perf list | grep retired | grep mem | grep stlb_miss_stores | tr -d ' ')
PERF_MEM_STLB_MISSES_EVENTS := $(STLB_MISS_LOADS_PEBS_EVENT):p,$(STLB_MISS_STORES_PEBS_EVENT):p
PERF_MEM_RECORD_CMD := perf record --data --count=$(PERF_RECORD_FREQUENCY) --event=$(PERF_MEM_STLB_MISSES_EVENTS)

PEBS_TLB_MISS_TRACE_OUTPUT := $(MODULE_NAME)/perf.data
$(MODULE_NAME): $(PEBS_TLB_MISS_TRACE_OUTPUT)

$(PEBS_TLB_MISS_TRACE_OUTPUT): $(MOSALLOC_TOOL) experiments/single_page_size/layouts.txt
	cd $(dir $@)
	ARGS_FOR_MOSALLOC="$(shell grep layout4k experiments/single_page_size/layouts.txt | cut -d ':' -f 2)"
	$(PERF_MEM_RECORD_CMD) -- \
		$(RUN_MOSALLOC_TOOL) --analyze $$ARGS_FOR_MOSALLOC --library $(MOSALLOC_TOOL) -- $(BENCHMARK)

DELETE_TARGETS := $(addsuffix /delete,$(PEBS_TLB_MISS_TRACE_OUTPUT))

$(MODULE_NAME)/clean:
	rm -f $(PEBS_TLB_MISS_TRACE_OUTPUT)
	cd $(dir $@)
	rm -f *csv*
	rm -f *.out


