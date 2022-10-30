MOSELECT_EXPERIMENT_NAME := moselect
MODULE_NAME := experiments/$(MOSELECT_EXPERIMENT_NAME)

MOSELECT_EXPERIMENT := $(MODULE_NAME)
MOSELECT_RESULTS := $(subst experiments,results,$(MOSELECT_EXPERIMENT))
MOSELECT_NUM_LAYOUTS ?= 50
NUM_LAYOUTS := $(MOSELECT_NUM_LAYOUTS)
NUM_OF_REPEATS := 1
undefine LAYOUTS #allow the template to create new layouts based on the new NUM_LAYOUTS

include $(EXPERIMENTS_TEMPLATE)

CREATE_MOSELECT_LAYOUTS_SCRIPT := $(MODULE_NAME)/createLayouts.py
$(LAYOUT_FILES): $(ROOT_DIR)/$(MOSELECT_EXPERIMENT)/layouts/%.csv: $(MEMORY_FOOTPRINT_FILE) analysis/pebs_tlb_miss_trace/mem_bins_2mb.csv
	mkdir -p results/$(MOSELECT_EXPERIMENT_NAME)
	$(COLLECT_RESULTS) --experiments_root=$(MOSELECT_EXPERIMENT) --reference=$(TODO) \
		--output_dir=$(MOSELECT_RESULTS)
	$(CREATE_MOSELECT_LAYOUTS_SCRIPT) \
		--memory_footprint=$(MEMORY_FOOTPRINT_FILE) \
		--pebs_mem_bins=$(MEM_BINS_2MB_CSV_FILE) \
		--layout=$* \
		--exp_dir=$(dir $@)/.. \
		--results_file=$(MOSELECT_RESULTS)/median.csv

override undefine NUM_LAYOUTS
override undefine LAYOUTS
