# Adding a provider

Prefer an Inspect model identifier. `InspectProvider` already supports providers configured by
Inspect, including OpenAI, Anthropic, Google, and OpenAI-compatible local endpoints. Keep credentials
in provider-standard environment variables.

A new direct adapter must implement the `Provider` protocol, report tokens, latency, cost and request
ID, accept a deterministic seed when supported, and have fake integration tests. Never log keys.
