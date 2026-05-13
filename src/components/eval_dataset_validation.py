"""
Evaluation Dataset Validation Component.

This module handles the integrity check for the golden dataset used in
qualitative evaluation (LLM-as-a-Judge):
- Verifying the presence and loadability of the golden samples.
- Ensuring the ground truth dataset is versioned and ready for CI/CD gates.
- Recording the validation status for DVC pipeline tracking.
"""

from src.entity.config_entity import EvalDatasetConfig
from src.evals.judge_harness import load_golden_dataset
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EvalDatasetValidation:
    """
    Handles the validation and integrity enforcement of the golden dataset.

    This component ensures that the qualitative evaluation ground truth is
    available and correctly structured before the evaluation harness executes.
    """

    def __init__(self, config: EvalDatasetConfig):
        """
        Initializes the EvalDatasetValidation component.

        Args:
            config (EvalDatasetConfig): Configuration entity containing root
                directories and status file paths.
        """
        self.config = config

    def validate(self):
        """
        Validates the golden dataset and records the validation status.

        This method attempts to load the dataset via the judge harness. If
        successful, it touches a status file in the artifacts directory to
        signal completion to the DVC pipeline.

        Raises:
            Exception: If the dataset cannot be loaded or the status file
                cannot be written.
        """
        logger.info("Starting Golden Dataset validation component...")
        try:
            samples = load_golden_dataset()
            logger.info(f"Successfully loaded {len(samples)} golden samples.")

            # Record validation status
            with open(self.config.status_file, "w") as f:
                f.write("VALIDATED")

            logger.info(
                f"Golden Dataset validation complete. Status recorded at: {self.config.status_file}"
            )
        except Exception as e:
            logger.error(f"Golden Dataset validation failed in component: {e}")
            raise e
