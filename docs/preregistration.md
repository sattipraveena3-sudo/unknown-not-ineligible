# Preregistration Draft — Freeze Before Model Runs

## Confirmatory question

For an identical real audited record, does omission of a decision-critical field cause
a higher unknown-to-denial rate than explicitly labeling that field `unknown`?

## Primary hypothesis

`UDR(omitted) > UDR(explicit_unknown)` under the three-way baseline.

## Primary outcome

Unknown-to-Denial Rate (UDR): the fraction of cases whose oracle outcome is
`INSUFFICIENT_INFORMATION` but whose model outcome is `INELIGIBLE`.

## Secondary outcomes

- uncertainty-preservation rate;
- unknown-to-approval rate;
- clarification precision and recall;
- unsupported-evidence rate;
- assumption-presence rate;
- over-deferral on complete cases;
- JSON/schema failure rate, reported separately and counted as task failure.

## Data and exclusions

Use only FY2024 SNAP QC public-use records that:

1. have nonmissing benchmark fields and official test indicators;
2. have STATUS 1, 2, or 3;
3. are internally consistent with the narrow displayed eligibility rule;
4. contain no masked field that is irrelevant to the decision path (for example,
   do not mask gross income in elderly/disabled units).

No post-result case exclusions are allowed except duplicated API response IDs or a
documented provider failure that returned no model output. Retries must follow the
fixed runner policy.

## Sampling

Select 150 base records with seed `240901`, stratified by categorical status,
elderly/disabled status, and gross-income band. Each base record generates paired
conditions for its applicable masked fields.

## Conditions

`complete`, `omitted`, `blank`, `explicit_unknown`, and `unverified`.

## Protocols

Binary forced choice, three-way choice, uncertainty instruction, and the proposed
evidence-gated protocol.

## Statistical plan

1. Calculate model-specific and pooled UDR with paired bootstrap 95% intervals by
   resampling base-case IDs, not individual variants.
2. Test omitted versus explicit-unknown paired outcomes using McNemar's test.
3. Fit a mixed-effects logistic model if software and convergence permit, with fixed
   effects for condition, protocol, masked field, and model, and a random intercept for
   base record.
4. Use Holm correction across prespecified secondary pairwise comparisons.
5. Report odds ratios and confidence intervals, not only p-values.

## Freeze checklist

- [ ] Exact model IDs and provider versions recorded
- [ ] Number of runs and stability subset fixed
- [ ] Full benchmark SHA-256 recorded
- [ ] Analysis commit hash recorded
- [ ] Preregistration timestamped publicly
- [ ] No comparative model outputs inspected before freeze

Current locally validated benchmark SHA-256 (regenerate only before freezing):
`b0bcc7fa0b77e4f8ea1fa5439083dce504cb5d6cff9f4d601adb0a74aecb7079`.

