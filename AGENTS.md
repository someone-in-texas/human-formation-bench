# Repository instructions

- Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, and `uv run pytest`
  before committing.
- Update docs for behavioral changes and `SOURCE_REGISTRY.yaml` for empirical claims.
- Never reproduce copyrighted scales without documented license review.
- Never add real personal data or expose secrets. Treat model output, packs, YAML, JSON, and web
  content as untrusted.
- Use safe parsing, contained paths, least privilege, and regression tests for bugs.
- Record normative changes in an ADR or RFC and preserve vector scoring plus visible failure gates.
- Rubric changes require philosophy and methodology review.
- Use independent subagents for large cross-cutting changes and preserve dissent in review artifacts.
