ANALYSIS_SLIDING_WINDOW_MODULE_NAME := analysis/sliding_window
SUBMODULES := 

define analysis-sliding-makefiles
SLIDING_WINDOW_WEIGHT := $(1)
include $(ANALYSIS_SLIDING_WINDOW_MODULE_NAME)/template.mk
endef

$(foreach w,$(SLIDING_WINDOW_WEIGHTS),$(eval $(call analysis-sliding-makefiles,$(w))))

