MODULE_NAME := experiments/growing_window_with_offset
GROWING_WINDOW_WITH_OFFSET_MODULE_NAME := $(MODULE_NAME)

NUM_OF_CONFIGURATIONS := 5
$(MODULE_NAME)/%: NUM_OF_CONFIGURATIONS := $(NUM_OF_CONFIGURATIONS)
$(MODULE_NAME)/spec_cpu2017/657.xz_s: NUM_OF_CONFIGURATIONS := 9
$(MODULE_NAME)/my_gups/16GB: NUM_OF_CONFIGURATIONS := 6

GROWING_WINDOW_WITH_OFFSET_CONFIGURATIONS := \
	$(call configuration_array,$(NUM_OF_CONFIGURATIONS))
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(GROWING_WINDOW_WITH_OFFSET_CONFIGURATIONS))

GROWING_WINDOW_WITH_OFFSET_NUM_OF_REPEATS := 3
$(MODULE_NAME)/%: NUM_OF_REPEATS := $(GROWING_WINDOW_WITH_OFFSET_NUM_OF_REPEATS)

CONFIGURATION_MAKEFILES := $(addsuffix /module.mk,$(SUBMODULES))
$(CONFIGURATION_MAKEFILES): $(MODULE_NAME)/configuration%/module.mk: \
	$(MOSALLOC_TEMPLATE)
	mkdir -p $(dir $@)
	cp -rf $< $@
	sed -i 's,TEMPLATE_ARG1,$(GROWING_WINDOW_WITH_OFFSET_MODULE_NAME),g' $@
	sed -i 's,TEMPLATE_ARG2,$*,g' $@

PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
$(PER_BENCHMARK_TARGETS): $(MODULE_NAME)/%: $(addsuffix /%,$(SUBMODULES))
	echo "Finished running all configurations of benchmark $*: $^"

CREATE_INCREASING_CONFIGURATIONS_SCRIPT := $(MODULE_NAME)/scanGrowingWindowWithOffset.py

$(MODULE_NAME)/graph500-2.1/4gb/configurations.txt:
	mkdir -p $(dir $@)
	$(CREATE_INCREASING_CONFIGURATIONS_SCRIPT) --effects $(EFFECTS_FILE) \
		--memory_footprints $(MEMORY_FOOTPRINTS_FILE) \
		--benchmark graph500-2.1/4gb \
		--num_configurations $(NUM_OF_CONFIGURATIONS) \
		--start_offset 4831838208 --output $@

$(MODULE_NAME)/xsbench/unionized_16GB/configurations.txt:
	mkdir -p $(dir $@)
	$(CREATE_INCREASING_CONFIGURATIONS_SCRIPT) --effects $(EFFECTS_FILE) \
		--memory_footprints $(MEMORY_FOOTPRINTS_FILE) \
		--benchmark xsbench/unionized_16GB \
		--num_configurations $(NUM_OF_CONFIGURATIONS) \
		--start_offset 0 --output $@

$(MODULE_NAME)/spec_cpu2006/429.mcf/configurations.txt:
	mkdir -p $(dir $@)
	$(CREATE_INCREASING_CONFIGURATIONS_SCRIPT) --effects $(EFFECTS_FILE) \
		--memory_footprints $(MEMORY_FOOTPRINTS_FILE) \
		--benchmark spec_cpu2006/429.mcf \
		--num_configurations $(NUM_OF_CONFIGURATIONS) \
		--start_offset 0 --output $@

$(MODULE_NAME)/spec_cpu2017/623.xalancbmk_s/configurations.txt:
	mkdir -p $(dir $@)
	$(CREATE_INCREASING_CONFIGURATIONS_SCRIPT) --effects $(EFFECTS_FILE) \
		--memory_footprints $(MEMORY_FOOTPRINTS_FILE) \
		--benchmark spec_cpu2017/623.xalancbmk_s \
		--num_configurations $(NUM_OF_CONFIGURATIONS) \
		--start_offset $$(( 340 * $(MIBI) )) --output $@

CONFIGURATION_FILES := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
CONFIGURATION_FILES := $(addsuffix /configurations.txt,$(CONFIGURATION_FILES))
DELETE_TARGETS := $(addsuffix /delete,$(CONFIGURATION_FILES) \
	$(CONFIGURATION_MAKEFILES))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk

