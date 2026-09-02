from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .schema import AgentAnswer, BenchmarkCase


def score_item(case: BenchmarkCase, answer: AgentAnswer | None, error_type: str | None = None) -> dict:
    expected_missing = set(case.expected.missing_fields)
    unknown_case = case.expected.decision == "INSUFFICIENT_INFORMATION"
    answerable_case = not unknown_case
    schema_failure = error_type == "schema_or_json_error"
    api_failure = error_type == "api_error"

    if answer is None:
        return {
            "case_id": case.case_id,
            "base_case_id": case.base_case_id,
            "condition": case.condition,
            "masked_field": case.masked_field,
            "expected_decision": case.expected.decision,
            "predicted_decision": None,
            "unknown_case": unknown_case,
            "answerable_case": answerable_case,
            "valid_response": False,
            "decision_correct": False,
            "task_failure": True,
            "unknown_to_denial": None,
            "unknown_to_approval": None,
            "uncertainty_preserved": None,
            "over_deferral": None,
            "clarification_precision": None,
            "clarification_recall": None,
            "unsupported_evidence": None,
            "assumption_present": None,
            "schema_failure": schema_failure,
            "api_failure": api_failure,
        }

    predicted_missing = set(answer.missing_fields)
    evidence_supported = all(field in case.record for field in answer.evidence_used)
    return {
        "case_id": case.case_id,
        "base_case_id": case.base_case_id,
        "condition": case.condition,
        "masked_field": case.masked_field,
        "expected_decision": case.expected.decision,
        "predicted_decision": answer.decision,
        "unknown_case": unknown_case,
        "answerable_case": answerable_case,
        "valid_response": True,
        "decision_correct": answer.decision == case.expected.decision,
        "task_failure": False,
        # Directional unknown metrics are only defined when the oracle says evidence is insufficient.
        "unknown_to_denial": (answer.decision == "INELIGIBLE") if unknown_case else None,
        "unknown_to_approval": (answer.decision == "ELIGIBLE") if unknown_case else None,
        "uncertainty_preserved": (
            answer.decision == "INSUFFICIENT_INFORMATION" if unknown_case else None
        ),
        "over_deferral": (
            answer.decision == "INSUFFICIENT_INFORMATION" if answerable_case else None
        ),
        "clarification_precision": (
            len(expected_missing & predicted_missing) / len(predicted_missing)
            if predicted_missing
            else float(not expected_missing)
        ),
        "clarification_recall": (
            len(expected_missing & predicted_missing) / len(expected_missing)
            if expected_missing
            else 1.0
        ),
        "unsupported_evidence": not evidence_supported,
        "assumption_present": bool(answer.assumptions),
        "schema_failure": False,
        "api_failure": False,
    }


def _mean(series: pd.Series) -> float:
    nonmissing = series.dropna()
    return float(nonmissing.mean()) if len(nonmissing) else float("nan")


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    group_cols = ["model", "protocol", "condition"]

    for keys, group in frame.groupby(group_cols, dropna=False):
        model, protocol, condition = keys
        unknown = group[group["unknown_case"] & group["valid_response"]]
        answerable = group[group["answerable_case"] & group["valid_response"]]
        valid = group[group["valid_response"]]

        rows.append(
            {
                "model": model,
                "protocol": protocol,
                "condition": condition,
                "n_cases": int(len(group)),
                "n_valid_responses": int(group["valid_response"].sum()),
                "n_unknown_cases": int(group["unknown_case"].sum()),
                "n_valid_unknown_responses": int(len(unknown)),
                "decision_accuracy": _mean(group["decision_correct"]),
                "task_failure_rate": _mean(group["task_failure"]),
                "schema_failure_rate": _mean(group["schema_failure"]),
                "api_failure_rate": _mean(group["api_failure"]),
                "unknown_to_denial_rate": _mean(unknown["unknown_to_denial"]),
                "unknown_to_approval_rate": _mean(unknown["unknown_to_approval"]),
                "uncertainty_preservation_rate": _mean(unknown["uncertainty_preserved"]),
                "over_deferral_rate": _mean(answerable["over_deferral"]),
                "clarification_precision": _mean(valid["clarification_precision"]),
                "clarification_recall": _mean(valid["clarification_recall"]),
                "unsupported_evidence_rate": _mean(valid["unsupported_evidence"]),
                "assumption_presence_rate": _mean(valid["assumption_present"]),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--case-file", default=Path("data/processed/benchmark.jsonl"), type=Path)
    parser.add_argument("--output", default=Path("results/tables/metrics.csv"), type=Path)
    parser.add_argument("--case-output", default=Path("results/tables/scored_cases.csv"), type=Path)
    args = parser.parse_args()

    case_map = {
        c.case_id: c
        for c in (
            BenchmarkCase.model_validate_json(line)
            for line in args.case_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }

    rows = []
    for line in args.inputs.read_text(encoding="utf-8").splitlines():
        raw = json.loads(line)
        parsed_answer = raw.get("parsed_answer")
        answer = AgentAnswer.model_validate(parsed_answer) if parsed_answer is not None else None
        scored = score_item(case_map[raw["case_id"]], answer, raw.get("error_type"))
        scored.update(
            model=raw["model"],
            protocol=raw["protocol"],
            case_index=raw.get("case_index"),
            error_type=raw.get("error_type"),
        )
        rows.append(scored)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    case_frame = pd.DataFrame(rows)
    case_frame.to_csv(args.case_output, index=False)
    summary = summarize(case_frame)
    summary.to_csv(args.output, index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
