# Validation Report — 1 September 2026

## Completed checks

- Official FY2024 data archive checksum matched.
- Official FY2024 technical-documentation checksum matched.
- Official FY2023 archive and CSV checksums matched.
- Extracted CSV checksum matched.
- Reproduced 44,891 rows and 1,177 columns.
- Reproduced STATUS totals: 27,055 correct, 10,734 overissuance, 7,102 underissuance.
- Reproduced FY2023 dimensions (43,776 × 854) and status totals (26,832; 10,131; 6,813).
- Eight unit tests passed.
- Static code checks passed with no findings.
- Benchmark generation completed deterministically with seed 240901.
- Source household identifiers are replaced with one-way pseudonyms.
- No sensitive person-level demographic fields are presented.
- No LLM-generated or hand-invented applicant records are included.

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

## Not yet completed

- No external model run was performed because no API key is configured.
- No numerical model result exists.
- The results section remains intentionally blank.
- The literature review and venue-specific ACL formatting require completion before submission.
