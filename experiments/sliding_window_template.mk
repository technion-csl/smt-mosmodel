NUM_OF_SLIDING_WINDOW_CONFIGURATIONS := 9
$(SLIDING_WINDOW_MODULE_NAME)/%: NUM_OF_SLIDING_WINDOW_CONFIGURATIONS := $(NUM_OF_SLIDING_WINDOW_CONFIGURATIONS)
SLIDING_WINDOW_CONFIGURATIONS := \
	$(call configuration_array,$(NUM_OF_SLIDING_WINDOW_CONFIGURATIONS))
SUBMODULES := $(addprefix $(SLIDING_WINDOW_MODULE_NAME)/,$(SLIDING_WINDOW_CONFIGURATIONS))

SLIDING_WINDOW_NUM_OF_REPEATS := 3
$(SLIDING_WINDOW_MODULE_NAME)/%: NUM_OF_REPEATS := $(SLIDING_WINDOW_NUM_OF_REPEATS)

SLIDING_WINDOW_CONFIGURATION_MAKEFILES := $(addsuffix /module.mk,$(SUBMODULES))
$(SLIDING_WINDOW_CONFIGURATION_MAKEFILES): $(SLIDING_WINDOW_MODULE_NAME)/configuration%/module.mk: $(MOSALLOC_TEMPLATE)
	mkdir -p $(dir $@)
	cp -rf $< $@
	sed -i 's,TEMPLATE_ARG1,$(SLIDING_WINDOW_MODULE_NAME),g' $@
	sed -i 's,TEMPLATE_ARG2,$*,g' $@

PER_BENCHMARK_TARGETS := $(addprefix $(SLIDING_WINDOW_MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
$(PER_BENCHMARK_TARGETS): $(SLIDING_WINDOW_MODULE_NAME)/%: $(addsuffix /%,$(SUBMODULES))
	echo "Finished running all sliding_window_configurations of benchmark $*: $^"

# For the filtered-out benchmarks, simply copy the runs from another directory.
# We can't override the rule of $(SLIDING_WINDOW_MODULE_NAME)/$(CONFIGURATION)/$(BENCHMARK) because it is defined later
# in the submodules, so we add a dependent target that will copy the directory.
# This is a dirty hack, but this makefile is already dirty anyway...
define not_suitable_benchmarks_rule =
$(SLIDING_WINDOW_MODULE_NAME)/$(CONFIGURATION)/$(BENCHMARK): $(SLIDING_WINDOW_MODULE_NAME)/$(CONFIGURATION)/$(BENCHMARK)/repeat0

$(SLIDING_WINDOW_MODULE_NAME)/$(CONFIGURATION)/$(BENCHMARK)/repeat0: $(GROWING_WINDOW_MODULE_NAME)/configuration1/$(BENCHMARK)
	mkdir -p $$(dir $$@)
	cp -rf --no-target-directory $$< $$(dir $$@)
endef
$(foreach CONFIGURATION,$(SLIDING_WINDOW_CONFIGURATIONS),\
	$(foreach BENCHMARK,$(NOT_SUITABLE_FOR_SLIDING_BENCHMARKS),$(eval $(not_suitable_benchmarks_rule))))

SLIDING_WINDOW_CONFIGURATION_FILES := $(addprefix $(SLIDING_WINDOW_MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
SLIDING_WINDOW_CONFIGURATION_FILES := $(addsuffix /configurations.txt,$(SLIDING_WINDOW_CONFIGURATION_FILES))
SLIDING_WINDOW_CONFIGURATION_OUTPUT_DIR := $(SLIDING_WINDOW_MODULE_NAME)

$(SLIDING_WINDOW_CONFIGURATION_FILES): $(SLIDING_WINDOW_MODULE_NAME)/%/configurations.txt: experiments/sliding_window/%/hot_region.txt	\
	analysis/single_page_size/memory_footprint.csv
	mkdir -p $(dir $@)
	if [[ "$*" == *"gups"* ]] || [[ "$*" == *"471.omnetpp"* && "$(CREATE_SLIDING_EXTRA_PARAMS)" == *"80"* ]]; then
	echo There are no sliding window configurations for this workload > $@
	else
	$(CREATE_SLIDING_WINDOW_CONFIGURATIONS_SCRIPT) \
		$(CREATE_SLIDING_EXTRA_PARAMS) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--hot_region=$< \
		--num_configurations=$(NUM_OF_SLIDING_WINDOW_CONFIGURATIONS) \
		--benchmark $* \
		--output=$@
	fi

DELETE_TARGETS := $(addsuffix /delete,$(SLIDING_WINDOW_CONFIGURATION_FILES) \
	$(SLIDING_WINDOW_CONFIGURATION_MAKEFILES))
$(SLIDING_WINDOW_MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk


