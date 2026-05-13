"""
Pydantic schemas for the LLM-as-a-Judge evaluation harness.

These schemas enforce structured output at every boundary of the eval
pipeline — from the golden dataset contract to the judge's verdict.
All models use ``extra="forbid"`` to surface any unexpected fields
immediately rather than silently discarding them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Golden Dataset Schemas
# ---------------------------------------------------------------------------


class GoldenSample(BaseModel):
    """A single (input, expected_output) pair in the golden dataset.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., ``"GD-001"``).
        company_id: Numeric identifier of the company in the ACRAS database.
        scenario_description: Human-readable description of what this scenario tests.
        input_query: The exact string that will be sent to the ACRAS agent.
        expected_keywords: Phrases that MUST appear in a correct report.
        expected_recommendation: The deterministically correct final directive.
        expected_risk_tier: The deterministic risk classification for this company.
        ground_truth_ratios: Key financial ratios used for faithfulness checking.
    """

    model_config = {"extra": "forbid"}

    sample_id: str = Field(..., description="Unique sample identifier (e.g., GD-001)")
    company_id: int = Field(..., description="Company ID in the ACRAS val.csv database")
    scenario_description: str = Field(
        ..., description="What business scenario this tests"
    )
    input_query: str = Field(..., description="The exact query sent to the ACRAS agent")
    expected_keywords: list[str] = Field(
        ...,
        min_length=3,
        description="Keywords that must appear in the report for relevance scoring",
    )
    expected_recommendation: Literal["APPROVE", "REJECT", "REVIEW"] = Field(
        ..., description="The deterministically correct final directive"
    )
    expected_risk_tier: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Expected risk classification"
    )
    ground_truth_ratios: dict[str, float] = Field(
        ..., description="Key financial ratios for faithfulness validation"
    )


# ---------------------------------------------------------------------------
# Judge Output Schemas
# ---------------------------------------------------------------------------


class DimensionScore(BaseModel):
    """Score for a single evaluation dimension.

    Attributes:
        score: Integer score on a 1–5 Likert scale.
        justification: One-sentence rationale for the score.
        pass_threshold: The minimum acceptable score for this dimension.
    """

    model_config = {"extra": "forbid"}

    score: int = Field(..., ge=1, le=5, description="Score from 1 (worst) to 5 (best)")
    justification: str = Field(..., description="One-sentence rationale for the score")
    pass_threshold: int = Field(
        ..., description="Minimum acceptable score (per Rule 4.1.4)"
    )


class JudgeVerdict(BaseModel):
    """Structured output produced by the LLM Judge for a single sample.

    Mirrors the four axes mandated by Rule 4.1.4:
    - Relevance        ≥ 4/5
    - Faithfulness     ≥ 4/5
    - Tool Usage       ≥ 4/5
    - Business Value   ≥ 3/5

    Attributes:
        relevance: Does the response address the user's intent?
        faithfulness: Are claims grounded in retrieved context (no hallucination)?
        tool_usage: Did the agent select the correct tool(s) for the task?
        business_value: Does the response move a meaningful business KPI?
        overall_summary: One-paragraph synthesis of the evaluation.
    """

    model_config = {"extra": "forbid"}

    relevance: DimensionScore
    faithfulness: DimensionScore
    tool_usage: DimensionScore
    business_value: DimensionScore
    overall_summary: str = Field(..., description="Judge's overall synthesis paragraph")


class EvalResult(BaseModel):
    """The complete evaluation result for one golden-dataset sample.

    Attributes:
        sample_id: Reference to the evaluated ``GoldenSample``.
        company_id: Company evaluated in this run.
        agent_response: Raw text returned by the ACRAS agent.
        judge_verdict: Structured scoring produced by the LLM Judge.
        passed: True when ALL dimension scores meet their thresholds.
        eval_timestamp: ISO-8601 timestamp of when the eval was executed.
        error: If the agent or judge raised an exception, the message is stored here.
    """

    model_config = {"extra": "forbid"}

    sample_id: str
    company_id: int
    agent_response: str
    judge_verdict: JudgeVerdict | None = None
    passed: bool = False
    eval_timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None


class EvalSuiteReport(BaseModel):
    """Aggregated results for a full evaluation suite run.

    Attributes:
        suite_version: Semantic version of the golden dataset used.
        run_timestamp: When the suite started.
        total_samples: Total number of evaluated samples.
        passed_samples: Samples where all dimension thresholds were met.
        failed_samples: Samples where at least one threshold was missed.
        pass_rate: Fraction of samples that passed (0.0–1.0).
        mean_relevance: Average relevance score across all samples.
        mean_faithfulness: Average faithfulness score across all samples.
        mean_tool_usage: Average tool_usage score across all samples.
        mean_business_value: Average business_value score across all samples.
        results: Full per-sample results for drill-down analysis.
    """

    model_config = {"extra": "forbid"}

    suite_version: str
    run_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_samples: int
    passed_samples: int
    failed_samples: int
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    mean_relevance: float
    mean_faithfulness: float
    mean_tool_usage: float
    mean_business_value: float
    results: list[EvalResult]
