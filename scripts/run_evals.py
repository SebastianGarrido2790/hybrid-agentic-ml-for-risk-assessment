"""
CLI Runner for the ACRAS LLM-as-a-Judge Evaluation Suite.

This script provides a command-line interface to execute the qualitative
evaluation harness against the golden dataset. Results are saved as a
timestamped JSON report in ``reports/docs/evaluations/``.

Usage:
    # Full suite run (requires API keys):
    uv run python scripts/run_evals.py

    # Dry run (no API calls — validates pipeline wiring):
    uv run python scripts/run_evals.py --dry-run

    # Evaluate a specific sample subset:
    uv run python scripts/run_evals.py --sample-ids GD-001 GD-005 GD-010

    # Pipe output to MLflow (future integration):
    uv run python scripts/run_evals.py --log-mlflow

Exit Codes:
    0 — All evaluated samples passed their dimension thresholds.
    1 — One or more samples failed; check the JSON report for details.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evals.judge_harness import load_golden_dataset, run_eval_suite
from src.utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = Path("artifacts") / "eval_dataset"


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the eval runner."""
    parser = argparse.ArgumentParser(
        prog="run_evals",
        description="ACRAS LLM-as-a-Judge Evaluation Suite Runner",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Skip all LLM calls; return synthetic passing results (for CI wiring tests).",
    )
    parser.add_argument(
        "--sample-ids",
        nargs="*",
        default=None,
        metavar="ID",
        help="Evaluate only the specified sample IDs (e.g. GD-001 GD-005). Default: all.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPORTS_DIR,
        help=f"Directory to save the JSON report. Default: {REPORTS_DIR}",
    )
    parser.add_argument(
        "--log-mlflow",
        action="store_true",
        default=False,
        help="Log aggregate metrics to MLflow (requires MLFLOW_TRACKING_URI).",
    )
    return parser.parse_args()


def _save_report(report_data: dict, output_dir: Path) -> Path:
    """Serialize the eval suite report to a timestamped JSON file.

    Args:
        report_data: Dictionary representation of the ``EvalSuiteReport``.
        output_dir: Directory where the report will be written.

    Returns:
        The absolute path of the written report file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"eval_report_{timestamp}.json"
    out_path.write_text(
        json.dumps(report_data, indent=2, default=str), encoding="utf-8"
    )
    logger.info(f"Report saved to: {out_path}")
    return out_path


def _log_to_mlflow(report_data: dict) -> None:
    """Log aggregate eval metrics to MLflow.

    Args:
        report_data: Dictionary representation of the ``EvalSuiteReport``.
    """
    try:
        import mlflow  # type: ignore[import]

        with mlflow.start_run(run_name="llm_judge_eval"):
            mlflow.log_metrics(
                {
                    "eval/pass_rate": report_data["pass_rate"],
                    "eval/mean_relevance": report_data["mean_relevance"],
                    "eval/mean_faithfulness": report_data["mean_faithfulness"],
                    "eval/mean_tool_usage": report_data["mean_tool_usage"],
                    "eval/mean_business_value": report_data["mean_business_value"],
                }
            )
            mlflow.log_params(
                {
                    "eval/suite_version": report_data["suite_version"],
                    "eval/total_samples": report_data["total_samples"],
                }
            )
        logger.info("Metrics logged to MLflow.")
    except ImportError:
        logger.warning("MLflow not available; skipping metric logging.")
    except Exception as e:
        logger.warning(f"MLflow logging failed: {e}")


def main() -> int:
    """Entry point for the eval runner.

    Returns:
        Exit code: 0 for all-pass, 1 for any failure.
    """
    args = _parse_args()

    logger.info("=== ACRAS LLM-as-a-Judge Evaluation Suite ===")
    logger.info(f"  Dry Run: {args.dry_run}")
    logger.info(f"  Sample Filter: {args.sample_ids or 'ALL'}")

    # Load and optionally filter the golden dataset
    all_samples = load_golden_dataset()
    if args.sample_ids:
        samples = [s for s in all_samples if s.sample_id in args.sample_ids]
        if not samples:
            logger.error(f"No samples found for IDs: {args.sample_ids}")
            return 1
        logger.info(f"Filtered to {len(samples)} sample(s): {args.sample_ids}")
    else:
        samples = all_samples

    # Run the eval suite
    report = run_eval_suite(samples=samples, dry_run=args.dry_run)
    report_data = report.model_dump()

    # Save the report
    _save_report(report_data, args.output_dir)

    # Optionally log to MLflow
    if args.log_mlflow:
        _log_to_mlflow(report_data)

    # Print a summary table to stdout
    print("\n" + "=" * 60)
    print("  ACRAS Eval Suite — Summary")
    print("=" * 60)
    print(
        f"  Samples   : {report.total_samples} total | {report.passed_samples} passed | {report.failed_samples} failed"
    )
    print(f"  Pass Rate : {report.pass_rate:.1%}")
    print(f"  Relevance      (>=4): {report.mean_relevance:.2f}")
    print(f"  Faithfulness   (>=4): {report.mean_faithfulness:.2f}")
    print(f"  Tool Usage     (>=4): {report.mean_tool_usage:.2f}")
    print(f"  Business Value (>=3): {report.mean_business_value:.2f}")
    print("=" * 60)

    if report.failed_samples > 0:
        print("\n  FAILED SAMPLES:")
        for result in report.results:
            if not result.passed:
                err = result.error or "Score below threshold"
                print(f"  - {result.sample_id}: {err}")

    # Exit code: 0 = all pass, 1 = any failure
    return 0 if report.failed_samples == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
