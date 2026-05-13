"""
Unit tests for the LLM-as-a-Judge evaluation harness.

These tests verify the deterministic components of the eval pipeline:
- Golden dataset loading and schema validation.
- Threshold gate logic (pass/fail decisioning).
- Judge response parser robustness.
- Dry-run mode for end-to-end pipeline wiring.
- Suite report aggregation correctness.

All LLM calls are mocked; these tests carry the ``unit`` marker and run
with zero API cost. Use the ``eval`` marker for full integration runs.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.evals.judge_harness import (
    GOLDEN_DATASET_PATH,
    _check_thresholds,
    _parse_judge_response,
    evaluate_sample,
    load_golden_dataset,
    run_eval_suite,
)
from src.evals.schemas import (
    DimensionScore,
    EvalSuiteReport,
    GoldenSample,
    JudgeVerdict,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_gd001() -> GoldenSample:
    """Return a minimal valid GoldenSample for unit testing."""
    return GoldenSample(
        sample_id="GD-TEST",
        company_id=1,
        scenario_description="Test scenario: healthy company.",
        input_query="Generate a credit risk assessment for company 1.",
        expected_keywords=["APPROVE", "Current Ratio", "EBITDA"],
        expected_recommendation="APPROVE",
        expected_risk_tier="LOW",
        ground_truth_ratios={"current_ratio": 1.8, "mora_ratio": 0.03},
    )


@pytest.fixture()
def passing_verdict() -> JudgeVerdict:
    """Return a JudgeVerdict where all dimensions meet their thresholds."""
    return JudgeVerdict(
        relevance=DimensionScore(score=4, justification="Relevant.", pass_threshold=4),
        faithfulness=DimensionScore(
            score=5, justification="No hallucinations.", pass_threshold=4
        ),
        tool_usage=DimensionScore(
            score=4, justification="Correct tools.", pass_threshold=4
        ),
        business_value=DimensionScore(
            score=4, justification="Actionable.", pass_threshold=3
        ),
        overall_summary="All dimensions passed.",
    )


@pytest.fixture()
def failing_verdict() -> JudgeVerdict:
    """Return a JudgeVerdict where one dimension falls below its threshold."""
    return JudgeVerdict(
        relevance=DimensionScore(score=2, justification="Off-topic.", pass_threshold=4),
        faithfulness=DimensionScore(
            score=5, justification="No hallucinations.", pass_threshold=4
        ),
        tool_usage=DimensionScore(
            score=4, justification="Correct tools.", pass_threshold=4
        ),
        business_value=DimensionScore(
            score=3, justification="Adequate.", pass_threshold=3
        ),
        overall_summary="Relevance failed.",
    )


# ---------------------------------------------------------------------------
# Golden Dataset Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_golden_dataset_file_exists() -> None:
    """Golden dataset JSON must exist at the expected path."""
    assert GOLDEN_DATASET_PATH.exists(), (
        f"Golden dataset not found: {GOLDEN_DATASET_PATH}"
    )


@pytest.mark.unit
def test_load_golden_dataset_returns_20_samples() -> None:
    """Dataset must contain exactly 20 curated samples."""
    samples = load_golden_dataset()
    assert len(samples) == 20, f"Expected 20 samples, got {len(samples)}"


@pytest.mark.unit
def test_golden_dataset_all_sample_ids_unique() -> None:
    """Every sample_id in the golden dataset must be unique."""
    samples = load_golden_dataset()
    ids = [s.sample_id for s in samples]
    assert len(ids) == len(set(ids)), "Duplicate sample_id detected in golden dataset"


@pytest.mark.unit
def test_golden_dataset_covers_all_risk_tiers() -> None:
    """Dataset must cover LOW, MEDIUM, and HIGH risk scenarios."""
    samples = load_golden_dataset()
    tiers = {s.expected_risk_tier for s in samples}
    assert "LOW" in tiers, "No LOW risk scenario in golden dataset"
    assert "MEDIUM" in tiers, "No MEDIUM risk scenario in golden dataset"
    assert "HIGH" in tiers, "No HIGH risk scenario in golden dataset"


@pytest.mark.unit
def test_golden_dataset_covers_all_recommendations() -> None:
    """Dataset must cover APPROVE, REJECT, and REVIEW recommendations."""
    samples = load_golden_dataset()
    recs = {s.expected_recommendation for s in samples}
    assert "APPROVE" in recs, "No APPROVE recommendation in dataset"
    assert "REJECT" in recs, "No REJECT recommendation in dataset"
    assert "REVIEW" in recs, "No REVIEW recommendation in dataset"


@pytest.mark.unit
def test_golden_sample_schema_rejects_invalid_recommendation(
    sample_gd001: GoldenSample,
) -> None:
    """GoldenSample must reject invalid recommendation values."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        GoldenSample(
            **{
                **sample_gd001.model_dump(),
                "expected_recommendation": "MAYBE",  # Invalid literal
            }
        )


# ---------------------------------------------------------------------------
# Threshold Gate Tests (Deterministic Brawn)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_check_thresholds_all_pass(passing_verdict: JudgeVerdict) -> None:
    """_check_thresholds must return True when all dimensions meet thresholds."""
    assert _check_thresholds(passing_verdict) is True


@pytest.mark.unit
def test_check_thresholds_fails_on_low_relevance(failing_verdict: JudgeVerdict) -> None:
    """_check_thresholds must return False when relevance is below 4."""
    assert _check_thresholds(failing_verdict) is False


@pytest.mark.unit
def test_check_thresholds_business_value_threshold_is_3() -> None:
    """Business Value threshold must be 3/5."""
    verdict = JudgeVerdict(
        relevance=DimensionScore(score=4, justification="ok", pass_threshold=4),
        faithfulness=DimensionScore(score=4, justification="ok", pass_threshold=4),
        tool_usage=DimensionScore(score=4, justification="ok", pass_threshold=4),
        business_value=DimensionScore(score=3, justification="ok", pass_threshold=3),
        overall_summary="Border case.",
    )
    assert _check_thresholds(verdict) is True, "Score of 3/3 should pass business_value"


@pytest.mark.unit
def test_check_thresholds_fails_on_low_business_value() -> None:
    """_check_thresholds must fail when business_value is 2 (below threshold of 3)."""
    verdict = JudgeVerdict(
        relevance=DimensionScore(score=4, justification="ok", pass_threshold=4),
        faithfulness=DimensionScore(score=4, justification="ok", pass_threshold=4),
        tool_usage=DimensionScore(score=4, justification="ok", pass_threshold=4),
        business_value=DimensionScore(
            score=2, justification="Not actionable.", pass_threshold=3
        ),
        overall_summary="Business value failed.",
    )
    assert _check_thresholds(verdict) is False


# ---------------------------------------------------------------------------
# JSON Parser Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_judge_response_valid_json(passing_verdict: JudgeVerdict) -> None:
    """Parser must produce a valid JudgeVerdict from clean JSON."""
    import json

    raw = json.dumps(passing_verdict.model_dump())
    result = _parse_judge_response(raw)
    assert result.relevance.score == 4
    assert result.faithfulness.score == 5


@pytest.mark.unit
def test_parse_judge_response_strips_markdown_fences(
    passing_verdict: JudgeVerdict,
) -> None:
    """Parser must strip ```json ... ``` fences that some models add."""
    import json

    raw = f"```json\n{json.dumps(passing_verdict.model_dump())}\n```"
    result = _parse_judge_response(raw)
    assert result.overall_summary == "All dimensions passed."


@pytest.mark.unit
def test_parse_judge_response_raises_on_invalid_json() -> None:
    """Parser must raise ValueError on malformed JSON."""
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_judge_response("this is not json at all")


@pytest.mark.unit
def test_parse_judge_response_injects_pass_threshold() -> None:
    """Parser must inject pass_threshold when LLM omits it from the response."""
    import json

    # Omit pass_threshold from all dimensions
    raw = json.dumps(
        {
            "relevance": {"score": 4, "justification": "ok"},
            "faithfulness": {"score": 4, "justification": "ok"},
            "tool_usage": {"score": 4, "justification": "ok"},
            "business_value": {"score": 3, "justification": "ok"},
            "overall_summary": "Test.",
        }
    )
    result = _parse_judge_response(raw)
    assert result.relevance.pass_threshold == 4
    assert result.business_value.pass_threshold == 3


# ---------------------------------------------------------------------------
# Dry-Run End-to-End Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_evaluate_sample_dry_run_passes(sample_gd001: GoldenSample) -> None:
    """evaluate_sample in dry_run mode must return a passing EvalResult."""
    result = evaluate_sample(sample_gd001, dry_run=True)
    assert result.passed is True
    assert result.error is None
    assert result.judge_verdict is not None
    assert result.sample_id == "GD-TEST"


@pytest.mark.unit
def test_evaluate_sample_dry_run_no_api_calls(sample_gd001: GoldenSample) -> None:
    """Dry run must not trigger any external API or model calls."""
    with (
        patch("src.evals.judge_harness._invoke_acras_agent") as mock_agent,
        patch("src.evals.judge_harness._invoke_judge") as mock_judge,
    ):
        evaluate_sample(sample_gd001, dry_run=True)
        mock_agent.assert_not_called()
        mock_judge.assert_not_called()


@pytest.mark.unit
def test_run_eval_suite_dry_run_returns_report() -> None:
    """run_eval_suite in dry_run must return an EvalSuiteReport for all 20 samples."""
    samples = load_golden_dataset()
    report = run_eval_suite(samples=samples, dry_run=True)
    assert isinstance(report, EvalSuiteReport)
    assert report.total_samples == 20
    assert report.passed_samples == 20
    assert report.failed_samples == 0
    assert report.pass_rate == 1.0


@pytest.mark.unit
def test_run_eval_suite_dry_run_subset() -> None:
    """run_eval_suite in dry_run must work correctly with a 3-sample subset."""
    samples = load_golden_dataset()[:3]
    report = run_eval_suite(samples=samples, dry_run=True)
    assert report.total_samples == 3
    assert report.pass_rate == 1.0


# ---------------------------------------------------------------------------
# Agent Error Handling Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_evaluate_sample_handles_agent_error(sample_gd001: GoldenSample) -> None:
    """evaluate_sample must return a failed EvalResult when the agent raises."""
    with patch(
        "src.evals.judge_harness._invoke_acras_agent",
        side_effect=RuntimeError("Agent unavailable"),
    ):
        result = evaluate_sample(sample_gd001, dry_run=False)
    assert result.passed is False
    assert result.error is not None
    assert "Agent error" in result.error


@pytest.mark.unit
def test_evaluate_sample_handles_judge_error(
    sample_gd001: GoldenSample,
) -> None:
    """evaluate_sample must return a failed EvalResult when the judge raises."""
    with (
        patch(
            "src.evals.judge_harness._invoke_acras_agent",
            return_value="Mocked credit report content.",
        ),
        patch(
            "src.evals.judge_harness._invoke_judge",
            side_effect=RuntimeError("Judge unavailable"),
        ),
    ):
        result = evaluate_sample(sample_gd001, dry_run=False)
    assert result.passed is False
    assert "Judge error" in (result.error or "")


# ---------------------------------------------------------------------------
# Schema Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_dimension_score_rejects_out_of_range() -> None:
    """DimensionScore must reject scores outside [1, 5]."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        DimensionScore(score=6, justification="Too high.", pass_threshold=4)

    with pytest.raises(pydantic.ValidationError):
        DimensionScore(score=0, justification="Too low.", pass_threshold=4)


@pytest.mark.unit
def test_eval_suite_report_pass_rate_computed_correctly() -> None:
    """EvalSuiteReport pass_rate field must be within [0.0, 1.0]."""
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        EvalSuiteReport(
            suite_version="1.0.0",
            total_samples=10,
            passed_samples=10,
            failed_samples=0,
            pass_rate=1.5,  # Invalid — above 1.0
            mean_relevance=4.0,
            mean_faithfulness=4.0,
            mean_tool_usage=4.0,
            mean_business_value=3.0,
            results=[],
        )
