MODULE_NAME := all
$(MODULE_NAME):

SHELL := /bin/bash
# all commands in a recipe are passed to a single invocation of the shell
.ONESHELL:

export ROOT_DIR := $(PWD)
export HOST_NAME := $(shell hostname)
LOG_FILE := $(ROOT_DIR)/log

# global auxiliary functions
comma := ,
empty :=
space := $(empty) $(empty)

define array_to_comma_separated
$(subst $(space),$(comma),$(strip $1))
endef

# the following list should preserve a topological ordering, i.e., if module B
# uses variables defined in module A, than module A should come before module B
SUBMODULES := experiments analysis

include benchmark.mk
include $(ROOT_DIR)/common.mk

# a top-level "clean" target, which calls all/clean
.PHONY: clean
clean: all/clean
	rm -f $(LOG_FILE)

# a generic pattern rule for deleting files
.PHONY: %/delete
%/delete:
	rm -rf $*

# empty recipes to prevent make from remaking the makefile and include files
# https://www.gnu.org/software/make/manual/html_node/Remaking-Makefiles.html
makefile: ;
$(ROOT_DIR)/common.mk: ;

