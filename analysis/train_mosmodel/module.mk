MODULE_NAME := analysis/train_mosmodel
SUBMODULES := 

CALCULATE_R_SQUARES_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/calculateRSquares.py
R_SQUARES := $(MODULE_NAME)/r_squares.csv

PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
SCATTER_CHARTS := $(addsuffix /scatter.pdf,$(PER_BENCHMARK_TARGETS))
WHISKER_CHARTS := $(addsuffix /whisker.pdf,$(PER_BENCHMARK_TARGETS))
REPEATS_CHARTS := $(addsuffix /all_repeats.pdf,$(PER_BENCHMARK_TARGETS))
SCATTER_CSVS := $(addsuffix /scatter.csv,$(PER_BENCHMARK_TARGETS))
MEAN_CSV_FILES := $(addsuffix /mean.csv,$(PER_BENCHMARK_TARGETS))

TRAIN_EXPS := growing_window_2m random_window_2m sliding_window_20 sliding_window_40 sliding_window_60 sliding_window_80
TRAIN_DIRS := $(addprefix analysis/,$(TRAIN_EXPS))
TRAIN_MEAN_CSV_FILES := $(addsuffix /%/mean.csv,$(TRAIN_DIRS))
TRAIN_SCATTER_CSV_FILES := $(addsuffix /%/scatter.csv,$(TRAIN_DIRS))
TRAIN_WHISKER_CSV_FILES := $(addsuffix /%/whisker.csv,$(TRAIN_DIRS))
TRAIN_ALL_REPEATS_CSV_FILES := $(addsuffix /%/all_repeats_scatter.csv,$(TRAIN_DIRS))

PER_BENCHMARK_CHARTS := %/scatter.pdf %/whisker.pdf %/all_repeats.pdf
$(PER_BENCHMARK_TARGETS): %: $(PER_BENCHMARK_CHARTS) %/mean.csv

$(MODULE_NAME): $(PER_BENCHMARK_TARGETS) $(R_SQUARES)

$(SCATTER_CHARTS): $(MODULE_NAME)/%/scatter.pdf: $(MODULE_NAME)/%/scatter.csv
	legend=`echo $(TRAIN_EXPS) | sed -e 's,_window,,g' | sed -e 's,_,-,g'`
	gnuplot -e "input_file='$^'" -e "output_file='$@'" -e "legend='$$legend'" $(SCATTER_PLOT_SCRIPT)

$(SCATTER_CSVS): $(MODULE_NAME)/%/scatter.csv: $(TRAIN_SCATTER_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/scatter.csv
	tail -n +2 -q $^ >> $(dir $@)/scatter.csv

$(REPEATS_CHARTS): $(MODULE_NAME)/%/all_repeats.pdf: $(TRAIN_ALL_REPEATS_CSV_FILES)
	mkdir -p $(dir $@)
	gnuplot -e "input_file='$^'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)
	head -n 1 -q $< > $(dir $@)/all_repeats.csv
	tail -n +2 -q $^ >> $(dir $@)/all_repeats.csv

$(WHISKER_CHARTS): $(MODULE_NAME)/%/whisker.pdf: $(TRAIN_WHISKER_CSV_FILES)
	mkdir -p $(dir $@)
	gnuplot -e "input_file='$^'" -e "output_file='$@'" $(WHISKER_PLOT_SCRIPT)
	head -n 1 -q $< > $(dir $@)/whisker.csv
	tail -n +2 -q $^ >> $(dir $@)/whisker.csv

$(MEAN_CSV_FILES): $(MODULE_NAME)/%/mean.csv: $(TRAIN_MEAN_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/mean.csv
	tail -n +2 -q $^ >> $(dir $@)/mean.csv

$(R_SQUARES): $(MEAN_CSV_FILES)
	$(CALCULATE_R_SQUARES_SCRIPT) --root_dir=analysis/train_mosmodel \
	--benchmarks=$(INTERESTING_BENCHMARKS_LIST) --output=$@

DELETE_TARGETS := $(addsuffix /delete,$(PER_BENCHMARK_TARGETS))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk

