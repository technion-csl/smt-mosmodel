ifndef NUM_LAYOUTS
NUM_LAYOUTS := 9
endif # ifndef NUM_LAYOUTS

ifndef LAYOUTS
LAYOUTS := $(shell seq 1 $(NUM_LAYOUTS))
LAYOUTS := $(addprefix layout,$(LAYOUTS)) 
endif #ifndef LAYOUTS

$(MODULE_NAME)%: NUM_LAYOUTS := $(NUM_LAYOUTS)
$(MODULE_NAME)%: EXTRA_ARGS_FOR_MOSALLOC := $(EXTRA_ARGS_FOR_MOSALLOC)

EXPERIMENT_DIR := $(MODULE_NAME)

LAYOUTS_DIR := $(ROOT_DIR)/$(EXPERIMENT_DIR)/layouts
LAYOUT_FILES := $(addprefix $(LAYOUTS_DIR)/,$(LAYOUTS))
LAYOUT_FILES := $(addsuffix .csv,$(LAYOUT_FILES))

$(LAYOUTS_DIR): $(LAYOUT_FILES)

EXPERIMENTS := $(addprefix $(EXPERIMENT_DIR)/,$(LAYOUTS)) 
MEASUREMENTS := $(addsuffix /1/repeat0/perf.out,$(EXPERIMENTS))

$(EXPERIMENT_DIR): $(MEASUREMENTS)
$(EXPERIMENTS): $(EXPERIMENT_DIR)/%: $(EXPERIMENT_DIR)/%/1/repeat0/perf.out

$(MEASUREMENTS): $(EXPERIMENT_DIR)/%/1/repeat0/perf.out: $(ROOT_DIR)/$(EXPERIMENT_DIR)/layouts/%.csv | experiments-prerequisites
	echo ========== [INFO] start producing: $@ ==========
	experiment_dir=$$(realpath -m $@/../../..)
	$(bind_first_sibling) $(run_benchmark) --directory "$$experiment_dir/1" --loop_until $(measure_timeout) --submit_command "$(measure_perf_events) $(RUN_MOSALLOC_TOOL) --library $(MOSALLOC_TOOL) -cpf $< $(EXTRA_ARGS_FOR_MOSALLOC)" -- $(BENCHMARK1) &
	$(bind_second_sibling) $(run_benchmark) --directory "$$experiment_dir/2" --loop_until $(measure_timeout) $(BENCHMARK2)
	wait

RESULT_DIR := $(subst experiments,results,$(EXPERIMENT_DIR))
RESULT_DIRS += $(RESULT_DIR)
RESULTS := $(addsuffix /mean.csv,$(RESULT_DIR)) 

results: $(RESULT_DIR)
$(RESULTS): LAYOUT_LIST := $(call array_to_comma_separated,$(LAYOUTS))
$(RESULT_DIR): $(RESULTS)
$(RESULTS): results/%/mean.csv: experiments/% $(INSTRUCTION_COUNT_FILE)
	mkdir -p $(dir $@)
	$(COLLECT_RESULTS) --experiments_root=$< --layouts=$(LAYOUT_LIST) --output_dir=$(dir $@) \
		--instruction_count=$(INSTRUCTION_COUNT_FILE)

DELETED_TARGETS := $(EXPERIMENTS) $(EXPERIMENT_REPEATS) $(LAYOUTS_DIR)
CLEAN_TARGETS := $(addsuffix /clean,$(DELETED_TARGETS))
$(CLEAN_TARGETS): %/clean: %/delete
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)

