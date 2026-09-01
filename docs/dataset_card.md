# Dataset Card

## Source

USDA Food and Nutrition Service, Supplemental Nutrition Assistance Program Quality
Control public-use database, fiscal year 2024, August 2026 corrected release.

## Verified local release

- Archive SHA-256: `b8b29b8593f78aa51c48332c47d2d92fa5bbecf5346570acb45e26f2d9ebd2b5`
- CSV SHA-256: `e871a8e9caca0be72e2003b09bdf71e1d020984b52289d2b74c4c6b88c4f793b`
- Documentation SHA-256: `d222c7ae7762df5cd4935a9f0dbb303852728282ecac21debe08a94ef8acbb06`
- Observations: 44,891
- Variables: 1,177
- Sample months: October 2023 through September 2024

## Reproduced status counts

| STATUS | Documentation meaning | Rows |
|---:|---|---:|
| 1 | Amount correct | 27,055 |
| 2 | Overissuance | 10,734 |
| 3 | Underissuance | 7,102 |

The public-use file converts every restricted-use missing reason to a single missing
value. It cannot support claims comparing naturally occurring kinds of missingness.

## Benchmark variables

| Presented name | Source variable | Meaning |
|---|---|---|
| `household_size` | FSUSIZE | Constructed certified unit size |
| `categorical_eligibility` | CAT_ELIG | Categorical-eligibility indicator |
| `gross_monthly_income` | FSGRINC | Final gross countable unit income |
| `gross_income_limit` | GROSSCRN | Applicable gross-income screen |
| `net_monthly_income` | FSNETINC | Final net countable unit income |
| `net_income_limit` | NETSCRN | Applicable net-income screen |
| `countable_assets` | FSASSET | Countable assets under state rules |
| `asset_limit` | ASSLIM | Applicable asset limit |
| `elderly_or_disabled_member` | FSELDER/FSDIS | Whether either unit indicator is positive |

Official pass/fail variables are used only to filter internally consistent records.
They are not shown to models because they would reveal the answer.

## Privacy

The public-use file is already prepared for public analysis. The benchmark does not
emit `HHLDNO`; it creates a deterministic truncated SHA-256 identifier salted with the
source year. Person-level race, sex, citizenship, and individual income fields are not
presented to models.

