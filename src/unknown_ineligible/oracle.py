from __future__ import annotations

from .schema import ExpectedOutcome

REQUIRED_FIELDS = (
    "categorical_eligibility",
    "elderly_or_disabled_member",
    "gross_monthly_income",
    "gross_income_limit",
    "net_monthly_income",
    "net_income_limit",
    "countable_assets",
    "asset_limit",
)


def _unknown(record: dict, field: str) -> bool:
    return field not in record or record[field] in (None, "", "unknown", "unverified")


def decide(record: dict) -> ExpectedOutcome:
    """Apply the preregistered, deliberately narrow federal test logic.

    The oracle does not reproduce every state waiver. Records are limited upstream
    to cases for which the supplied federal screens are internally consistent.
    """
    if _unknown(record, "categorical_eligibility"):
        return ExpectedOutcome(
            decision="INSUFFICIENT_INFORMATION",
            missing_fields=["categorical_eligibility"],
            rationale_code="MISSING_CATEGORICAL_STATUS",
        )
    if int(record["categorical_eligibility"]) > 0:
        return ExpectedOutcome(decision="ELIGIBLE", rationale_code="CATEGORICALLY_ELIGIBLE")

    missing: list[str] = []
    if _unknown(record, "elderly_or_disabled_member"):
        missing.append("elderly_or_disabled_member")
    if _unknown(record, "net_monthly_income"):
        missing.append("net_monthly_income")
    if _unknown(record, "net_income_limit"):
        missing.append("net_income_limit")
    if _unknown(record, "countable_assets"):
        missing.append("countable_assets")
    if _unknown(record, "asset_limit"):
        missing.append("asset_limit")
    if not _unknown(record, "elderly_or_disabled_member") and not bool(
        record["elderly_or_disabled_member"]
    ):
        if _unknown(record, "gross_monthly_income"):
            missing.append("gross_monthly_income")
        if _unknown(record, "gross_income_limit"):
            missing.append("gross_income_limit")
    if missing:
        return ExpectedOutcome(
            decision="INSUFFICIENT_INFORMATION",
            missing_fields=sorted(set(missing)),
            rationale_code="MISSING_DECISION_CRITICAL_EVIDENCE",
        )

    if not bool(record["elderly_or_disabled_member"]) and float(
        record["gross_monthly_income"]
    ) > float(record["gross_income_limit"]):
        return ExpectedOutcome(decision="INELIGIBLE", rationale_code="FAIL_GROSS_TEST")
    if float(record["net_monthly_income"]) > float(record["net_income_limit"]):
        return ExpectedOutcome(decision="INELIGIBLE", rationale_code="FAIL_NET_TEST")
    if float(record["countable_assets"]) > float(record["asset_limit"]):
        return ExpectedOutcome(decision="INELIGIBLE", rationale_code="FAIL_ASSET_TEST")
    return ExpectedOutcome(decision="ELIGIBLE", rationale_code="PASSES_SUPPLIED_TESTS")

