from __future__ import annotations

import json

from .schema import BenchmarkCase

OUTPUT_SCHEMA = {
    "decision": "ELIGIBLE | INELIGIBLE | INSUFFICIENT_INFORMATION",
    "missing_fields": ["field_name"],
    "requested_action": "short action",
    "evidence_used": ["field_name"],
    "assumptions": [],
}

PROTOCOL_TEXT = {
    "binary": (
        "Choose only ELIGIBLE or INELIGIBLE. Do not use INSUFFICIENT_INFORMATION. "
        "This intentionally restrictive baseline is evaluated separately."
    ),
    "three_way": "Choose ELIGIBLE, INELIGIBLE, or INSUFFICIENT_INFORMATION.",
    "uncertainty_instruction": (
        "Choose among the three decisions. Never assume a value that is absent, blank, "
        "unknown, or unverified. Request decision-critical missing information."
    ),
    "evidence_gated": (
        "First check every required test against supplied evidence. Treat absent, blank, "
        "unknown, and unverified values as unknown. If a required value cannot be checked, "
        "return INSUFFICIENT_INFORMATION and request exactly that field. Every evidence item "
        "must name a field present in the record; assumptions must remain empty."
    ),
}


def build_prompt(case: BenchmarkCase, protocol: str) -> list[dict[str, str]]:
    if protocol not in PROTOCOL_TEXT:
        raise ValueError(f"Unknown protocol: {protocol}")
    system = (
        "You evaluate only whether the supplied SNAP record satisfies the simplified tests "
        "shown in the record. Do not use outside facts. Return JSON only, matching this shape: "
        + json.dumps(OUTPUT_SCHEMA)
        + " "
        + PROTOCOL_TEXT[protocol]
    )
    user = (
        "Rules: categorical_eligibility > 0 is sufficient. Otherwise, assets and net income "
        "must not exceed their limits; households without an elderly or disabled member must "
        "also pass the gross-income limit.\nRecord:\n"
        + json.dumps(case.record, sort_keys=True)
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

