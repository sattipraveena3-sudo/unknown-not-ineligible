# Unknown Is Not Ineligible

Reproducible research code for evaluating whether language-model agents preserve
uncertainty when decision-critical evidence is missing from public-benefit records.

## Status

| Component | Status |
|---|---|
| Official SNAP QC FY2024 primary data | Downloaded and checksum-verified |
| Official SNAP QC FY2023 temporal-validation data | Downloaded and checksum-verified |
| Dataset validation | Implemented |
| Real-record paired benchmark builder | Implemented |
| Deterministic oracle and scorer | Implemented |
| OpenAI-compatible model runner | Implemented; requires user API key/model selection |
| Statistical results | Not yet available; no results are fabricated |
| ACL manuscript | Protocol skeleton only; results must be run first |

## Research question

When a required value is absent, blank, explicitly unknown, or unverified, does an
LLM request the missing evidence or convert uncertainty into an unsupported adverse
decision?

## Data

The project uses the August 2026 public-use release of the **FY2024 USDA SNAP
Quality Control database**: 44,891 audited active cases and 1,177 variables. The
download script verifies exact SHA-256 hashes. No applicant records, incomes, or
labels are invented.

The controlled cases are paired transformations of real audited records. One genuine
field is hidden or marked unresolved; all other presented values remain unchanged.
This is an experimental intervention on real records, not synthetic applicant generation.

Important scope: public-use FY2024 data contain active cases (`STATUS` 1–3), not a
representative sample of denied applications. The benchmark therefore evaluates
**evidence sufficiency and unsupported adverse decisions**, not observed denial rates.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
make download
make validate
make test
make build
```

The primary benchmark is written to `data/processed/benchmark.jsonl`, and the FY2023
temporal-validation benchmark to `data/processed/benchmark_2023.jsonl`. Source household
identifiers are never emitted; deterministic SHA-256 pseudonyms are used instead.

## Run a small API smoke check

Do this only after all tests pass. It is a plumbing check, not a reported pilot result.

```bash
cp configs/models.example.yaml configs/models.local.yaml
# Edit the exact model ID, then set the key in your shell.
export OPENROUTER_API_KEY='your-key'
python -m unknown_ineligible.run_models \
  --protocol evidence_gated --limit 2 \
  --output results/raw/smoke.jsonl
```

Do not merge smoke outputs into the preregistered experiment. Delete or archive them
before the full run.

## Full experiment

Run each protocol into a separate immutable output and record the exact model version,
provider, date, temperature, and API metadata. Detailed steps are in
`docs/USER_ACTIONS.md` and the frozen design is in `docs/preregistration.md`.

## Ethical boundary

This repository is a research evaluation. It must not be used to make real eligibility
decisions. SNAP policy includes state options and exceptions that the narrow oracle does
not reproduce. See `docs/ethics_and_limitations.md`.

## Official sources

- Data portal: https://snapqcdata.net/datafiles
- FY2024 technical documentation: included by the verified downloader
- SNAP QC regulation: https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-C/part-275/subpart-C
