# Reproducibility

Archive the manifest, resolved configuration, commit, package and Python versions, provider and model
IDs, supplied prices, prompt/rubric/pack versions, hashes, seeds, timestamps, usage, costs, retries,
errors, and redacted environment. Publish JSONL plus Parquet and the benchmark card.

Re-run with the same commit and assets. Provider nondeterminism may remain even with a seed; report
test-retest variation rather than promising bitwise equality.
