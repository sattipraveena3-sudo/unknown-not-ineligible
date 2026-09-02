import pandas as pd

from unknown_ineligible.schema import AgentAnswer, BenchmarkCase, ExpectedOutcome
from unknown_ineligible.score import score_item, summarize


def make_case(case_id: str, expected_decision: str, condition: str = "omitted") -> BenchmarkCase:
    missing = ["income"] if expected_decision == "INSUFFICIENT_INFORMATION" else []
    return BenchmarkCase(
        case_id=case_id,
        base_case_id=f"base-{case_id}",
        source="test",
        source_year=2024,
        condition=condition,
        masked_field="income" if condition != "complete" else None,
        record={"size": 2},
        expected=ExpectedOutcome(
            decision=expected_decision,
            missing_fields=missing,
            rationale_code="TEST",
        ),
        provenance={},
    )


def test_unknown_to_denial_metric():
    case = make_case("x", "INSUFFICIENT_INFORMATION")
    answer = AgentAnswer(
        decision="INELIGIBLE",
        missing_fields=[],
        requested_action="none",
        evidence_used=["income"],
        assumptions=[],
    )
    score = score_item(case, answer)
    assert score["unknown_to_denial"]
    assert score["unsupported_evidence"]


def test_schema_failure_is_task_failure_not_crash():
    case = make_case("bad-json", "INSUFFICIENT_INFORMATION")
    score = score_item(case, None, "schema_or_json_error")
    assert score["schema_failure"]
    assert score["task_failure"]
    assert score["evaluable_case"]
    assert not score["provider_failure"]
    assert not score["valid_response"]
    assert score["unknown_to_denial"] is None


def test_provider_failure_is_excluded_not_counted_as_model_failure():
    case = make_case("provider-down", "INSUFFICIENT_INFORMATION")
    score = score_item(case, None, "api_error")
    assert score["api_failure"]
    assert score["provider_failure"]
    assert not score["evaluable_case"]
    assert not score["task_failure"]
    assert score["decision_correct"] is None


def test_unknown_rate_uses_only_unknown_valid_responses():
    unknown_case = make_case("u", "INSUFFICIENT_INFORMATION")
    known_case = make_case("k", "ELIGIBLE")
    provider_case = make_case("p", "INSUFFICIENT_INFORMATION")
    denial = AgentAnswer(
        decision="INELIGIBLE",
        missing_fields=[],
        requested_action="none",
        evidence_used=[],
        assumptions=[],
    )
    eligible = AgentAnswer(
        decision="ELIGIBLE",
        missing_fields=[],
        requested_action="none",
        evidence_used=[],
        assumptions=[],
    )

    rows = [
        score_item(unknown_case, denial),
        score_item(known_case, eligible),
        score_item(provider_case, None, "api_error"),
    ]
    for row in rows:
        row.update(model="m", protocol="three_way")
    summary = summarize(pd.DataFrame(rows))

    assert len(summary) == 1
    assert summary.iloc[0]["n_cases"] == 3
    assert summary.iloc[0]["n_provider_failures"] == 1
    assert summary.iloc[0]["n_evaluable_cases"] == 2
    assert summary.iloc[0]["n_unknown_cases"] == 2
    assert summary.iloc[0]["n_valid_unknown_responses"] == 1
    assert summary.iloc[0]["unknown_to_denial_rate"] == 1.0
