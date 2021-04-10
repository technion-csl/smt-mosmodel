MODULE_NAME := analysis/single_page_size
LAYOUTS := layout1gb layout2mb layout4kb

include $(COMMON_ANALYSIS_MAKEFILE)

# undefine LAYOUTS to allow next makefiles to use the defaults LAYOUTS
undefine LAYOUTS

