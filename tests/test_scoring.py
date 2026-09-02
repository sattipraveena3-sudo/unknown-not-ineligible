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
    assert not score["valid_response"]
    assert score["unknown_to_denial"] is None


def test_unknown_rate_uses_only_unknown_valid_responses():
    unknown_case = make_case("u", "INSUFFICIENT_INFORMATION")
    known_case = make_case("k", "ELIGIBLE")
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

    rows = [score_item(unknown_case, denial), score_item(known_case, eligible)]
    for row in rows:
        row.update(model="m", protocol="three_way")
    summary = summarize(pd.DataFrame(rows))

    assert len(summary) == 1
    assert summary.iloc[0]["n_unknown_cases"] == 1
    assert summary.iloc[0]["n_valid_unknown_responses"] == 1
    assert summary.iloc[0]["unknown_to_denial_rate"] == 1.0
