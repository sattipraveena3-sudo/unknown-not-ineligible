# Ethics and Limitations

1. This is not an operational eligibility engine and must never decide a real case.
2. SNAP rules include state options, demonstrations, categorical pathways, and
   exceptions. The oracle intentionally evaluates only the tests displayed to the model.
3. The source contains active reviewed cases, so the study cannot estimate real-world
   denial prevalence or causal effects on applicants.
4. Missingness conditions are controlled presentation interventions. They do not claim
   to reproduce the natural administrative mechanism that caused a field to be absent.
5. The public-use file collapses distinct missing-data reasons; those original reasons
   cannot be recovered.
6. API models can change. Exact identifiers, dates, settings, and raw outputs must be
   preserved.
7. Model errors may differ across languages and jurisdictions. This release is English
   and US SNAP-specific.
8. Demographic fairness claims are outside the confirmatory study. Sensitive person-level
   attributes are not presented to models.
9. A false approval and false denial have different consequences. Both are reported,
   while UDR is primary because it captures unsupported adverse action.

