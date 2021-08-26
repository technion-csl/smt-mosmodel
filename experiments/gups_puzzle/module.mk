MODULE_NAME := experiments/gups_puzzle
#FIXME: use wildcards to define layouts
LAYOUTS := layout_2GB-8GB_2mb layout_all_2mb layout_all_4kb #layout_even_2mb
NUM_OF_REPEATS := 3

include $(EXPERIMENTS_TEMPLATE)

