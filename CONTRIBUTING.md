# Contributing

Thank you for helping make HFB more honest, pluralistic, reproducible, and difficult to game.

1. Open an issue before a normative or schema-breaking change.
2. Create a focused branch and add tests for behavior changes.
3. Run `uv sync`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, and
   `uv run pytest`.
4. Update documentation, source mappings, changelog, schemas, and pack hashes as applicable.
5. Submit the pull-request template with methodology, worldview, security, cost, and evidence impact.

Never add real personal data, secrets, copyrighted psychological instruments without license review,
or generated scenarios to the canonical pack without human approval. Treat model output and imported
packs as untrusted.

Scenario proposals follow `docs/contributing/SCENARIO_CHANGES.md`; rubric and normative changes follow
`docs/contributing/RUBRIC_CHANGES.md` and the RFC process. Source corrections should show the primary
source and describe downstream impact. A removal request may be based on privacy, license, safety,
construct validity, stereotyping, or contamination.
