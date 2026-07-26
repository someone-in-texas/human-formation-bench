# Alpha review summary

Release decision: **approve with non-blocking reservations** for
`v0.1.0-alpha.1`.

The review target was implementation commit
`328288e9bba99e846f75b2effea43834f7372b93`. Five required independent review
passes and one additional Goodhart/red-team pass found no unresolved Critical
or High findings.

| Review discipline | Verdict | Unresolved Critical/High |
|---|---|---:|
| Technical and reproducibility | Approve with non-blocking reservations | 0 |
| Psychometrics and methodology | Approve with non-blocking reservations | 0 |
| Philosophy and pluralism | Approve with non-blocking reservations | 0 |
| Alignment and adversarial robustness | Approve with non-blocking reservations | 0 |
| Security, privacy, and open source | Approve with non-blocking reservations | 0 |
| Goodhart/red-team (additional) | Approve with non-blocking reservations | 0 |

The final artifacts are in each review-domain directory. They preserve the
initial findings, resolution evidence, exact reviewed commit, validation
commands, and non-blocking reservations.

## What changed because of review

- Deterministic lexical logic is detector-only: it emits no ordinal formation
  score, cannot update synthetic state, and cannot earn research assurance.
- Multi-policy results remain separate, use equal-scenario clustered
  summaries, expose paired scenario/seed contrasts, and never pool harmful
  controls into a benign headline.
- Research assurance fails closed when configured judges are unavailable.
  The alpha does not claim calibrated model-judge, human-rater, construct, or
  real-user outcome validity.
- Research and frontier longitudinal horizons execute at 15 and 24 turns, with
  an evaluation-aware sleeper control and attributed failure-gate evidence.
- Six versioned philosophical lenses, executable positive/adversarial
  contrasts, and distinct policy rationales make worldview disagreement
  visible without asserting a universal scalar ranking.
- Private packs disable caching, withhold transcript bodies and source paths,
  replace pack/scenario/sample identifiers with opaque hashes, restrict run
  and export permissions, and exclude trajectories from copied exports.
- Runs maintain canonical per-trajectory content hashes. Resume and shard
  merge reject missing, duplicated, or content-modified records.
- Execution, aggregation, reporting, columnar export, and shard merge stream
  records rather than retaining the complete trajectory corpus.
- The release builds a reproducible SBOM from a clean, locked, wheel-installed
  runtime; dev/release tools and a duplicate project component are rejected.
- Main and release tags are protected, releases require the `release`
  environment, checksums exclude themselves, and build provenance is attested.

## Validation evidence

- Ruff formatting and lint: pass
- Mypy: pass for 17 source files
- Pytest: 64 pass; 1 opt-in live-provider test skipped
- Strict documentation build: pass
- Benchmark asset validation: 24 scenarios, 16 rubrics, 5 profiles, 37
  sources, 7 constitutions, 6 lenses, 12 perspective contrasts, and 6 public
  adversarial challenges
- Dependency exception gate and `pip-audit`: pass, with the pinned Click
  exception scheduled for review by 2026-08-15
- Clean-runtime SBOM: 88 runtime components and byte-identical output across
  two independent generations
- GitHub PR checks: Linux Python 3.11/3.12/3.13, macOS Python 3.12, Windows
  Python 3.12, package smoke, security, dependency review, docs, benchmark
  smoke, and CodeQL all pass

## Preserved limitations

This is an open, public, pre-validation alpha. Public cases and detectors can
be contaminated or optimized against. Private-pack secrecy is not evidence of
validity. The public core is a small English-language author sample; its
anchors, cultural coverage, human-rating path, and affected-community
validation remain incomplete. Failure gates recognize narrow overt patterns,
not semantic safety. Paired deltas are descriptive, not proof of normative
disagreement. Synthetic trajectories and diagnostic state annotations do not
establish effects on real people.

The review passes were performed by independent Codex subagents with distinct
disciplinary roles. That separation is useful for adversarial engineering
review but is not a substitute for external domain experts, tradition-competent
reviewers, affected communities, blinded human raters, or preregistered
human-subject research. Medium and Low follow-ups remain tracked as public
issues and are required before stronger validity or assurance claims.
