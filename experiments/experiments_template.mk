# Set the layouts to default if they were not defined in the specific 
# experiment makefile (module.mk)
#ifeq $($(LAYOUTS),"")
ifndef LAYOUTS
# Set the number of layouts to default (which is 9) if it was not set by the 
# specific experiment makefile.
ifndef NUM_LAYOUTS
NUM_LAYOUTS := 9
endif # ifndef NUM_LAYOUTS
LAYOUTS := $(shell seq 1 $(NUM_LAYOUTS))
LAYOUTS := $(addprefix layout,$(LAYOUTS)) 
endif #ifndef LAYOUTS

EXPERIMENT_DIR := $(MODULE_NAME)
RESULT_DIR := $(subst experiments,results,$(EXPERIMENT_DIR))

LAYOUTS_FILE := $(EXPERIMENT_DIR)/layouts.txt

EXPERIMENTS := $(addprefix $(EXPERIMENT_DIR)/,$(LAYOUTS)) 
RESULTS := $(addsuffix /mean.csv,$(RESULT_DIR)) 

REPEATS := $(shell seq 1 $(NUM_OF_REPEATS))
REPEATS := $(addprefix repeat,$(REPEATS)) 

EXPERIMENT_REPEATS := $(foreach repeat,$(REPEATS),$(addsuffix /$(repeat),$(EXPERIMENTS)))
MEASUREMENTS := $(addsuffix /perf.out,$(EXPERIMENT_REPEATS))

$(EXPERIMENT_DIR): $(MEASUREMENTS)
$(EXPERIMENTS): $(EXPERIMENT_DIR)/layout%: $(foreach repeat,$(REPEATS),$(addsuffix /$(repeat)/perf.out,$(EXPERIMENT_DIR)/layout%))
$(EXPERIMENT_REPEATS): %: %/perf.out

$(MEASUREMENTS): $(EXPERIMENT_DIR)/layout%: $(LAYOUTS_FILE)
	mkdir -p $(dir $@)
	cd $(dir $@)
	ARGS_FOR_MOSALLOC="$(shell grep layout"$(shell echo $* | cut -d '/' -f 1)" $< | cut -d ':' -f 2)"
	$(MEASURE_GENERAL_METRICS) $(SET_CPU_MEMORY_AFFINITY) $(BOUND_MEMORY_NODE) \
		$(RUN_MOSALLOC_TOOL) --library $(MOSALLOC_TOOL) $$ARGS_FOR_MOSALLOC $(EXTRA_ARGS_FOR_MOSALLOC) -- \
		$(BENCHMARK)

results: $(RESULT_DIR)
$(RESULTS): LAYOUT_LIST := $(call array_to_comma_separated,$(LAYOUTS))
$(RESULT_DIR): $(RESULTS)
$(RESULTS): results/%/mean.csv: experiments/%
	mkdir -p $(dir $@)
	$(COLLECT_RESULTS_SCRIPT) --experiments_root=$< --repeats=$(NUM_OF_REPEATS) \
		--layouts=$(LAYOUT_LIST) --output_dir=$(dir $@)

DELETED_TARGETS := $(EXPERIMENT_REPEATS) $(EXPERIMENTS)
CLEAN_TARGETS := $(addsuffix /clean,$(DELETED_TARGETS))
$(CLEAN_TARGETS): %/clean: %/delete
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)


