# Chosen Gravity experimental extension

Gravity examines a limited question: when assistance removes effort, uncertainty, interpersonal
friction, or practical work, does it also remove an opportunity relevant to the user's stated goal?

This is a synthetic behavioral benchmark, not a validated psychometric instrument. It does not
measure a real person's flourishing, competence, dependence, loneliness, virtue, spirituality, or
mental health. Its signals are deterministic triage evidence, not semantic judgments or scores.

## Vertical-slice quick start

```bash
hfb list extensions
hfb validate --extension gravity
hfb plan --extension gravity --profile gravity_micro --max-samples 2 --json
hfb run \
  --extension gravity \
  --profile gravity_micro \
  --model fake/formation-v1 \
  --max-samples 2 \
  --budget-usd 5 \
  --hard-stop
```

`--module gravity` is a compatibility alias for `--extension gravity`. Extension provenance and its
content fingerprint are included in resolved configuration and extension run manifests. Changing a
behaviorally relevant extension asset invalidates resume compatibility.

The micro profile contains no research controls. Selecting a research-control policy requires
`--allow-research-controls`; those policies are synthetic known-groups fixtures and must never be
deployed to users.

## What is implemented

- a strict built-in extension descriptor and contained asset allowlist;
- a versioned Gravity scenario envelope, synthetic state, observable events, transfer records,
  construct models, and explicit experimental result models;
- a small authored scenario vertical slice and safe reference policies;
- high-precision deterministic signals with evidence spans and no ordinal score;
- bounded event-driven transitions and transfer preconditions;
- extension-aware planning, validation, running, provenance, caching, and resume;
- explicit opt-in for research controls.

## What is staged

- calibrated model-judge execution;
- a large independently reviewed public pack;
- validated ordinal construct scoring;
- human-rater calibration and adjudication;
- reliability, invariance, and construct-validity evidence;
- live-provider comparative claims;
- human-subject outcome validation;
- arbitrary third-party executable extensions.

The presence of model-judge or larger-profile design metadata does not mean the current runner can
execute those stages. Unsupported judges fail closed.

## Read next

- [Theory of change](../methodology/gravity/THEORY_OF_CHANGE.md)
- [Construct proposals](../methodology/gravity/CONSTRUCTS.md)
- [Core crosswalk](../methodology/gravity/CROSSWALK.md)
- [Scenario taxonomy](../methodology/gravity/SCENARIO_TAXONOMY.md)
- [Synthetic state](../methodology/gravity/STATE_MODEL.md)
- [Transfer protocol](../methodology/gravity/TRANSFER.md)
- [Philosophical foundations](../philosophy/gravity/FOUNDATIONS.md)
- [Critiques](../philosophy/gravity/CRITIQUES.md)
- [Claims ledger](../research/gravity/CLAIMS_LEDGER.md)
- [Limitations](../research/gravity/LIMITATIONS.md)
- [Accessibility safeguards](../security/gravity/ACCESSIBILITY.md)
