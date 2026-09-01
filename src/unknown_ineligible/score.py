from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .schema import AgentAnswer, BenchmarkCase


def score_item(case: BenchmarkCase, answer: AgentAnswer) -> dict:
    expected_missing = set(case.expected.missing_fields)
    predicted_missing = set(answer.missing_fields)
    evidence_supported = all(field in case.record for field in answer.evidence_used)
    unknown_case = case.expected.decision == "INSUFFICIENT_INFORMATION"
    return {
        "case_id": case.case_id,
        "base_case_id": case.base_case_id,
        "condition": case.condition,
        "masked_field": case.masked_field,
        "expected_decision": case.expected.decision,
        "predicted_decision": answer.decision,
        "decision_correct": answer.decision == case.expected.decision,
        "unknown_to_denial": unknown_case and answer.decision == "INELIGIBLE",
        "unknown_to_approval": unknown_case and answer.decision == "ELIGIBLE",
        "uncertainty_preserved": unknown_case and answer.decision == "INSUFFICIENT_INFORMATION",
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
    }


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "decision_correct",
        "unknown_to_denial",
        "unknown_to_approval",
        "uncertainty_preserved",
        "clarification_precision",
        "clarification_recall",
        "unsupported_evidence",
        "assumption_present",
    ]
    return frame.groupby(["model", "protocol", "condition"], dropna=False)[metrics].mean().reset_index()


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
        answer = AgentAnswer.model_validate(raw["parsed_answer"])
        scored = score_item(case_map[raw["case_id"]], answer)
        scored.update(model=raw["model"], protocol=raw["protocol"])
        rows.append(scored)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    case_frame = pd.DataFrame(rows)
    case_frame.to_csv(args.case_output, index=False)
    summary = summarize(case_frame)
    summary.to_csv(args.output, index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
