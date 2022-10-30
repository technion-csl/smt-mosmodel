# MODEL_EXPERIMENTS should be set before calling this template

SCATTER_CHART := $(MODULE_NAME)/scatter.pdf
SCATTER_CSV_FILE := $(MODULE_NAME)/scatter.csv
MEAN_CSV_FILE := $(MODULE_NAME)/mean.csv

MODEL_MEAN_CSV_FILES := $(addsuffix /mean.csv,$(MODEL_EXPERIMENTS))
MODEL_MEAN_CSV_FILES := $(addprefix results/,$(MODEL_MEAN_CSV_FILES))
MODEL_EXPERIMENTS := $(addprefix analysis/,$(MODEL_EXPERIMENTS))
MODEL_SCATTER_CSV_FILES := $(addsuffix /scatter.csv,$(MODEL_EXPERIMENTS))

TARGETS := $(SCATTER_CHART) $(SCATTER_CSV_FILE) $(MEAN_CSV_FILE)

$(MODULE_NAME): $(TARGETS)

$(SCATTER_CHART): $(SCATTER_CSV_FILE) 
	legend=`echo $(MODEL_EXPERIMENTS) | sed -e 's,_window,,g' | sed -e 's,_,-,g'`
	gnuplot -e "input_file='$^'" -e "output_file='$@'" -e "legend='$$legend'" $(SCATTER_PLOT)

$(SCATTER_CSV_FILE): $(MODEL_SCATTER_CSV_FILES) 
	head -n 1 -q $< > $@
	tail -n +2 -q $^ >> $@

$(MEAN_CSV_FILE): $(MODEL_MEAN_CSV_FILES)
	head -n 1 -q $< > $@
	tail -n +2 -q $^ >> $@

DELETE_TARGETS := $(addsuffix /delete,$(TARGETS))
$(MODULE_NAME)/clean: $(DELETE_TARGETS)

include $(ROOT_DIR)/common.mk

