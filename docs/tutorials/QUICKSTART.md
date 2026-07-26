# Quickstart

Install with `uv sync`, run `uv run hfb doctor`, inspect the call graph with `uv run hfb plan
--profile micro`, and execute the no-network demo with `uv run hfb run --profile micro --hard-stop`.
Open `runs/<id>/report.html`; confirm the low-assurance banner, vector, intervals, failure gates,
missingness, cost, and “does not mean” section. Resume interrupted work with `hfb resume`.

Before a paid run, verify current provider prices and pass `--input-cost`, `--output-cost`, and an
explicit `--budget-usd`. Start with `--max-samples 2`.
