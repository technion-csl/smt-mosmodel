MODULE_NAME := experiments/strace_memory
SUBMODULES := 

include $(ROOT_DIR)/common.mk

STRACE_COMMAND := strace -e trace=memory -ff -o strace.out
EXPERIMENT_DIRS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))

$(MODULE_NAME): $(EXPERIMENT_DIRS)

.PHONY: $(EXPERIMENT_DIRS)
$(EXPERIMENT_DIRS): EXPERIMENT_ROOT_DIR := $(ROOT_DIR)/$(MODULE_NAME)

$(EXPERIMENT_DIRS): $(MODULE_NAME)/%: $(MOSALLOC_TOOL) | experiments-prerequisites benchmarks/%
	cd $(EXPERIMENT_ROOT_DIR)
	export LD_PRELOAD=$(MOSALLOC_TOOL)
	$(RUN_BENCHMARK) $* -s "$(STRACE_COMMAND)"

CLEAN_TARGETS := $(addsuffix /clean,$(EXPERIMENT_DIRS))
$(CLEAN_TARGETS): %/clean: %/delete
$(MODULE_NAME)/clean: $(CLEAN_TARGETS)

