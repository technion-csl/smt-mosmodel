EXPERIMENTS_ROOT := $(MODULE_NAME:analysis%=experiments%)
$(MODULE_NAME)/%: EXPERIMENTS_ROOT := $(EXPERIMENTS_ROOT)

RESULT_DIRS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
MEAN_FILES := $(addsuffix /mean.csv,$(RESULT_DIRS))
STD_FILES := $(addsuffix /std.csv,$(RESULT_DIRS))
ALL_REPEATS_FILES := $(addsuffix /all_repeats.csv,$(RESULT_DIRS))
NORMALIZED_SCATTER_FILES := $(addsuffix /normalized_scatter.csv,$(RESULT_DIRS))
SCATTER_FILES := $(addsuffix /scatter.csv,$(RESULT_DIRS))
WHISKER_FILES := $(addsuffix /whisker.csv,$(RESULT_DIRS))
ALL_REPEATS_SCATTER_FILES := $(addsuffix /all_repeats_scatter.csv,$(RESULT_DIRS))
NORMALIZED_SCATTER_CHARTS := $(addsuffix /normalized_scatter.pdf,$(RESULT_DIRS))
SCATTER_CHARTS := $(addsuffix /scatter.pdf,$(RESULT_DIRS))
WHISKER_CHARTS := $(addsuffix /whisker.pdf,$(RESULT_DIRS))
ALL_REPEATS_CHARTS := $(addsuffix /all_repeats.pdf,$(RESULT_DIRS))
POLY_CHARTS := $(addsuffix /poly.pdf,$(RESULT_DIRS))

ALL_CHARTS := $(SCATTER_CHARTS) $(WHISKER_CHARTS) $(ALL_REPEATS_CHARTS) $(POLY_CHARTS)
PER_BENCHMARK_CHARTS := %/normalized_scatter.pdf %/scatter.pdf %/whisker.pdf %/all_repeats.pdf %/poly.pdf

$(MODULE_NAME): $(ALL_CHARTS)

PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
$(PER_BENCHMARK_TARGETS): %: $(PER_BENCHMARK_CHARTS)

$(POLY_CHARTS): %/poly.pdf: %/scatter.csv
	$(POLY_PLOT_SCRIPT) --metric='cpu-cycles' \
		--input_file=$< --output_file=$@ > $*/poly.csv

$(NORMALIZED_SCATTER_CHARTS): %/normalized_scatter.pdf: %/normalized_scatter.csv
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)

$(SCATTER_CHARTS): %/scatter.pdf: %/scatter.csv
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)

$(ALL_REPEATS_CHARTS): %/all_repeats.pdf: %/all_repeats_scatter.csv
	if [[ $(NUM_OF_REPEATS) != 1 ]]; then
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)
	fi

$(WHISKER_CHARTS): %/whisker.pdf: %/whisker.csv
	if [[ $(NUM_OF_REPEATS) != 1 ]]; then
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(WHISKER_PLOT_SCRIPT)
	fi

$(NORMALIZED_SCATTER_FILES): %/normalized_scatter.csv: %/mean.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --normalize='by-y' --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(SCATTER_FILES): %/scatter.csv: %/mean.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(WHISKER_FILES): %/whisker.csv: %/mean.csv %/std.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --normalize='by-y' --y-metric='cpu-cycles' \
		--mean_file=$(word 1,$^) --std_file=$(word 2,$^) --output=$@

$(ALL_REPEATS_SCATTER_FILES): %/all_repeats_scatter.csv: %/all_repeats.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(ALL_REPEATS_FILES): %/all_repeats.csv: %/mean.csv
$(STD_FILES): %/std.csv: %/mean.csv
$(MEAN_FILES): $(MODULE_NAME)/%/mean.csv: | $(EXPERIMENTS_ROOT)/%
	$(COLLECT_RESULTS) --experiments_root=$(EXPERIMENTS_ROOT) \
		--configurations=$(CONFIGURATION_LIST) --benchmarks=$* \
		--repeats=$(NUM_OF_REPEATS) --output_dir=$(dir $@)

DELETE_TARGETS := $(addsuffix /delete,$(RESULT_DIRS))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk

