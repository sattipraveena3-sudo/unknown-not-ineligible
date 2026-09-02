# Validation Report — 2 September 2026

## Completed checks

- Official FY2024 data archive checksum matched.
- Official FY2024 technical-documentation checksum matched.
- Official FY2023 archive and CSV checksums matched.
- Extracted CSV checksum matched.
- Reproduced 44,891 rows and 1,177 columns.
- Reproduced STATUS totals: 27,055 correct, 10,734 overissuance, 7,102 underissuance.
- Reproduced FY2023 dimensions (43,776 × 854) and status totals (26,832; 10,131; 6,813).
- Deterministic unit tests passed in GitHub Actions on 2 September 2026.
- Static code checks passed with no findings in the local validation stage.
- Benchmark generation completed deterministically with seed 240901.
- Source household identifiers are replaced with one-way pseudonyms.
- No sensitive person-level demographic fields are presented.
- No LLM-generated or hand-invented applicant records are included.
- GitHub Actions secret wiring, official-data download, validation, benchmark build,
  model-call plumbing, failure-tolerant scoring, metadata capture, and artifact upload
  were verified in a guarded two-case smoke run (workflow run #1).
- The smoke artifact is explicitly non-publication output and is not used as evidence
  for any paper claim.

## Generated benchmark

- Base records: 150
- Total paired cases: 1,650
- Complete cases: 150
- Each unresolved presentation condition: 375
- Oracle ELIGIBLE: 918
- Oracle INSUFFICIENT_INFORMATION: 732
- Oracle INELIGIBLE: 0
- Benchmark SHA-256: `b0bcc7fa0b77e4f8ea1fa5439083dce504cb5d6cff9f4d601adb0a74aecb7079`

## Temporal-validation benchmark

- Source: FY2023 SNAP QC public-use data
- Base records: 150
- Total paired cases: 1,650
- Oracle ELIGIBLE: 930
- Oracle INSUFFICIENT_INFORMATION: 720
- SHA-256: `e784ccfbcced7c792a47bc71b2150e2a4e0b7d1abd60134b8e2bb80816291b19`

The absence of oracle-INELIGIBLE cases is expected because the public-use source is an
active-case dataset. This benchmark is suitable for testing uncertainty preservation and
unsupported adverse decisions, but not for estimating binary eligibility accuracy. A
future extension needs a legally shareable denied-application dataset or separately
validated rule-complete records; we will not fabricate such records.

## Evaluation-code corrections completed before confirmatory runs

- Model evaluation supports immutable offset/limit shards rather than repeatedly
  evaluating the same first cases.
- Malformed JSON/schema outputs are recorded as task failures instead of crashing the run.
- Exhausted API failures are recorded separately.
- Unknown-to-Denial Rate is summarized over genuine oracle-unknown cases rather than
  being diluted by answerable cases.
- Over-deferral, schema-failure, API-failure, unsupported-evidence, assumption, and
  clarification metrics are retained separately.
- OpenRouter routing metadata is requested and stored when the provider returns it.

## Not yet completed

- No confirmatory external-model result has been run.
- The preregistration is still a draft and must be frozen before confirmatory evaluation.
- Exact confirmatory model panel and run budget must be fixed before execution.
- No numerical smoke output will be copied into the manuscript.
- The results section remains intentionally blank.
- The literature review and venue-specific ACL formatting require completion before submission.
