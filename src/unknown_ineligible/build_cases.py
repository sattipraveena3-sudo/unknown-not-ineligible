from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

from .oracle import decide
from .schema import BenchmarkCase

SOURCE_COLUMNS = {
    "STATE": "state_code",
    "FSUSIZE": "household_size",
    "CAT_ELIG": "categorical_eligibility",
    "FSELDER": "elderly_member",
    "FSDIS": "disabled_member",
    "FSGRINC": "gross_monthly_income",
    "GROSSCRN": "gross_income_limit",
    "FSNETINC": "net_monthly_income",
    "NETSCRN": "net_income_limit",
    "FSASSET": "countable_assets",
    "ASSLIM": "asset_limit",
    "FSBEN": "audited_benefit",
    "STATUS": "qc_status",
    "FSGRTEST": "source_gross_test",
    "FSNETEST": "source_net_test",
    "FSASTEST": "source_asset_test",
    "HHLDNO": "source_household_id",
}

PRESENTED_FIELDS = (
    "state_code",
    "household_size",
    "categorical_eligibility",
    "elderly_or_disabled_member",
    "gross_monthly_income",
    "gross_income_limit",
    "net_monthly_income",
    "net_income_limit",
    "countable_assets",
    "asset_limit",
)


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_and_filter(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=list(SOURCE_COLUMNS)).rename(columns=SOURCE_COLUMNS)
    numeric = [c for c in df.columns if c not in ("source_household_id",)]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    df["elderly_or_disabled_member"] = (
        (df["elderly_member"] > 0) | (df["disabled_member"] > 0)
    ).astype(int)

    needed = list(PRESENTED_FIELDS) + [
        "source_gross_test",
        "source_net_test",
        "source_asset_test",
        "source_household_id",
    ]
    df = df.dropna(subset=needed).copy()
    # Active public-use cases only; require the supplied official pass indicators
    # to agree with the narrow benchmark rule. Derived indicators are never shown.
    df = df[df["qc_status"].isin([1, 2, 3])]
    noncat = df["categorical_eligibility"] == 0
    consistent = (
        (~noncat)
        | (
            (df["source_net_test"] == 1)
            & (df["source_asset_test"] == 1)
            & ((df["elderly_or_disabled_member"] == 1) | (df["source_gross_test"] == 1))
        )
    )
    return df[consistent].reset_index(drop=True)


def stratified_sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    work = df.copy()
    work["stratum"] = (
        work["categorical_eligibility"].gt(0).astype(str)
        + "_"
        + work["elderly_or_disabled_member"].astype(str)
        + "_"
        + pd.cut(
            work["gross_monthly_income"],
            bins=[-1, 0, 1000, 2000, float("inf")],
            labels=["zero", "low", "mid", "high"],
        ).astype(str)
    )
    groups = list(work.groupby("stratum", observed=True))
    if n > len(work):
        raise ValueError(f"Requested {n} records but only {len(work)} are eligible")
    quota = max(1, n // max(1, len(groups)))
    selected = []
    for _, group in groups:
        selected.append(group.sample(n=min(quota, len(group)), random_state=seed))
    result = pd.concat(selected).drop_duplicates()
    if len(result) < n:
        remaining = work.drop(index=result.index)
        result = pd.concat(
            [result, remaining.sample(n=n - len(result), random_state=seed + 1)]
        )
    return result.sample(n=n, random_state=seed + 2).reset_index(drop=True)


def safe_id(raw_id: object, year: int) -> str:
    digest = hashlib.sha256(f"{year}:{raw_id}".encode()).hexdigest()[:16]
    return f"snapqc-{year}-{digest}"


def apply_condition(record: dict, field: str, condition: str) -> dict:
    changed = dict(record)
    if condition == "complete":
        return changed
    if condition == "omitted":
        changed.pop(field, None)
    elif condition == "blank":
        changed[field] = ""
    elif condition == "explicit_unknown":
        changed[field] = "unknown"
    elif condition == "unverified":
        changed[field] = "unverified"
    else:
        raise ValueError(f"Unknown condition: {condition}")
    return changed


def build(config: dict) -> list[BenchmarkCase]:
    source_path = Path(config["source_csv"])
    df = stratified_sample(
        load_and_filter(source_path), int(config["base_records"]), int(config["seed"])
    )
    cases: list[BenchmarkCase] = []
    provenance = {
        new: f"SNAP QC FY{config['source_year']} variable {old}"
        for old, new in SOURCE_COLUMNS.items()
        if new in PRESENTED_FIELDS
    }
    provenance["elderly_or_disabled_member"] = "Derived from FSELDER > 0 or FSDIS > 0"

    for _, row in df.iterrows():
        base_id = safe_id(row["source_household_id"], int(config["source_year"]))
        record = {field: row[field].item() if hasattr(row[field], "item") else row[field] for field in PRESENTED_FIELDS}
        cases.append(
            BenchmarkCase(
                case_id=f"{base_id}-complete",
                base_case_id=base_id,
                source="USDA SNAP Quality Control public-use database",
                source_year=int(config["source_year"]),
                condition="complete",
                masked_field=None,
                record=record,
                expected=decide(record),
                provenance=provenance,
            )
        )
        for field in config["mask_fields"]:
            # Gross income is not decision-critical for elderly/disabled units.
            if field == "gross_monthly_income" and record["elderly_or_disabled_member"] == 1:
                continue
            for condition in (c for c in config["conditions"] if c != "complete"):
                presented = apply_condition(record, field, condition)
                expected = decide(presented)
                case_id = f"{base_id}-{field}-{condition}"
                cases.append(
                    BenchmarkCase(
                        case_id=case_id,
                        base_case_id=base_id,
                        source="USDA SNAP Quality Control public-use database",
                        source_year=int(config["source_year"]),
                        condition=condition,
                        masked_field=None if condition == "complete" else field,
                        record=presented,
                        expected=expected,
                        provenance=provenance,
                    )
                )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    cases = build(config)
    output = Path(config["output_jsonl"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(case.model_dump_json() + "\n")
    print(json.dumps({"base_records": config["base_records"], "cases": len(cases), "output": str(output)}))


if __name__ == "__main__":
    main()
