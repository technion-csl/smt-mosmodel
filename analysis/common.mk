EXPERIMENTS_ROOT := $(MODULE_NAME:analysis%=experiments%)
$(MODULE_NAME)/%: EXPERIMENTS_ROOT := $(EXPERIMENTS_ROOT)

ANALYSIS_DIRS := $(MODULE_NAME)
NORMALIZED_SCATTER_FILE := $(ANALYSIS_DIRS)/normalized_scatter.csv
SCATTER_FILE := $(ANALYSIS_DIRS)/scatter.csv
WHISKER_FILE := $(ANALYSIS_DIRS)/whisker.csv
ALL_REPEATS_SCATTER_FILE := $(ANALYSIS_DIRS)/all_repeats_scatter.csv
NORMALIZED_SCATTER_CHART := $(ANALYSIS_DIRS)/normalized_scatter.pdf
SCATTER_CHART := $(ANALYSIS_DIRS)/scatter.pdf
WHISKER_CHART := $(ANALYSIS_DIRS)/whisker.pdf
ALL_REPEATS_CHART := $(ANALYSIS_DIRS)/all_repeats.pdf
POLY_CHART := $(ANALYSIS_DIRS)/poly.pdf

ALL_CHARTS := $(SCATTER_CHART) $(WHISKER_CHART) $(ALL_REPEATS_CHART) $(POLY_CHART)
ALL_CSVS := $(NORMALIZED_SCATTER_FILE) $(SCATTER_FILE) $(WHISKER_FILE) $(ALL_REPEATS_SCATTER_FILE)

$(MODULE_NAME)%: ALL_CSVS := $(ALL_CSVS) 
$(MODULE_NAME)%: ALL_CHARTS := $(ALL_CHARTS)
$(MODULE_NAME): $(ALL_CSVS) $(ALL_CHARTS)

$(POLY_CHART): $(SCATTER_FILE)
	$(POLY_PLOT_SCRIPT) --metric='cpu-cycles' \
		--input_file=$< --output_file=$@ > $(dir $@)/poly.csv

$(NORMALIZED_SCATTER_CHART): $(NORMALIZED_SCATTER_FILE)
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)

$(SCATTER_CHART): $(SCATTER_FILE)
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)

$(ALL_REPEATS_CHART): $(ALL_REPEATS_SCATTER_FILE)
	if [[ $(NUM_OF_REPEATS) != 1 ]]; then
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)
	fi

$(WHISKER_CHART): $(WHISKER_FILE)
	if [[ $(NUM_OF_REPEATS) != 1 ]]; then
	gnuplot -e "input_file='$<'" -e "output_file='$@'" $(WHISKER_PLOT_SCRIPT)
	fi

$(NORMALIZED_SCATTER_FILE): analysis/%/normalized_scatter.csv: results/%/mean.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --normalize='by-y' --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(SCATTER_FILE): analysis/%/scatter.csv: results/%/mean.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(WHISKER_FILE): analysis/%/whisker.csv: results/%/mean.csv results/%/std.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --normalize='by-y' --y-metric='cpu-cycles' \
		--mean_file=$(word 1,$^) --std_file=$(word 2,$^) --output=$@

$(ALL_REPEATS_SCATTER_FILE): analysis/%/all_repeats_scatter.csv: results/%/all_repeats.csv
	$(ARRANGE_DATA_TO_PLOT_SCRIPT) --y-metric='cpu-cycles' \
		--mean_file=$< --output=$@

$(MODULE_NAME)/clean:
	rm -f $(ALL_CHARTS) $(ALL_CSVS)

include $(ROOT_DIR)/common.mk

