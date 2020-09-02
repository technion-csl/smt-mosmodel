MODULE_NAME := experiments/sliding_window_80
SLIDING_WINDOW_MODULE_NAME := $(MODULE_NAME)
$(MODULE_NAME)%: SLIDING_WINDOW_MODULE_NAME := $(MODULE_NAME)
$(MODULE_NAME)%: CREATE_SLIDING_EXTRA_PARAMS := --weight=80
include $(ROOT_DIR)/experiments/sliding_window_template.mk

