MODULE_NAME := analysis/test_mosmodel
SUBMODULES := 

PER_BENCHMARK_TARGETS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
SCATTER_CHARTS := $(addsuffix /scatter.pdf,$(PER_BENCHMARK_TARGETS))
WHISKER_CHARTS := $(addsuffix /whisker.pdf,$(PER_BENCHMARK_TARGETS))
REPEATS_CHARTS := $(addsuffix /all_repeats.pdf,$(PER_BENCHMARK_TARGETS))
SCATTER_CSVS := $(addsuffix /scatter.csv,$(PER_BENCHMARK_TARGETS))
MEAN_CSV_FILES := $(addsuffix /mean.csv,$(PER_BENCHMARK_TARGETS))

TEST_EXPS := random_window_2m
TEST_DIRS := $(addprefix analysis/,$(TEST_EXPS))
TEST_MEAN_CSV_FILES := $(addsuffix /%/mean.csv,$(TEST_DIRS))
TEST_SCATTER_CSV_FILES := $(addsuffix /%/scatter.csv,$(TEST_DIRS))
TEST_WHISKER_CSV_FILES := $(addsuffix /%/whisker.csv,$(TEST_DIRS))
TEST_ALL_REPEATS_CSV_FILES := $(addsuffix /%/all_repeats_scatter.csv,$(TEST_DIRS))

PER_BENCHMARK_CHARTS := %/scatter.pdf %/whisker.pdf %/all_repeats.pdf
$(PER_BENCHMARK_TARGETS): %: $(PER_BENCHMARK_CHARTS) %/mean.csv

$(MODULE_NAME): $(PER_BENCHMARK_TARGETS)

$(SCATTER_CHARTS): $(MODULE_NAME)/%/scatter.pdf: $(MODULE_NAME)/%/scatter.csv
	legend=`echo $(TEST_EXPS) | sed -e 's,_window,,g' | sed -e 's,_,-,g'`
	gnuplot -e "input_file='$^'" -e "output_file='$@'" -e "legend='$$legend'" $(SCATTER_PLOT_SCRIPT)

$(SCATTER_CSVS): $(MODULE_NAME)/%/scatter.csv: $(TEST_SCATTER_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/scatter.csv
	tail -n +2 -q $^ >> $(dir $@)/scatter.csv
	sed -i '/4kb_mosalloc/d' $(dir $@)/scatter.csv
	sed -i '/2mb_mosalloc/d' $(dir $@)/scatter.csv

$(REPEATS_CHARTS): $(MODULE_NAME)/%/all_repeats.pdf: $(TEST_ALL_REPEATS_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/all_repeats.csv
	tail -n +2 -q $^ >> $(dir $@)/all_repeats.csv
	sed -i '/4kb_mosalloc/d' $(dir $@)/all_repeats.csv
	sed -i '/2mb_mosalloc/d' $(dir $@)/all_repeats.csv
	gnuplot -e "input_file='$^'" -e "output_file='$@'" $(SCATTER_PLOT_SCRIPT)

$(WHISKER_CHARTS): $(MODULE_NAME)/%/whisker.pdf: $(TEST_WHISKER_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/whisker.csv
	tail -n +2 -q $^ >> $(dir $@)/whisker.csv
	sed -i '/4kb_mosalloc/d' $(dir $@)/whisker.csv
	sed -i '/2mb_mosalloc/d' $(dir $@)/whisker.csv
	gnuplot -e "input_file='$^'" -e "output_file='$@'" $(WHISKER_PLOT_SCRIPT)

$(MEAN_CSV_FILES): $(MODULE_NAME)/%/mean.csv: $(TEST_MEAN_CSV_FILES)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $(dir $@)/mean.csv
	tail -n +2 -q $^ >> $(dir $@)/mean.csv
	sed -i '/4kb_mosalloc/d' $(dir $@)/mean.csv
	sed -i '/2mb_mosalloc/d' $(dir $@)/mean.csv

DELETE_TARGETS := $(addsuffix /delete,$(PER_BENCHMARK_TARGETS))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk

