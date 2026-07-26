# Synthetic-user simulation

The simulator is hybrid. A bounded `UserState` holds probabilities for self-directed action,
outsourcing, uncertainty tolerance, reassurance seeking, evidence checking, human contact,
AI exclusivity, independent attempts, retained skill, guardrail use, and domination preference.
Rule-based transitions use scored observable response features. An optional language model may render
replies, but it never determines by itself whether formation occurred.

Each update is small, clamped to `[0, 1]`, deterministic for a fixed transcript, and separately
auditable. The same scenario, initial state, external events, and random seed can be replayed across
policies. Target, simulator, judge, adversary, and council model identities are recorded separately;
reports warn when roles share a family.

These variables are simulated counterfactual state, not clinical facts. They help test longitudinal
policy consistency and generate hypotheses. Only real-world, ethically reviewed evidence can support
claims about user change.
