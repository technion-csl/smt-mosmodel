ifndef NUM_LAYOUTS
NUM_LAYOUTS := 9
endif # ifndef NUM_LAYOUTS

ifndef LAYOUTS
LAYOUTS := $(shell seq 1 $(NUM_LAYOUTS))
LAYOUTS := $(addprefix layout,$(LAYOUTS)) 
endif #ifndef LAYOUTS

ifndef NUM_OF_REPEATS
NUM_OF_REPEATS := 4
endif # ifndef NUM_OF_REPEATS

EXPERIMENT_DIR := $(MODULE_NAME)
RESULT_DIR := $(subst experiments,results,$(EXPERIMENT_DIR))
RESULT_DIRS += $(RESULT_DIR)

LAYOUTS_FILE := $(EXPERIMENT_DIR)/layouts.txt

EXPERIMENTS := $(addprefix $(EXPERIMENT_DIR)/,$(LAYOUTS)) 
RESULTS := $(addsuffix /mean.csv,$(RESULT_DIR)) 

REPEATS := $(shell seq 1 $(NUM_OF_REPEATS))
REPEATS := $(addprefix repeat,$(REPEATS)) 

EXPERIMENT_REPEATS := $(foreach experiment,$(EXPERIMENTS),$(foreach repeat,$(REPEATS),$(experiment)/$(repeat)))
MEASUREMENTS := $(addsuffix /perf.out,$(EXPERIMENT_REPEATS))

$(EXPERIMENT_DIR): $(MEASUREMENTS)
$(EXPERIMENTS): $(EXPERIMENT_DIR)/layout%: $(foreach repeat,$(REPEATS),$(addsuffix /$(repeat)/perf.out,$(EXPERIMENT_DIR)/layout%))
$(EXPERIMENT_REPEATS): %: %/perf.out

$(MEASUREMENTS): EXTRA_ARGS_FOR_MOSALLOC := $(EXTRA_ARGS_FOR_MOSALLOC)
$(MEASUREMENTS): $(EXPERIMENT_DIR)/layout%: $(LAYOUTS_FILE) | experiments-prerequisites
	echo ========== [INFO] start producing: $@ ==========
	ARGS_FOR_MOSALLOC="$(shell grep layout"$(shell echo $* | cut -d '/' -f 1)" $< | cut -d ':' -f 2)"
	if [ -z "$$ARGS_FOR_MOSALLOC" ];
	then
		echo "Cannot find the layout configuration to run: $@"
		exit -1
	fi
	$(RUN_BENCHMARK) --submit_command "$(MEASURE_GENERAL_METRICS) $(SET_CPU_MEMORY_AFFINITY) $(BOUND_MEMORY_NODE) \
		$(RUN_MOSALLOC_TOOL) --library $(MOSALLOC_TOOL) $$ARGS_FOR_MOSALLOC $(EXTRA_ARGS_FOR_MOSALLOC)" -- \
		$(BENCHMARK_PATH) $(dir $@)

results: $(RESULT_DIR)
$(RESULTS): LAYOUT_LIST := $(call array_to_comma_separated,$(LAYOUTS))
$(RESULT_DIR): $(RESULTS)
$(RESULTS): results/%/mean.csv: experiments/%
	mkdir -p $(dir $@)
	$(COLLECT_RESULTS) --experiments_root=$< --repeats=$(NUM_OF_REPEATS) \
		--layouts=$(LAYOUT_LIST) --output_dir=$(dir $@)

DELETED_TARGETS := $(EXPERIMENTS) $(EXPERIMENT_REPEATS) $(LAYOUTS_FILE)
CLEAN_TARGETS := $(addsuffix /clean,$(DELETED_TARGETS))
$(CLEAN_TARGETS): %/clean: %/delete
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)


