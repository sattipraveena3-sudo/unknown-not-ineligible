from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import httpx
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential

from .prompts import build_prompt
from .schema import AgentAnswer, BenchmarkCase


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1].rsplit("```", 1)[0]
        if stripped.lstrip().startswith("json"):
            stripped = stripped.lstrip()[4:].lstrip()
    return json.loads(stripped)


@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=20), reraise=True)
def call_openai_compatible(
    provider: dict, model: str, messages: list[dict], config: dict
) -> tuple[str, dict]:
    key = os.getenv(provider["api_key_env"])
    if not key:
        raise RuntimeError(f"Missing environment variable {provider['api_key_env']}")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": config.get("temperature", 0),
        "max_tokens": config.get("max_tokens", 500),
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    # OpenRouter can surface the upstream routing decision. Recording it makes
    # provider-level replication/auditing possible without exposing the API key.
    if "openrouter.ai" in provider["base_url"]:
        headers["X-OpenRouter-Metadata"] = "enabled"

    with httpx.Client(timeout=config.get("timeout_seconds", 90)) as client:
        response = client.post(
            provider["base_url"].rstrip("/") + "/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
    return body["choices"][0]["message"]["content"], body


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

    with args.output.open("a", encoding="utf-8") as out:
        for provider_name, provider in config["providers"].items():
            for model in provider["models"]:
                for local_index, case in enumerate(cases):
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
                    except Exception as exc:  # retries are exhausted before reaching here
                        row["error_type"] = "api_error"
                        row["error_message"] = f"{type(exc).__name__}: {exc}"[:2000]
                        counts["api_error"] += 1

                    row["latency_seconds"] = round(time.time() - started, 4)
                    out.write(json.dumps(row) + "\n")
                    out.flush()

    print(
        json.dumps(
            {
                "selected_cases": len(cases),
                "offset": args.offset,
                "limit": args.limit,
                "counts": counts,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
