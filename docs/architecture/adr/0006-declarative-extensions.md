# ADR 0006: Declarative, typed experimental extensions

Status: accepted for the experimental alpha

## Context

HFB began with one public scenario pack, one core rubric vector, and a fixed set of thick worldview
lenses. The Gravity proposal needs additional scenario metadata, synthetic-state signals, transfer
events, reports, and controls. Building those as a second benchmark framework would duplicate the
runner, budgets, storage, provenance, and safety boundaries. Adding every proposed construct to the
core would instead turn one experimental theory into a universal HFB commitment.

The original worldview implementation also used a closed perspective list. Christianity should not
be privileged as a core primitive, but extracting Christianity alone while leaving secular,
virtue-ethical, care-ethical, communal-duty, and self-direction lenses in core would create a new and
unjustified asymmetry.

## Decision

HFB uses a small, data-first extension boundary:

- an extension has a strict manifest with an identifier, version, status, capabilities, and typed
  configuration;
- extension identifiers and asset identifiers are stable and collision checked;
- extension-specific scenario content is carried in a namespaced, typed envelope rather than added
  to the core dimension enum;
- the core retains ownership of parsing limits, contained paths, budgets, providers, storage,
  provenance, resume, sharding, and the existing formation-profile vector;
- the first implementation supports bundled extensions. Loading arbitrary third-party executable
  Python is outside this decision;
- deterministic extension logic emits named observable signals. A signal is not an ordinal score,
  a latent-trait estimate, or evidence of an effect on a real person;
- research controls remain visibly marked and require the same or stronger safeguards as core
  controls;
- unknown extension configuration fails closed. Extension assets cannot silently override core or
  other extension assets.

Gravity is the first experimental formation extension. Its initial release is a small vertical
slice, not the full research program described in `gravity-spec.md`. It reuses HFB execution and
artifacts while keeping Gravity-specific claims and signals distinct.

Worldview lenses remain operationally compatible in this release. Christianity is not extracted
alone. A later, separately reviewed migration should move **all** thick lenses behind the same
worldview-extension contract while preserving the current lens and policy identifiers through a
documented compatibility period. The thin floor remains core and contestable.

## Schema compatibility

The extension manifest and Gravity envelope have their own versioned schemas. That does not by itself
require changing every core artifact from schema `1.0` to `1.1`.

However, a core schema with `additionalProperties: false` cannot gain a serialized field while still
claiming to be the identical `1.0` contract. If implementation adds extension metadata to a core
scenario, trajectory, manifest, or score report, it must publish a new core schema version and keep
the committed v1 schema snapshots readable. An additive `1.1` line is sufficient when old inputs
remain valid; a semantic reinterpretation or removal requires a major schema version. Code may not
silently overwrite the existing v1 snapshots.

## Consequences

Benefits:

- Gravity extends rather than replaces HFB.
- Other formation theories can use the same bounded envelope and provenance contract.
- Core scores and failure gates remain comparable with existing runs.
- Experimental claims remain visibly namespaced and removable.
- Worldview migration can be handled consistently rather than singling out one tradition.

Costs and limits:

- Extension composition, collisions, hashes, and compatibility require new regression tests.
- A data-first contract cannot express every future solver or scorer without later review.
- Bundled code is still trusted package code; the manifest is not a sandbox.
- Separate signals require careful reporting so readers do not treat them as a hidden composite.

## Rejected alternatives

**Gravity-specific command branches and parallel models.** Rejected because they would duplicate
security and reproducibility infrastructure.

**Add all Gravity constructs to `Dimension`.** Rejected because the constructs are experimental and
partially overlap existing dimensions.

**Automatically import third-party entry points.** Rejected for the proto-extension because
installation would become code execution with access to provider credentials and private packs.

**Extract only Christianity now.** Rejected because it changes one tradition's status without a
general worldview migration or a compatibility and review plan.

**Implement the full proposed pack and model-judge ensemble immediately.** Rejected because authored
volume is not validation, configured model judging is not yet calibrated evidence, and large
normative changes require methodology and philosophy review.
