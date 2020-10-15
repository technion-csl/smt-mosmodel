MODULE_NAME := analysis/mosmodel
SUBMODULES := test train 
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

MOSMODEL_TEMPLATE_MAKEFILE := $(MODULE_NAME)/template.mk

#************* scripts *************
VALIDATE_MODELS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/validateModels.py
AGGREGATE_ERRORS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/aggregateErrorsOverLayouts.py
PLOT_MAX_ERRORS_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/plotMaxErrors.py
COLLECT_POLYNOMIAL_COEFFICIENTS := $(ROOT_DIR)/$(MODULE_NAME)/collectPolynomialCoefficients.py
CROSS_VALIDATE_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/crossValidateModel.py
CALCULATE_R_SQUARES_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/calculateRSquares.py

#************* consts *************
MAX_ERRORS_PLOT_TITLE := "Max Errors"
TRAIN_ERRORS_FILE := $(MODULE_NAME)/train_errors.csv
TEST_ERRORS_FILE := $(MODULE_NAME)/test_errors.csv
CROSS_VALIDATION_FILE := $(MODULE_NAME)/cross_validation.csv
POLY_FILE = $(MODULE_NAME)/poly3.csv
UNIFIED_MEAN_FILE := $(MODULE_NAME)/mean.csv

TRAIN_MAX_ERRORS := $(MODULE_NAME)/train_max_errors.csv
TEST_MAX_ERRORS := $(MODULE_NAME)/test_max_errors.csv
TEST_AVG_ERRORS := $(MODULE_NAME)/test_avg_errors.csv
POLY_COEFFICIENTS := $(MODULE_NAME)/poly_coefficients.csv
CROSS_VALIDATION_MAX_ERRORS := $(MODULE_NAME)/cross_validation_max_errors.csv
CROSS_VALIDATION_AVG_ERRORS := $(MODULE_NAME)/cross_validation_avg_errors.csv
MAX_ERRORS_PLOTS := $(MODULE_NAME)/linear_models.pdf $(MODULE_NAME)/polynomial_models.pdf

$(MODULE_NAME): $(MAX_ERRORS_PLOTS) $(TRAIN_MAX_ERRORS) $(TEST_MAX_ERRORS) \
	$(TEST_AVG_ERRORS) $(CROSS_VALIDATION_MAX_ERRORS) $(CROSS_VALIDATION_AVG_ERRORS)

$(MAX_ERRORS_PLOTS): $(TRAIN_MAX_ERRORS)
	$(PLOT_MAX_ERRORS_SCRIPT) --max_errors=$(TRAIN_MAX_ERRORS) --plot_title=$(MAX_ERRORS_PLOT_TITLE) --output=$(@D)

$(TRAIN_MAX_ERRORS): $(TRAIN_ERRORS_FILE)
	$(AGGREGATE_ERRORS_SCRIPT) \
		--errors_file=$(TRAIN_ERRORS_FILE) --function=max \
		--output=$@

$(TEST_MAX_ERRORS): $(TEST_PER_BENCHMARK_ERRORS)
	$(AGGREGATE_ERRORS_SCRIPT) \
		--errors_file=$(TEST_ERRORS_FILE) --function=max \
		--output=$@

$(TEST_AVG_ERRORS): $(TEST_PER_BENCHMARK_ERRORS)
	$(AGGREGATE_ERRORS_SCRIPT) \
		--errors_file=$(TEST_ERRORS_FILE) --function=avg \
		--output=$@

$(POLY_COEFFICIENTS):
	$(COLLECT_POLYNOMIAL_COEFFICIENTS) --output=$@

$(TRAIN_ERRORS_FILE): $(TRAIN_MEAN_CSV_FILE) $(LINEAR_MODELS_COEFFS) 
	mkdir -p $(dir $@)
	$(VALIDATE_MODELS_SCRIPT) --train_dataset=$(TRAIN_MEAN_CSV_FILE) --test_dataset=$(TRAIN_MEAN_CSV_FILE) --output=$@ \
		--coeffs_file=$(LINEAR_MODELS_COEFFS) --poly=/dev/null

$(TEST_ERRORS_FILE): $(TEST_MEAN_CSV_FILE) $(TRAIN_MEAN_CSV_FILE) $(LINEAR_MODELS_COEFFS)
	mkdir -p $(dir $@)
	$(VALIDATE_MODELS_SCRIPT) --train_dataset=$(TRAIN_MEAN_CSV_FILE) --test_dataset=$(TEST_MEAN_CSV_FILE) --output=$@ \
		--coeffs_file=$(LINEAR_MODELS_COEFFS) --poly=$(dir $@)/$(POLY_FILE)

$(CROSS_VALIDATION_MAX_ERRORS): $(CROSS_VALIDATION_FILE)
	$(AGGREGATE_ERRORS_SCRIPT) \ 
		--errors_file=$(CROSS_VALIDATION_FILE) --function=max --columns=mosmodel,poly3,poly2,poly1 \
		--output=$@

$(CROSS_VALIDATION_AVG_ERRORS): $(CROSS_VALIDATION_FILE)
	$(AGGREGATE_ERRORS_SCRIPT) \
		--errors_file=$(CROSS_VALIDATION_FILE) --function=avg --columns=mosmodel,poly3,poly2,poly1 \
		--output=$@

$(CROSS_VALIDATION_FILE):$(UNIFIED_MEAN_FILE) 
	$(CROSS_VALIDATE_SCRIPT) --input=$< --output=$@

$(UNIFIED_MEAN_FILE): $(TRAIN_ERRORS_FILE) $(TEST_ERRORS_FILE)
	mkdir -p $(dir $@)
	head -n 1 -q $< > $@
	tail -n +2 -q $^ >> $@


$(MODULE_NAME)/clean:
	rm -f *.pdf
	rm -f *.csv

include $(ROOT_DIR)/common.mk
