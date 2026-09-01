# Related Work Matrix

This matrix records the closest work found before model execution. “Gap” claims must be
updated immediately before submission.

| Work | What it establishes | Difference from this study |
|---|---|---|
| Zhang et al., CLAMBER, ACL 2024 | Benchmarks identifying and clarifying ambiguous user questions | General ambiguity; not missing administrative evidence, benefit decisions, or false denial |
| Zhang et al., Ask-before-Plan, EMNLP Findings 2024 | Tests whether planning agents seek clarification before acting | Planning/travel tasks rather than high-stakes eligibility records |
| Dong et al., Human–Agent Communication, ACL 2026 | Formalizes acting versus interrupting under incomplete requests | Communication framework; does not isolate unknown-to-adverse-decision conversion |
| Bhar et al., COCORELI, SIGDIAL 2026 | Studies missing-information detection and targeted clarification | Collaborative execution tasks, not real audited benefit records or decision evidence |
| Geng et al., NAACL 2024 survey | Surveys confidence estimation, calibration, and selective prediction | Model confidence is different from field-level evidentiary sufficiency |
| Rystrøm et al., 2026 | Argues public-sector benchmarks should be realistic, process-based, domain-specific, and use relevant metrics | Requirements analysis rather than an executed benefit-record benchmark |
| PolicyLLM/PolicyBench, 2026 | Evaluates public-policy comprehension across systems | Policy knowledge, not missing applicant evidence or procedural deferral |
| CitizenQuery-UK, 2026 | Evaluates answers to real government-service questions | Citizen QA rather than individual evidence-based decisions |
| SNAP QC FY2024 | Provides audited active-case data and official test variables | Data source, not an LLM benchmark |

## Defensible positioning

Prior work studies clarification under ambiguous requests, confidence-based abstention,
policy comprehension, and requirements for public-sector agent benchmarks. This project
connects these strands by isolating whether different presentations of a missing,
decision-critical field cause an LLM to issue an unsupported adverse decision on matched
real benefit records.

## Sources

- https://aclanthology.org/2024.acl-long.578/
- https://aclanthology.org/2024.findings-emnlp.636/
- https://aclanthology.org/2026.acl-long.1987/
- https://aclanthology.org/2026.sigdial-1.36/
- https://aclanthology.org/2024.naacl-long.366/
- https://arxiv.org/abs/2601.20617
- https://arxiv.org/abs/2604.12995
- https://arxiv.org/abs/2602.04064
- https://snapqcdata.net/datafiles

