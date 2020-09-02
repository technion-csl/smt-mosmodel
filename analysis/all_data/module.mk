MODULE_NAME := analysis/all_data
SUBMODULES := 

PLOT_ALL_MOSMODEL_POINTS_SCRIPT := $(MODULE_NAME)/plotAllPoints.py
MOSMODEL_CHART_FILE_NAME := table_walks_scatter.pdf
PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
MOSMODEL_CHARTS := $(addsuffix /$(MOSMODEL_CHART_FILE_NAME),$(PER_BENCHMARK_TARGETS))

$(PER_BENCHMARK_TARGETS): %: %/$(MOSMODEL_CHART_FILE_NAME)

$(MODULE_NAME): $(PER_BENCHMARK_TARGETS)

$(MOSMODEL_CHARTS): $(MODULE_NAME)/%/$(MOSMODEL_CHART_FILE_NAME): analysis/train_mosmodel/%/mean.csv analysis/test_mosmodel/%/mean.csv
	mkdir -p $(dir $@)
	$(PLOT_ALL_MOSMODEL_POINTS_SCRIPT) --train_mean_file=$(word 1,$^) --test_mean_file=$(word 2,$^) --output=$(dir $@)


DELETE_TARGETS := $(addsuffix /delete,$(PER_BENCHMARK_TARGETS))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk


