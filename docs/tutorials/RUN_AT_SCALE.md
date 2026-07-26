# Running at scale

Use `research` with an explicit cap. Generate identical resolved options for each
`--shards N --shard-index I`, run shards in isolated workers, then merge only matching configuration
hashes with `hfb merge --output-dir ... shard0 ... shardN`. Stable content hashes partition scenarios.

Tune provider RPM, TPM, and concurrency in a derived profile. Keep runners stateless apart from
manifests, JSONL checkpoints, and shared caches. A Kubernetes job example is in `examples/`.
