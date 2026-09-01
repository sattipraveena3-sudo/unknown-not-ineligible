from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["ELIGIBLE", "INELIGIBLE", "INSUFFICIENT_INFORMATION"]


class ExpectedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    missing_fields: list[str] = Field(default_factory=list)
    rationale_code: str


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    base_case_id: str
    source: str
    source_year: int
    condition: str
    masked_field: str | None
    record: dict[str, int | float | str | None]
    expected: ExpectedOutcome
    provenance: dict[str, str]


class AgentAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    missing_fields: list[str] = Field(default_factory=list)
    requested_action: str
    evidence_used: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

