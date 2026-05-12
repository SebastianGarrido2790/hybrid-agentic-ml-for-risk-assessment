"""
Data Validation Component.

This module handles the validation of ingested data using a dual-contract approach:
- **Structural Validation**: Enforces the schema defined in schema.yaml (column names/types).
- **Statistical Validation**: Enforces data quality and distribution contracts via Great Expectations (GX).
"""

import json
import sys

import great_expectations as gx
import pandas as pd

from src.entity.config_entity import DataValidationConfig
from src.utils.exception import CustomException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataValidation:
    """
    Handles both structural schema enforcement and statistical contract validation.
    """

    def __init__(self, config: DataValidationConfig):
        self.config = config

    def validate_statistical_contracts(self, data: pd.DataFrame) -> bool:
        """
        Validates the data against statistical expectations using Great Expectations.

        Args:
            data: The pandas DataFrame to validate.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        try:
            logger.info("Starting statistical validation with Great Expectations...")

            # Initialize GX context (Ephemeral for lightweight execution)
            context = gx.get_context()

            # Load expectations from JSON
            with open(self.config.EXPECTATIONS_FILE) as f:
                suite_data = json.load(f)

            suite_name = suite_data.get("expectation_suite_name", "acras_suite")
            suite = context.suites.add(gx.ExpectationSuite(name=suite_name))

            # Add expectations from file to the suite
            for exp_dict in suite_data.get("expectations", []):
                exp_type = exp_dict["expectation_type"]
                kwargs = exp_dict["kwargs"]
                # Convert dict to GX Expectation object if needed,
                # but GX 1.x allows adding from dict or using a validator
                # Here we use the Validator approach for simplicity in execution
                pass

            # Setup data source and asset
            datasource_name = "pandas_datasource"
            asset_name = "training_data_asset"

            datasource = context.data_sources.add_pandas(name=datasource_name)
            asset = datasource.add_dataframe_asset(name=asset_name)
            batch_definition = asset.add_batch_definition_whole_dataframe(
                name="training_batch"
            )

            # Create a validation definition
            validation_definition = context.validation_definitions.add(
                gx.ValidationDefinition(
                    name="acras_validation_definition",
                    data=batch_definition,
                    suite=suite,
                )
            )

            # Map expectations from JSON to the suite object
            # In GX 1.x, we use Expectation classes
            from great_expectations.expectations.core.expect_column_values_to_be_between import (
                ExpectColumnValuesToBeBetween,
            )
            from great_expectations.expectations.core.expect_column_values_to_be_in_set import (
                ExpectColumnValuesToBeInSet,
            )
            from great_expectations.expectations.core.expect_column_values_to_not_be_null import (
                ExpectColumnValuesToNotBeNull,
            )

            # Mapping for a few common ones
            type_map = {
                "expect_column_values_to_not_be_null": ExpectColumnValuesToNotBeNull,
                "expect_column_values_to_be_between": ExpectColumnValuesToBeBetween,
                "expect_column_values_to_be_in_set": ExpectColumnValuesToBeInSet,
            }

            for exp_dict in suite_data.get("expectations", []):
                exp_type = exp_dict["expectation_type"]
                kwargs = exp_dict["kwargs"]
                if exp_type in type_map:
                    suite.add_expectation(type_map[exp_type](**kwargs))

            # Run validation
            batch_parameters = {"dataframe": data}
            validation_results = validation_definition.run(
                batch_parameters=batch_parameters
            )

            if not validation_results.success:
                logger.error("Statistical validation failed!")
                return False

            logger.info("Statistical validation passed successfully.")
            return True

        except Exception as e:
            raise CustomException(e, sys)

    def validate_all_columns(self) -> bool:
        """
        Checks if all columns in the dataset exist in the schema and
        runs statistical validation.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        try:
            validation_status = True

            # Read the training data for validation
            data_path = self.config.unzip_data_dir / "train.csv"
            data = pd.read_csv(data_path)
            all_cols = list(data.columns)

            all_schema = self.config.all_schema.keys()

            with open(self.config.STATUS_FILE, "w") as f:
                # 1. Structural Validation (Columns)
                for col in all_cols:
                    if col not in all_schema:
                        validation_status = False
                        logger.error(f"Column {col} not found in schema.")
                        f.write(f"Validation status: {validation_status}\n")
                        f.write(f"Column {col} not in schema.\n")
                        return validation_status

                for col in all_schema:
                    if col not in all_cols:
                        validation_status = False
                        logger.error(f"Schema column {col} not found in data.")
                        f.write(f"Validation status: {validation_status}\n")
                        f.write(f"Schema column {col} not in data.\n")
                        return validation_status

                # 2. Statistical Validation (Great Expectations)
                statistical_status = self.validate_statistical_contracts(data)
                if not statistical_status:
                    validation_status = False
                    f.write(f"Validation status: {validation_status}\n")
                    f.write("Statistical validation (GX) failed.\n")
                    return validation_status

                f.write(f"Validation status: {validation_status}")
                logger.info(f"Full Data validation status: {validation_status}")

            return validation_status

        except Exception as e:
            raise CustomException(e, sys)
