PERF_MEM_EXP_WORKLOADS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))

PERF_RECORD_FREQUENCY := $$(( 2**15 ))
PERF_MEM_ACCESSES_EVENTS := mem_uops_retired.all_loads:p,mem_uops_retired.all_stores:p
PERF_MEM_STLB_MISSES_EVENTS := mem_uops_retired.stlb_miss_loads:p,mem_uops_retired.stlb_miss_stores:p
PERF_MEM_RECORD_BASE := perf record --data --count=$(PERF_RECORD_FREQUENCY)
PERF_MEM_RECORD := $(PERF_MEM_RECORD_BASE) --event=$(PERF_MEM_EVENTS)

$(MODULE_NAME): $(PERF_MEM_EXP_WORKLOADS)
$(PERF_MEM_EXP_WORKLOADS): EXPERIMENT_ROOT_DIR := $(ROOT_DIR)/$(MODULE_NAME)

$(PERF_MEM_EXP_WORKLOADS): $(MODULE_NAME)/%: $(MOSALLOC_TOOL) | experiments-prerequisites
	cd $(EXPERIMENT_ROOT_DIR)
	$(RUN_BENCHMARK) $* --exclude_files="perf.data" --submit_command \
		"$(PERF_MEM_RECORD_BASE) --event=$(PERF_MEM_EVENTS) -- \
		$(RUN_MOSALLOC_TOOL) --analyze $(MOSALLOC_POOLS_ARGS) -l $(MOSALLOC_TOOL)"

DELETE_TARGETS := $(addsuffix /delete,$(PERF_MEM_EXP_WORKLOADS))

$(MODULE_NAME)/clean: $(DELETE_TARGETS)

