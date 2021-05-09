MODULE_NAME := experiments/pebs_tlb_miss_trace
SUBMODULES :=

PERF_RECORD_FREQUENCY := $$(( 2**15 ))
PERF_MEM_STLB_MISSES_EVENTS := mem_uops_retired.stlb_miss_loads:p,mem_uops_retired.stlb_miss_stores:p
PERF_MEM_RECORD_CMD := perf record --data --count=$(PERF_RECORD_FREQUENCY) --event=$(PERF_MEM_STLB_MISSES_EVENTS)

PEBS_TLB_MISS_TRACE_OUTPUT := $(MODULE_NAME)/perf.data
$(MODULE_NAME): $(PEBS_TLB_MISS_TRACE_OUTPUT)

$(PEBS_TLB_MISS_TRACE_OUTPUT): $(MOSALLOC_TOOL) experiments/single_page_size/layouts
	cd $(dir $@)
	$(PERF_MEM_RECORD_CMD) -- \
		$(RUN_MOSALLOC_TOOL) --analyze \
		-cpf $(ROOT_DIR)/experiments/single_page_size/layouts/layout4kb.csv \
		--library $(MOSALLOC_TOOL) -- $(BENCHMARK)

DELETE_TARGETS := $(addsuffix /delete,$(PEBS_TLB_MISS_TRACE_OUTPUT))

$(MODULE_NAME)/clean:
	rm -f $(PEBS_TLB_MISS_TRACE_OUTPUT)
	cd $(dir $@)
	rm -f *csv*
	rm -f *.out


