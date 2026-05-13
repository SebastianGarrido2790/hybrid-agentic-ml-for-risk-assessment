"""
Stage 07: Eval Dataset Validation Pipeline.

This stage ensures the golden dataset for qualitative evaluation is intact
and ready for the evaluation harness.
"""

import sys

from src.components.eval_dataset_validation import EvalDatasetValidation
from src.config.configuration import ConfigurationManager
from src.utils.exception import CustomException
from src.utils.logger import get_logger

STAGE_NAME = "Eval Dataset Validation stage"
logger = get_logger(__name__)


class EvalDatasetValidationPipeline:
    """
    Orchestrates the Golden Dataset Validation stage.
    """

    def __init__(self):
        pass

    def main(self):
        """
        Executes the evaluation dataset validation stage.
        """
        config = ConfigurationManager()
        eval_dataset_config = config.get_eval_dataset_config()
        eval_validation = EvalDatasetValidation(config=eval_dataset_config)
        eval_validation.validate()


if __name__ == "__main__":
    try:
        logger.info(f"STARTED: {STAGE_NAME}")
        obj = EvalDatasetValidationPipeline()
        obj.main()
        logger.info(f"COMPLETED: {STAGE_NAME}")
    except Exception as e:
        logger.error(CustomException(e, sys))
        raise e
