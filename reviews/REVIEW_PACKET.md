# Alpha critical-review packet

Reviewed baseline commit: `2244b20`

## Purpose and claim boundary

HFB evaluates observable assistant behavior and structured synthetic trajectories plausibly related to
human formation. It does not infer a real user's psychological, moral, spiritual, or clinical state.
The canonical result is a 16-dimension vector with uncertainty, missingness, and separate failure
gates; there is no default composite leaderboard.

## Architecture

- Strict Pydantic schemas and safe bounded YAML.
- Twenty-four public-core scenarios, 16 rubrics, seven policies/lenses, and five cost profiles.
- Deterministic fake provider plus provider-neutral Inspect adapter.
- Async concurrency, request pacing, atomic budget reservations, checkpointed JSONL, resume,
  content-addressed caching, deterministic sharding, and merge.
- JSON, CSV, Parquet, DuckDB, Markdown, HTML, benchmark card, and immutable initial manifest.
- Public repository security, CI, docs, package, SBOM, attestation, and prerelease workflows.

See `docs/architecture/ARCHITECTURE.md`, `docs/methodology/`, `docs/philosophy/`,
`docs/research/`, and `docs/security/`.

## Research and normative map

`docs/research/SOURCE_REGISTRY.yaml` contains 37 records with status, URL/DOI, use, limits, and
non-claims. `docs/research/EVIDENCE_MAP.md` maps dimensions to anchors. The audit corrected the seed
specification's unrelated automation-bias DOI. The thin floor and thick-lens disagreements are
explicit in `docs/philosophy/`.

## Verification at baseline

- Ruff formatting and lint: pass.
- Strict mypy: pass, 17 source files.
- Pytest: 49 pass, one opt-in live test skipped.
- Coverage: 87.39%.
- Strict MkDocs build: pass.
- Inspect-native mock evaluation: pass, two samples.
- Full fake micro run: pass, 24 trajectories, `$0.00`.
- Wheel build, clean install, asset validation, and fake run: pass.
- Pip audit: one documented transitive exception, `PYSEC-2026-2132`, expiring 2026-08-15;
  Inspect's Click constraint blocks the fixed version and HFB/Inspect do not call `click.edit()`.

## Sample result

`examples/sample-report/report.md` is an actual four-trajectory fake-provider summary. It is labeled
low assurance and contains the public claim boundary. Full run artifacts include provenance and all
required storage formats.

## Known limitations

- No paid live-provider call was made in this implementation session.
- Model-judge ensemble, human-rater calibration, DIF, and measurement invariance remain future
  validation work and are not claimed complete.
- Public-core scenarios are small, authored for alpha, and contamination-prone.
- The deterministic scorer is lexically shallow and expressly not ground truth.
- The Click dependency exception is temporary and fail-closed at its review date.
- GitHub-hosted checks, rulesets, and the prerelease are completed only after review remediation.

## Review instructions

Write YAML matching the specification under the assigned `reviews/<domain>/initial.yaml`. Use
Critical, High, Medium, Low, or Note. Cite concrete paths and line ranges. A release-blocking verdict
is `request_changes`. Do not manufacture consensus; non-blocking reservations are welcome.
