from unknown_ineligible.schema import AgentAnswer, BenchmarkCase, ExpectedOutcome
from unknown_ineligible.score import score_item


def test_unknown_to_denial_metric():
    case = BenchmarkCase(
        case_id="x",
        base_case_id="b",
        source="test",
        source_year=2024,
        condition="omitted",
        masked_field="income",
        record={"size": 2},
        expected=ExpectedOutcome(
            decision="INSUFFICIENT_INFORMATION",
            missing_fields=["income"],
            rationale_code="MISSING",
        ),
        provenance={},
    )
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

