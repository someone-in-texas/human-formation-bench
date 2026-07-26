# Secrets and private extensions

Use provider-standard environment variables only in the local process. Never place keys in YAML,
command history examples, test fixtures, reports, caches, issues, or pull requests. `doctor` reports
only whether some provider key is present, never its name or value. Common credential and direct-PII
patterns are redacted before logs.

Private scenario packs belong outside the repository and may be selected with `HFB_HOME`.
`private_packs/`, `.env`, run outputs, databases, and Parquet files are ignored. Do not publish a run
artifact until scenario text and representative examples have been reviewed for private information.

If a secret is committed, revoke it first, then use an incident-specific history-removal plan. Merely
deleting the current file is insufficient.
