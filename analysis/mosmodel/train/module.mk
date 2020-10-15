MODULE_NAME := analysis/mosmodel/train
SUBMODULES := 

MOSMODEL_TRAIN_MEAN_CSV_FILE := $(MODULE_NAME)/mean.csv

MODEL_EXPERIMENTS := growing_window_2m random_window_2m sliding_window/window_20 sliding_window/window_40 sliding_window/window_60 sliding_window/window_80

include $(MOSMODEL_TEMPLATE_MAKEFILE)
