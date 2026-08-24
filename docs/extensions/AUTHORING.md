# Author an experimental extension

Extensions add bounded, versioned evaluation content without replacing HFB's runner or core vector.
The current interface is experimental and intended first for bundled, reviewable extensions.

## Start with the claim boundary

Before writing configuration, state:

1. the observable assistant behavior of interest;
2. what the extension emits;
3. what the output does **not** establish;
4. the normative assumptions and likely dissent;
5. the evidence and source-license status;
6. the smallest scenario set that could falsify the intended distinction.

An extension must not claim to infer a user's virtue, diagnosis, faith, flourishing, addiction, or
durable capacity from ordinary model text. Synthetic state is labeled simulation, not observation.

## Manifest

Use the committed extension-manifest schema. Provide a stable lowercase identifier, semantic version,
experimental status, capabilities, and typed configuration. Keep content under the extension's
namespace. Do not depend on filesystem traversal, symlinks, network retrieval, environment-variable
expansion, or implicit override order.

The manifest version describes the extension bundle. Scenario, signal, transition, and rubric-like
assets may carry more specific versions. A run must preserve enough resolved metadata and hashes to
identify all behaviorally relevant inputs.

## Scenario envelopes

Keep universal scenario fields in the HFB scenario record. Put extension-specific data in its typed
envelope. The envelope should contain only information required for execution or interpretation.
Reject unknown fields.

Good extension metadata identifies observable conditions such as a declared learning goal, an
available human handoff, an emergency, an accommodation, or a scheduled withdrawal event. Avoid
unobservable labels such as "the user became wise" or "the assistant caused dependency."

## Signals and scoring

Prefer deterministic named signals for narrow events that can be recognized reliably. Signals must
include their polarity and evidence location where applicable. They do not automatically become
scores.

An extension that proposes ordinal scoring must separately document anchors, missingness,
not-applicable rules, known confounds, accessibility effects, source mappings, validation hypotheses,
and philosophy and methodology approval. Do not create a canonical composite.

## Registration and composition

Registration is currently limited to reviewed built-ins. A new built-in adds one core registration
record containing a declarative descriptor plus allowlisted validator, reporter, resource package,
and runtime-file provenance. The registry never discovers or imports third-party entry points.

- Extension and asset IDs must be unique after resolution.
- Duplicate IDs are errors, even when payloads are identical.
- An extension may not silently override another extension or core asset.
- Dependencies and compatible core versions must be explicit.
- Resolution order must not change hashes or meaning.
- Research controls must remain visibly distinguishable from safe policies.

This is a proto-extension seam, not a claim that independently installed packages can plug in without
core review. A future external plug-in API requires a separate threat model and compatibility RFC.

## Required tests

At minimum test strict parsing, unknown fields, duplicate IDs, deterministic serialization, content
hash changes, contained paths, size limits, signal evidence, legacy core runs, installed-wheel assets,
resume mismatch, and failure under incomplete configuration. Add accessibility, emergency, and
adversarial minimal pairs when the construct depends on level of assistance.

## Review and release

Normative or rubric-like changes follow the RFC and rubric-change processes. Empirical claims require
`SOURCE_REGISTRY.yaml` entries or mappings. Preserve dissent in review artifacts. Experimental content
must not be described as validated merely because schemas and tests pass.
