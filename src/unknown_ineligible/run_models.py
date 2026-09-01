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
def call_openai_compatible(provider: dict, model: str, messages: list[dict], config: dict) -> tuple[str, dict]:
    key = os.getenv(provider["api_key_env"])
    if not key:
        raise RuntimeError(f"Missing environment variable {provider['api_key_env']}")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": config.get("temperature", 0),
        "max_tokens": config.get("max_tokens", 500),
    }
    with httpx.Client(timeout=config.get("timeout_seconds", 90)) as client:
        response = client.post(
            provider["base_url"].rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
    return body["choices"][0]["message"]["content"], body.get("usage", {})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=Path("data/processed/benchmark.jsonl"), type=Path)
    parser.add_argument("--models", default=Path("configs/models.local.yaml"), type=Path)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default=Path("results/raw/responses.jsonl"), type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.models.read_text(encoding="utf-8"))
    cases = [BenchmarkCase.model_validate_json(x) for x in args.cases.read_text().splitlines() if x]
    if args.limit:
        cases = cases[: args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as out:
        for provider_name, provider in config["providers"].items():
            for model in provider["models"]:
                for case in cases:
                    started = time.time()
                    text, usage = call_openai_compatible(provider, model, build_prompt(case, args.protocol), config)
                    parsed = AgentAnswer.model_validate(extract_json(text))
                    row = {
                        "case_id": case.case_id,
                        "provider": provider_name,
                        "model": model,
                        "protocol": args.protocol,
                        "raw_answer": text,
                        "parsed_answer": parsed.model_dump(),
                        "usage": usage,
                        "latency_seconds": round(time.time() - started, 4),
                    }
                    out.write(json.dumps(row) + "\n")
                    out.flush()


if __name__ == "__main__":
    main()

