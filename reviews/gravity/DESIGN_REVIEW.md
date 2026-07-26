# Gravity extension design review

Status: architecture selection for an experimental vertical slice

This artifact records three independently developed proposals and their disagreements. The reviewers
were Codex subagents inspecting the repository from technical, compatibility, and methodology
perspectives. This is useful adversarial design work, not external expert, tradition-competent,
disability-community, psychometric, or human-subject review.

## Proposal A: hook-rich Gravity module

Build `human_formation_benchmark.modules.gravity` with module-specific loaders, state, transitions,
tasks, scorers, transfer logic, reports, and controls. Add a module registry that can later register
similar packages.

Strengths:

- maps directly to the full Gravity specification;
- supports custom behavior and Inspect tasks cleanly;
- makes the complete future research program legible.

Objections:

- risks a parallel framework beside the core runner;
- gives the first experimental theory too much architectural surface;
- encourages implementing unvalidated scoring and large authored packs prematurely;
- a broad hook API becomes difficult to secure or keep compatible before a second extension exists.

## Proposal B: declarative typed extension envelopes

Add a general, built-in extension registry and strict manifest. Carry Gravity-specific scenario
configuration in a namespaced typed envelope. Reuse core execution, budgets, storage, and reports.
Emit deterministic named signals tied to observable events rather than new ordinal scores.

Strengths:

- additive and small;
- preserves the existing formation vector and visible gates;
- creates a reusable seam without promising arbitrary third-party execution;
- makes missingness, event evidence, and experimental status explicit;
- allows a vertical slice to test the architecture before a large pack.

Objections and residual uncertainty:

- a data-first interface may be too narrow for later solver and scorer research;
- adding serialized fields to strict core v1 artifacts raises a schema-version question;
- built-in-only registration is not yet a user-installable plugin ecosystem;
- deterministic signals can still be lexical and gameable.

## Proposal C: package plugin ecosystem and immediate worldview extraction

Define installable Python entry points with capability hooks and migrate Christianity into its own
worldview plugin immediately. Potentially migrate every thick lens into a separate package.

Strengths:

- clear long-term ecosystem model;
- removes closed worldview enums from core;
- enables independently versioned extension releases.

Objections:

- automatic entry points execute third-party code with process authority and need a trust and
  revocation design;
- extracting Christianity alone creates religious exceptionalism while other thick lenses remain
  first-class;
- migrating all lenses and packaging simultaneously expands compatibility and governance risk far
  beyond the Gravity vertical slice;
- installed-package discovery, dependency conflicts, signing, provenance, and private-pack access are
  unresolved.

## Selected design

Select Proposal B for the experimental release:

- `extension` is the canonical term; `--module` is a compatibility alias;
- registry entries are built in and declarative;
- paths and content are validated and fingerprinted;
- Gravity emits named signals and observable event traces, not a canonical score;
- model judges, large packs, human calibration, and executable third-party plugins are staged;
- Christianity stays behaviorally and configurationally compatible in this release;
- closed perspective typing becomes data-extensible;
- the baseline required worldview set moves from Python into reviewed configuration;
- a later proposal must migrate all thick lenses together behind one worldview-extension contract.

## Preserved dissent

### Schema version

One proposal recommended publishing core schema `1.1` immediately because strict v1 JSON Schemas
reject additional serialized properties. The selected implementation can defer `1.1` only while
extension metadata remains in separately versioned extension schemas or is omitted from v1
serialization. If a new field is emitted in a scenario, trajectory, run manifest, or score report,
the dissent becomes a release blocker: publish a new core schema line and keep v1 immutable.

### Christianity migration

Some reviewers preferred immediate extraction to demonstrate that Christianity is not a core
primitive. The compatibility and pluralism objection prevailed: do not single it out. This does not
endorse the permanent fixed-lens architecture. The agreed follow-up is one migration for all thick
lenses, with preserved IDs, transition guidance, and tradition-competent review.

### Signals versus scores

The full specification asks for anchored construct scoring. Methodology review objected that software
anchors without human calibration could be mistaken for validation. The release therefore uses
signals. Future scores remain possible only after rubric, philosophy, methodology, minimal-pair,
judge, missingness, and validation work.

### Scope

The full specification calls for many scenarios, judges, statistics, visualizations, and reviews.
The technical proposal favored broader implementation. The selected staged approach treats a small
working vertical slice as more honest than unreviewed volume. The unimplemented portions remain
requirements for later milestones, not completed acceptance criteria.

## Release recommendation

The design review recommends an experimental prerelease only after implementation tests, strict docs,
security review, philosophy and methodology review, and explicit release notes pass. It does not
recommend a validated label, a universal composite, or claims about real-user outcomes.
