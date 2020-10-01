SHELL := /bin/bash
# all commands in a recipe are passed to a single invocation of the shell
.ONESHELL:

EXPERIMENT_DIR := $(MODULE_NAME)

LAYOUTS_FILE := $(EXPERIMENT_DIR)/layouts.txt

# Please note that NUM_LAYOUTS variable should be defined in the calling makefile
LAYOUTS := $(shell seq 1 $(NUM_LAYOUTS))
LAYOUTS := $(addprefix layout,$(LAYOUTS))
PERF_OUT_FILE := perf.out
EXPERIMENTS := $(addprefix $(EXPERIMENT_DIR)/,$(LAYOUTS))
EXPERIMENTS_PERF_OUT := $(addsuffix /$(PERF_OUT_FILE),$(EXPERIMENTS))

REPEAT_DIRS := $(shell seq 1 $(NUM_OF_REPEATS))
REPEAT_DIRS := $(addprefix repeat,$(REPEAT_DIRS))

REPEAT_NUMBERS := $(shell seq 1 $(NUM_OF_REPEATS))
LAYOUT_NUMBERS := $(shell seq 1 $(NUM_LAYOUTS))

EXPERIMENT_REPEATS := $(addprefix /(REPEAT_DIRS),$(EXPERIMENTS))

dummy:
	echo WIP...

$(EXPERIMENT_DIR): $(EXPERIMENTS_PERF_OUT)
$(EXPERIMENTS): $(EXPERIMENT_DIR)/layout%: $(EXPERIMENT_DIR)/layout%/$(PERF_OUT_FILE)

define EXPERIMENTS_template =
$(EXPERIMENT_DIR)/layout$(LAYOUT)/repeat$(REPEAT)/perf.out: $(EXPERIMENT_DIR)/layout%/repeat$(REPEAT)/perf.out: $(LAYOUTS_FILE)
	mkdir -p $$(dir $$@)
	cd $$(dir $$@)
	if [ -z "$$(BENCHMARK_PATH)" ]; \
		then cp $$(BENCHMARK_COMMAND) .; \
		else cp $$(BENCHMARK_PATH)/* .; \ 
	fi
	ARGS_FOR_TOOL="$$(shell head -$$* $$< | tail -1) \
				  --library $$(MOSALLOC_TOOL)"
	$$(MEASURE_GENERAL_METRICS) $$(SET_CPU_MEMORY_AFFINITY) $$(BOUND_MEMORY_NODE) \
		$$(RUN_MOSALLOC_TOOL) $$$$ARGS_FOR_TOOL -- $$(BENCHMARK_COMMAND)
endef

$(foreach REPEAT,$(REPEAT_NUMBERS), $(foreach LAYOUT,$(LAYOUT_NUMBERS), $(eval $(EXPERIMENTS_template))))

CLEAN_TARGETS := $(addsuffix /clean,$(EXPERIMENT_DIR))
$(CLEAN_TARGETS): %/clean: %/delete
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)


