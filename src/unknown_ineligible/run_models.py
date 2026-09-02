from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import httpx
import yaml

from .prompts import build_prompt
from .schema import AgentAnswer, BenchmarkCase


class ProviderCallError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1].rsplit("```", 1)[0]
        if stripped.lstrip().startswith("json"):
            stripped = stripped.lstrip()[4:].lstrip()
    return json.loads(stripped)


def structured_answer_schema() -> dict:
    schema = AgentAnswer.model_json_schema()
    # AgentAnswer provides local defaults for convenience, but a remote model response
    # must explicitly serialize every scored field so missing keys cannot be confused
    # with intentionally empty lists.
    schema["required"] = list(schema["properties"])
    schema["additionalProperties"] = False
    return schema


def build_payload(model: str, messages: list[dict], config: dict) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": config.get("temperature", 0),
        "max_tokens": config.get("max_tokens", 500),
    }

    # For models selected specifically because they support structured outputs,
    # enforce the exact scoring schema at the API layer. This changes only the
    # serialization contract, not the eligibility rules or evidence available.
    if config.get("structured_output", False):
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "agent_answer",
                "strict": True,
                "schema": structured_answer_schema(),
            },
        }
        # OpenRouter should not silently route to an endpoint that drops the
        # required response-format parameter.
        payload["provider"] = {"require_parameters": True}

    if config.get("reasoning") is not None:
        payload["reasoning"] = config["reasoning"]

    return payload


def _call_once(
    provider: dict, model: str, messages: list[dict], config: dict
) -> tuple[str, dict]:
    key = os.getenv(provider["api_key_env"])
    if not key:
        raise RuntimeError(f"Missing environment variable {provider['api_key_env']}")

    payload = build_payload(model, messages, config)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=config.get("timeout_seconds", 90)) as client:
        response = client.post(
            provider["base_url"].rstrip("/") + "/chat/completions",
            headers=headers,
            json=payload,
        )
        if response.is_error:
            # Preserve enough provider detail to diagnose failures without exposing keys.
            body = response.text.replace("\n", " ")[:1500]
            raise ProviderCallError(
                f"HTTP {response.status_code}: {body}", status_code=response.status_code
            )
        body = response.json()

    return body["choices"][0]["message"]["content"], body


def call_openai_compatible(
    provider: dict, model: str, messages: list[dict], config: dict
) -> tuple[str, dict]:
    """Retry only genuinely transient transport/5xx failures.

    Deliberately do not retry HTTP 429 or ordinary 4xx responses. Free-tier 429s can
    represent daily/account limits; blind retries consume scarce quota and do not add
    scientific value.
    """

    attempts = int(config.get("max_attempts", 4))
    for attempt in range(1, attempts + 1):
        try:
            return _call_once(provider, model, messages, config)
        except ProviderCallError as exc:
            retryable = exc.status_code in {408, 425} or (
                exc.status_code is not None and 500 <= exc.status_code < 600
            )
            if not retryable or attempt >= attempts:
                raise
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt >= attempts:
                raise

        time.sleep(min(20, 2 ** (attempt - 1)))

    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=Path("data/processed/benchmark.jsonl"), type=Path)
    parser.add_argument("--models", default=Path("configs/models.local.yaml"), type=Path)
    parser.add_argument("--protocol", required=True)
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Zero-based starting case index. Use with --limit for immutable shards.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default=Path("results/raw/responses.jsonl"), type=Path)
    args = parser.parse_args()

    if args.offset < 0:
        raise ValueError("--offset must be >= 0")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be > 0 when supplied")

    config = yaml.safe_load(args.models.read_text(encoding="utf-8"))
    all_cases = [
        BenchmarkCase.model_validate_json(x)
        for x in args.cases.read_text(encoding="utf-8").splitlines()
        if x
    ]
    end = None if args.limit is None else args.offset + args.limit
    cases = all_cases[args.offset:end]
    if not cases:
        raise ValueError(
            f"No cases selected: offset={args.offset}, limit={args.limit}, total={len(all_cases)}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts = {"ok": 0, "schema_or_json_error": 0, "api_error": 0}
    attempted_cases = 0
    stopped_early = False

    with args.output.open("a", encoding="utf-8") as out:
        stop_run = False
        for provider_name, provider in config["providers"].items():
            if stop_run:
                break
            for model in provider["models"]:
                if stop_run:
                    break
                for local_index, case in enumerate(cases):
                    attempted_cases += 1
                    started = time.time()
                    row = {
                        "case_id": case.case_id,
                        "case_index": args.offset + local_index,
                        "provider": provider_name,
                        "model": model,
                        "protocol": args.protocol,
                        "raw_answer": None,
                        "parsed_answer": None,
                        "usage": {},
                        "response_id": None,
                        "response_model": None,
                        "system_fingerprint": None,
                        "openrouter_metadata": None,
                        "api_status_code": None,
                        "error_type": None,
                        "error_message": None,
                    }

                    try:
                        text, body = call_openai_compatible(
                            provider, model, build_prompt(case, args.protocol), config
                        )
                        row["raw_answer"] = text
                        row["usage"] = body.get("usage", {})
                        row["response_id"] = body.get("id")
                        row["response_model"] = body.get("model")
                        row["system_fingerprint"] = body.get("system_fingerprint")
                        row["openrouter_metadata"] = body.get("openrouter_metadata")

                        try:
                            parsed = AgentAnswer.model_validate(extract_json(text))
                            row["parsed_answer"] = parsed.model_dump()
                            counts["ok"] += 1
                        except Exception as exc:  # malformed model output is an outcome, not a crash
                            row["error_type"] = "schema_or_json_error"
                            row["error_message"] = f"{type(exc).__name__}: {exc}"[:2000]
                            counts["schema_or_json_error"] += 1
                    except Exception as exc:
                        row["error_type"] = "api_error"
                        row["error_message"] = f"{type(exc).__name__}: {exc}"[:2000]
                        if isinstance(exc, ProviderCallError):
                            row["api_status_code"] = exc.status_code
                        counts["api_error"] += 1
                        # Stop the shard after the first exhausted provider failure. This avoids
                        # turning a quota/outage into hundreds of meaningless failed requests.
                        stop_run = True
                        stopped_early = True

                    row["latency_seconds"] = round(time.time() - started, 4)
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    if stop_run:
                        break

    print(
        json.dumps(
            {
                "selected_cases": len(cases),
                "attempted_cases": attempted_cases,
                "offset": args.offset,
                "limit": args.limit,
                "stopped_early": stopped_early,
                "counts": counts,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
