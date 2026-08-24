# ADR 0007: Stage external specialist review during the solo alpha

Status: accepted for experimental alpha; review by 2026-12-31 and at the second maintainer

## Context

HFB has one maintainer and does not yet have a standing panel of independent domain experts. Requiring
external approval for every experimental merge would make the repository unable to iterate, while
silently treating internal review as external verification would overstate assurance.

The repository already separates experimental software consistency from construct validation. Gravity
is namespaced, opt-in, explicitly uncalibrated, and does not publish ordinal construct scores or claims
about effects on real people. Its internal review also preserves substantive dissent about disability,
care, accessibility, cultural scope, and the meaning of formation.

## Decision

For the `internal_alpha` stage recorded in `reviews/review-policy.yaml`, external specialist approval is
advisory rather than a merge or prerelease gate. Alpha changes still require:

- all automated branch and release checks;
- independent internal review across technical/security and relevant normative domains;
- no unresolved Critical or High findings;
- visible limitations, provenance, and dissent in review and release artifacts; and
- no claim that internal multi-agent review is external validation.

The machine-readable policy retains an `external_verification` switch. Setting `required: true` makes
the prerelease gate require all seven external specialist roles, externally marked review artifacts,
and candidate-commit binding (or its direct parent when the final commit contains review artifacts
only). The policy review date also fails closed so the temporary stage cannot continue silently.

External specialist approval becomes release-blocking before any of these triggers:

- beta or stable promotion;
- calibrated or ordinal scoring;
- comparative, construct-validity, or real-user outcome claims;
- human-subject research;
- a large public scenario-pack expansion; or
- establishment of a second active maintainer and a viable review panel.

Disability, accessibility, and care review is the highest-priority missing perspective. It must be
obtained before public-pack expansion or stronger claims; the current waiver applies only to the small,
synthetic, experimental vertical slice.

## Consequences

Alpha development can merge without unavailable experts, but its assurance ceiling stays explicit.
The external-review framework remains fail-closed and can be re-enabled with a one-field policy change
plus qualifying review artifacts. Automated safety, vector scoring, visible failure gates, rubric
review requirements, and human-subject protections are unchanged.
