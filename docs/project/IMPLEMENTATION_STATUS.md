# Implementation status

This checklist is the release gate for the alpha. A checked item means an artifact exists and has
passed its stated automated check; it does not imply construct validity.

## Foundations and research

- [x] Contestable thin floor and thick worldview lenses are explicit.
- [x] Source registry records status, stable link, use, limitations, and non-claims.
- [x] All 16 dimensions have versioned rubrics and source mappings.
- [x] Theory of change exists in Mermaid and machine-readable YAML.
- [x] Measurement limits separate model behavior from real-user outcomes.
- [ ] Independent methodology and philosophy reviewers approve the release commit.

## Functional benchmark

- [x] `uv sync` succeeds.
- [x] `hfb --help`, `hfb doctor`, and asset validation work.
- [x] A no-network fake-provider run creates JSONL, CSV, Parquet, DuckDB, Markdown, and HTML.
- [x] Inspect-native task, scorer, and provider-neutral model path exist.
- [x] Checkpointed manifests, content cache, resume, filtering, deterministic sampling, and sharding exist.
- [x] Atomic reservations enforce a hard cap before concurrent provider calls.
- [x] Public core has 24 author-reviewed alpha scenarios spanning the required domains.
- [ ] Cross-provider live smoke test is run manually with a tiny explicit cap.
- [ ] Judge-model ensemble and human adjudication are implemented and calibrated against human ratings.

## Quality and security

- [x] Ruff, strict mypy, pytest, Hypothesis, package build, docs build, and fake smoke gates exist.
- [x] Path traversal, secret redaction, PII screening, safe YAML, and budget invariants are tested.
- [x] Public red-team fixtures are executable smoke regressions for six attack families.
- [ ] Per-dimension positive/negative/subtle/ambiguous/paraphrase/minimal-pair coverage and rotating
  held-out validation are complete.
- [x] GitHub Actions are least-privilege and pinned.
- [x] CodeQL, dependency review, Scorecard, Dependabot, SBOM, and attestations are configured.
- [ ] GitHub-hosted checks pass on the release-candidate commit.
- [ ] No unresolved Critical or High independent-review findings remain.

## Open source and release

- [x] Apache-2.0 code and CC BY 4.0 benchmark-data/documentation licensing is explicit.
- [x] Governance, conduct, security, citation, contribution, RFC, and change processes exist.
- [x] Issue forms, PR template, CODEOWNERS, and release tooling exist.
- [ ] Main ruleset is applied after required check names have completed at least once.
- [ ] `v0.1.0-alpha.1` package and release artifacts pass the prerelease script.
- [ ] GitHub prerelease is published and its wheel is verified in a clean environment.

The unchecked human-validation and live-provider items are deliberate alpha limitations, not silent
omissions. Release automation must fail while any required reviewer reports Critical or High findings.
