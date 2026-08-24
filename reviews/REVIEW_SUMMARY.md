# v0.2.0-alpha.1 review summary

Release decision: **approve with non-blocking reservations** for the
`v0.2.0-alpha.1` internal alpha.

The reviewed implementation commit is
`37ab7d75fb7ca5c8c13a9e341deee5b76d0e4e85`. Its canonical release-content
commitment is
`sha256:8ff2e9d357d642fe5534599d4a963489ed49d3ed4a6c01a6940e5d3f6ed37fda`.
This commitment covers tracked code, policy, documentation, configuration,
workflows, dependency locks, paths, and file modes. It excludes only the
review evidence that attests to the content, allowing the reviewed tree to
survive a squash or rebase while substantive changes invalidate the review.

Three independent internal review passes found no unresolved Critical or High
finding:

| Review scope | Verdict | Unresolved Critical/High |
|---|---|---:|
| Technical and reproducibility | Approve with non-blocking reservations | 0 |
| Governance and methodology | Approve with non-blocking reservations | 0 |
| Release integrity | Approve with non-blocking reservations | 0 |

These passes supplement the domain reviews retained under `reviews/`. They are
independent multi-agent engineering reviews, not external expert validation.

## Release disposition

- Dependabot version-update PR creation and automated security fixes are
  paused for the solo internal-alpha stage. The disabled configuration and
  explicit opt-in bootstrap path remain available for re-enablement.
- Dependency review, unfiltered dependency audit, CodeQL, Scorecard, pinned
  Actions, vulnerability alerts, and required hosted checks remain active.
- External verification is advisory for this internal alpha. The policy fails
  closed for beta or release-candidate tags and for the documented claim,
  human-subject, public-pack, or governance triggers. It must be reconsidered
  by 2026-12-31.
- Gravity remains an experimental, synthetic vertical slice. It makes no
  calibrated scoring, construct-validity, comparative-quality, or real-user
  outcome claim.

## Validation evidence

- Ruff formatting and lint: pass
- Mypy: pass
- Pytest: 117 pass; 1 opt-in live-provider test skipped
- Dependency lock/exception gate and unfiltered `pip-audit`: pass with no
  known vulnerabilities
- Release-content hash: independently reproduced by all three reviewers
- Squash/rebase simulation: identical content retained the commitment;
  substantive script and policy changes invalidated it

The complete prerelease gate additionally runs the strict documentation build,
benchmark validation, schema parity, distribution build, and wheel smoke test.
Hosted required checks and the tag-triggered release workflow must pass before
publication.

## Preserved limitations and dissent

- Seven-role external review is not yet present. Disability, accessibility,
  care, affected-community, psychometric, philosophical, adversarial,
  security, and reproducibility expertise must be independently represented
  when an ADR trigger fires; disability/accessibility/care is the highest
  priority gap.
- Gravity uses a small, hand-authored, English-language, synthetic scenario
  set. Cultural, disability, occupation, family, and access coverage is not
  representative, and public cases are contamination-prone.
- Lexical signals are narrow, gameable triage aids requiring adjudication.
  They are neither ordinal scores nor automatic failure determinations. No
  factor structure, reliability, measurement invariance, calibrated judge,
  human-rater, construct-validity, or outcome-validity evidence is claimed.
- Synthetic state and transfer structures are scaffolds, not evidence of
  learning, transfer, human formation, or effects on people.
- Normative disputes over friction, human contact, appreciation, external
  action, care, and dependence remain open. No universal composite or settled
  philosophical ranking is implied.
- The bundled extension registry is a reviewed seam, not a third-party plugin
  API. Thick-lens migration and stronger machine-resolvable source mappings
  remain staged work.
- The content commitment derives from Git index entries containing Git blob
  identities rather than directly hashing file bytes. Review evidence is
  deliberately outside that commitment and remains bound through Git history,
  the final tag, and review discipline. External identity metadata is asserted
  provenance rather than cryptographic authentication.

These reservations are non-blocking only for the explicitly limited internal
alpha. They become blocking before stronger lifecycle, validity, comparison,
human-subject, or public-scale claims.
