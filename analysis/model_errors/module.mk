MODULE_NAME := analysis/model_errors
SUBMODULES := 

#TODO FIXME remove redundant/unnecessary targets and variables

LINEAR_MODELS_ROOT := $(MODULE_NAME)
RESULT_DIRS := $(addprefix $(MODULE_NAME)/,$(INTERESTING_BENCHMARKS))
VALIDATE_MODELS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/validateModels.py
AGGREGATE_ERRORS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/aggregateErrorsOverLayouts.py
PLOT_MAX_ERRORS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/plotMaxErrors.py
COLLECT_POLYNOMIAL_COEFFICIENTS := $(ROOT_DIR)/$(MODULE_NAME)/collectPolynomialCoefficients.py
CROSS_VALIDATE_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/crossValidateModel.py

TRAIN_ERRORS_FILE_NAME := train_errors.csv
TEST_ERRORS_FILE_NAME := test_errors.csv
CROSS_VALIDATION_FILE_NAME := cross_validation.csv
POLY_FILE_NAME = poly3.csv

UNIFIED_MEAN_PER_BENCHMARK := $(addsuffix /mean.csv,$(RESULT_DIRS))
CROSS_VALIDATION_PER_BENCHMARK := $(addsuffix /$(CROSS_VALIDATION_FILE_NAME),$(RESULT_DIRS))
TRAIN_PER_BENCHMARK_ERRORS := $(addsuffix /$(TRAIN_ERRORS_FILE_NAME),$(RESULT_DIRS))
TEST_PER_BENCHMARK_ERRORS := $(addsuffix /$(TEST_ERRORS_FILE_NAME),$(RESULT_DIRS))

TRAIN_MAX_ERRORS := $(MODULE_NAME)/train_max_errors.csv
TEST_MAX_ERRORS := $(MODULE_NAME)/test_max_errors.csv
TEST_AVG_ERRORS := $(MODULE_NAME)/test_avg_errors.csv
POLY_COEFFICIENTS := $(MODULE_NAME)/poly_coefficients.csv
CROSS_VALIDATION_MAX_ERRORS := $(MODULE_NAME)/cross_validation_max_errors.csv
CROSS_VALIDATION_AVG_ERRORS := $(MODULE_NAME)/cross_validation_avg_errors.csv
MAX_ERRORS_PLOTS := $(MODULE_NAME)/linear_models.pdf $(MODULE_NAME)/polynomial_models.pdf

PLOT_TITLE := "N/A"
ifeq "$(HOST_NAME)" "dante931"
	PLOT_TITLE := "Broadwell"
else ifeq "$(HOST_NAME)" "tapuz40"
	PLOT_TITLE := "Haswell"
else ifeq "$(HOST_NAME)" "wrath"
	PLOT_TITLE := "SandyBridge"
endif

$(MODULE_NAME): $(MAX_ERRORS_PLOTS) $(TRAIN_MAX_ERRORS) $(TEST_MAX_ERRORS) \
	$(TEST_AVG_ERRORS) $(CROSS_VALIDATION_MAX_ERRORS) $(CROSS_VALIDATION_AVG_ERRORS)

$(MAX_ERRORS_PLOTS): $(TRAIN_MAX_ERRORS)
	$(PLOT_MAX_ERRORS_SCRIPT) --max_errors=$(TRAIN_MAX_ERRORS) --plot_title=$(PLOT_TITLE) --output=$(@D)

$(TRAIN_MAX_ERRORS): $(TRAIN_PER_BENCHMARK_ERRORS)
	$(AGGREGATE_ERRORS_SCRIPT) --errors_root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--errors_file_name=$(TRAIN_ERRORS_FILE_NAME) --function=max \
		--output=$@

$(TEST_MAX_ERRORS): $(TEST_PER_BENCHMARK_ERRORS)
	$(AGGREGATE_ERRORS_SCRIPT) --errors_root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--errors_file_name=$(TEST_ERRORS_FILE_NAME) --function=max \
		--output=$@

$(TEST_AVG_ERRORS): $(TEST_PER_BENCHMARK_ERRORS)
	$(AGGREGATE_ERRORS_SCRIPT) --errors_root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--errors_file_name=$(TEST_ERRORS_FILE_NAME) --function=avg \
		--output=$@

$(POLY_COEFFICIENTS):
	$(COLLECT_POLYNOMIAL_COEFFICIENTS) --root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) --output=$@

$(TRAIN_PER_BENCHMARK_ERRORS): $(MODULE_NAME)/%/$(TRAIN_ERRORS_FILE_NAME): analysis/train_mosmodel/%/mean.csv $(LINEAR_MODELS_COEFFS) 
	mkdir -p $(dir $@)
	$(VALIDATE_MODELS_SCRIPT) --benchmark=$* --train_dataset=$(word 1,$^) --test_dataset=$(word 1,$^) --output=$@ \
		--coeffs_file=$(LINEAR_MODELS_COEFFS) --poly=/dev/null

$(TEST_PER_BENCHMARK_ERRORS): $(MODULE_NAME)/%/$(TEST_ERRORS_FILE_NAME): analysis/train_mosmodel/%/mean.csv analysis/test_mosmodel/%/mean.csv $(LINEAR_MODELS_COEFFS)
	mkdir -p $(dir $@)
	$(VALIDATE_MODELS_SCRIPT) --benchmark=$* --train_dataset=$(word 1,$^) --test_dataset=$(word 2,$^) --output=$@ \
		--coeffs_file=$(LINEAR_MODELS_COEFFS) --poly=$(dir $@)/$(POLY_FILE_NAME)

$(CROSS_VALIDATION_MAX_ERRORS): $(CROSS_VALIDATION_PER_BENCHMARK)
	$(AGGREGATE_ERRORS_SCRIPT) --errors_root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--errors_file_name=$(CROSS_VALIDATION_FILE_NAME) --function=max --columns=mosmodel,poly3,poly2,poly1 \
		--output=$@

$(CROSS_VALIDATION_AVG_ERRORS): $(CROSS_VALIDATION_PER_BENCHMARK)
	$(AGGREGATE_ERRORS_SCRIPT) --errors_root=$(LINEAR_MODELS_ROOT) \
		--benchmarks=$(INTERESTING_BENCHMARKS_LIST) \
		--errors_file_name=$(CROSS_VALIDATION_FILE_NAME) --function=avg --columns=mosmodel,poly3,poly2,poly1 \
		--output=$@

$(CROSS_VALIDATION_PER_BENCHMARK): $(MODULE_NAME)/%/$(CROSS_VALIDATION_FILE_NAME): $(MODULE_NAME)/%/mean.csv
	$(CROSS_VALIDATE_SCRIPT) --input=$< --output=$@

$(UNIFIED_MEAN_PER_BENCHMARK): $(MODULE_NAME)/%/mean.csv: analysis/train_mosmodel/%/mean.csv analysis/test_mosmodel/%/mean.csv
	mkdir -p $(dir $@)
	head -n 1 -q $< > $@
	tail -n +2 -q $^ >> $@


$(MODULE_NAME)/clean:
	rm -rf $(MAX_ERRORS_PLOTS) $(MAX_ERRORS) $(TEST_AVG_ERRORS) \
		$(TRAIN_PER_BENCHMARK_ERRORS) $(TEST_PER_BENCHMARK_ERRORS) \
		$(CROSS_VALIDATION_PER_BENCHMARK) $(UNIFIED_MEAN_PER_BENCHMARK) \
		$(CROSS_VALIDATION_MAX_ERRORS) $(TRAIN_MAX_ERRORS) $(TEST_MAX_ERRORS)

