# Authoring scenarios

Copy the schema fields from `data/public_core/scenarios.yaml`; write behaviorally specific stakes,
affected parties, consent, uncertainty, prohibited shortcuts, positive indicators, and failure modes.
Avoid stereotypes and real user data. Run `hfb pack validate` and `hfb pack hash`.

Canonical additions require deduplication, PII/leakage checks, philosophy and psychometric review,
adversarial mutation, human approval, a changelog entry, and a version bump.
