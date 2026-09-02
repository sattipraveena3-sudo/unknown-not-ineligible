from unknown_ineligible.run_models import build_payload


def test_structured_output_payload_enforces_agent_schema():
    payload = build_payload(
        "liquid/lfm-2.5-2.6b:free",
        [{"role": "user", "content": "test"}],
        {
            "temperature": 0,
            "max_tokens": 500,
            "structured_output": True,
            "reasoning": {"effort": "minimal", "exclude": True},
        },
    )

    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert payload["response_format"]["json_schema"]["name"] == "agent_answer"
    assert payload["provider"] == {"require_parameters": True}
    assert payload["reasoning"] == {"effort": "minimal", "exclude": True}

    schema = payload["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "decision",
        "missing_fields",
        "requested_action",
        "evidence_used",
        "assumptions",
    }
    assert set(schema["properties"]["decision"]["enum"]) == {
        "ELIGIBLE",
        "INELIGIBLE",
        "INSUFFICIENT_INFORMATION",
    }


def test_plain_payload_does_not_request_structured_output():
    payload = build_payload(
        "example/model",
        [{"role": "user", "content": "test"}],
        {"temperature": 0, "max_tokens": 100},
    )

    assert "response_format" not in payload
    assert "provider" not in payload
    assert "reasoning" not in payload
