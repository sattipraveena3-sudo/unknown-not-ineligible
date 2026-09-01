from unknown_ineligible.build_cases import apply_condition


def test_conditions_preserve_all_non_target_fields():
    record = {"income": 10, "size": 2}
    for condition, value in [
        ("blank", ""),
        ("explicit_unknown", "unknown"),
        ("unverified", "unverified"),
    ]:
        changed = apply_condition(record, "income", condition)
        assert changed["income"] == value
        assert changed["size"] == 2
        assert record["income"] == 10


def test_omitted_removes_only_target():
    assert apply_condition({"income": 10, "size": 2}, "income", "omitted") == {"size": 2}

