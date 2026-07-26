# ADR 0003: JSONL checkpoints with DuckDB and Parquet views

Status: accepted

Each completed trajectory is appended to portable JSONL and checkpointed in the manifest. Resume
deduplicates stable sample IDs. Finalization creates Parquet and DuckDB for scale, while JSON and CSV
remain accessible. Content-addressed response caching reduces repeat spend without storing secrets.
