from unknown_ineligible.oracle import decide


def complete_record():
    return {
        "categorical_eligibility": 0,
        "elderly_or_disabled_member": 0,
        "gross_monthly_income": 1000,
        "gross_income_limit": 1600,
        "net_monthly_income": 700,
        "net_income_limit": 1200,
        "countable_assets": 100,
        "asset_limit": 2750,
    }


def test_complete_eligible():
    assert decide(complete_record()).decision == "ELIGIBLE"


def test_unknown_is_not_ineligible():
    record = complete_record()
    record["gross_monthly_income"] = "unknown"
    result = decide(record)
    assert result.decision == "INSUFFICIENT_INFORMATION"
    assert result.missing_fields == ["gross_monthly_income"]


def test_missing_gross_not_required_for_elderly_or_disabled():
    record = complete_record()
    record["elderly_or_disabled_member"] = 1
    record.pop("gross_monthly_income")
    assert decide(record).decision == "ELIGIBLE"


def test_categorical_eligibility_short_circuits_tests():
    assert decide({"categorical_eligibility": 1}).decision == "ELIGIBLE"


def test_known_failure_is_ineligible():
    record = complete_record()
    record["net_monthly_income"] = 1300
    assert decide(record).decision == "INELIGIBLE"

