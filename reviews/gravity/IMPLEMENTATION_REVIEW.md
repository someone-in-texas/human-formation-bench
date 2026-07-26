# Gravity implementation review

Date: 2026-07-26

This record preserves the independent internal review cycle requested for the Gravity
proto-extension. It is not a substitute for the seven specialist approvals required by
`gravity-spec.md`, external expert review, disability-community review, psychometric validation, or
human-subject review.

## Reviewers and initial verdicts

Three agents reviewed commit `91c5d70` independently after the initial implementation:

| Reviewer | Scope | Initial verdict |
|---|---|---|
| Noether (`architecture_proposal`) | architecture, security, reproducibility | request changes |
| Halley (`methodology_proposal`) | methodology, philosophy, accessibility, claim boundaries | request changes |
| Meitner (`compatibility_proposal`) | compatibility, regression, packaging, release | block merge and release |

The reviewers agreed on the following High findings:

1. `hfb validate --extension gravity` validated runner projections but not the canonical typed
   Gravity research assets.
2. Runtime worldview models had widened while still declaring the frozen schema-v1 contract.
3. Hand-authored Gravity JSON Schemas did not match the runtime models and were not packaged.
4. Exact-pattern detector output pooled policies, was absent from HTML, and could be mistaken for
   adjudicated failure gates.
5. Public helper APIs could construct evidence-free ordinal or transfer claims.
6. Core report/export paths materialized every trajectory, reopening a previously resolved scaling
   defect.
7. Existing core research controls unintentionally acquired a new CLI opt-in requirement.
8. Private-pack resume could not safely reattach the withheld source pack.

Material dissent and staged-work findings were also preserved:

- The current built-in registry is a reusable reviewed seam, but not a third-party plug-in API.
- State-transition and transfer record models are not integrated into actual benchmark runs.
- Rubric source mappings and prose minimal pairs need stronger machine-resolvable fixtures.
- The authored scenario set has internal multi-agent review only; it has not received the external,
  accessibility/care, psychometric, or affected-community review required for release claims.
- The required seven exact-commit specialist reviews remain absent, so this work must remain a draft
  prerelease candidate even when automated gates pass.

## Remediation

The implementation was revised to:

- register a semantic validator and reporter through one reviewed built-in registration record;
- parse and cross-check all rich scenarios, rubrics, profiles, manifest, configuration, runner
  projections, policies, controls, and packaged schemas;
- include behaviorally relevant built-in Python files in the extension fingerprint;
- restore the schema-v1 worldview enum and add schema generation/no-diff CI coverage;
- generate and package Gravity JSON Schemas from the runtime models;
- stream core and Gravity report/export inputs without whole-corpus materialization;
- preserve legacy core-control execution while requiring opt-in for declared Gravity controls;
- require explicit, hash-matching private-pack reattachment on resume;
- emit policy-attributed detector hits with evidence in JSONL, Markdown, HTML, and the benchmark card;
- label lexical matches as adjudication-required detector hits rather than automatic failure
  determinations;
- suppress reviewed negation, safety-context, and benign emergency-clarification false positives;
- remove ordinal and transfer builders from the public Gravity API and require complete evidence
  provenance in the internal models;
- label the scenarios `internal_multi_agent_reviewed` with scoped provenance instead of claiming
  independent external review; and
- document that run-time transition/transfer integration, calibrated scoring, third-party plug-ins,
  and specialist review remain staged.

## Release disposition

Do not merge or tag solely on the basis of this internal review. A release candidate remains blocked
until the specialist roles required by `gravity-spec.md` review the exact candidate commit and all
Critical and High findings are resolved. Automated tests establish implementation consistency, not
construct validity.
