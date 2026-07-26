# Troubleshooting

- `inspect-ai` install fails: confirm Python 3.11+; this checkout uses Python 3.12.
- Assets not found after install: set `HFB_HOME` to a checkout and report the packaging defect.
- Paid run refuses to start: provide current `--input-cost`, `--output-cost`, and `--budget-usd`.
- Resume rejects options: use the original run directory and resolved configuration.
- Empty filter: check exact values with `hfb list scenarios`.
- Live provider error: run `inspect eval` with the same model to validate provider credentials.
