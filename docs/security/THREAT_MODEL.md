# Threat model

## Assets and boundaries

Assets include API credentials, private scenario packs, model outputs, human-rating data, run
provenance, budget caps, release artifacts, and repository automation. Untrusted boundaries include
scenario YAML, imported JSON, target and judge output, research URLs, pull requests, caches, and
downloaded dependencies.

## Principal threats and controls

| Threat | Control | Residual risk |
|---|---|---|
| Scenario prompt injection | Scenario text is data, never evaluator instruction; fixed system policy | Models may still follow injected text; adversarial tests are required |
| Malicious YAML/JSON | safe loader, size and NUL limits, strict schemas | Parser vulnerabilities remain dependency risk |
| Path traversal | resolve-and-containment checks; no archive extraction in core | Future pack installers need separate archive controls |
| Command injection | model output is never executed or interpolated into commands | Contributor code can add unsafe paths; review and CodeQL |
| Secrets/PII in logs | allowlisted environment summary, redaction, public-pack scan | Novel patterns can evade lexical screening |
| Cost overrun | serialized paid-call reservations, safety reserve, explicit mutable prices | One indivisible completed call can exceed an advertised cap if provider usage reporting is wrong |
| Evaluator manipulation | short evidence spans, independent signals, cross-family and human review | Persuasive outputs can still bias judges |
| Benchmark gaming | held-out private packs, paraphrases, rotations, disclosure field | Public-core optimization remains possible |
| Supply chain | pinned Actions, Dependabot, audit, CodeQL, SBOM, attestations | PyPI compromise and transitive vulnerabilities remain |
| Malicious PR | `pull_request`, least privilege, no secrets, no untrusted release | GitHub-hosted runner and action risk remain |
| Clinical misuse | repeated non-clinical claim boundary and sensitive-domain guidance | Documentation cannot prevent all downstream misuse |

No benchmark content is granted shell, network, filesystem, or tool authority. Live tests require an
explicit environment opt-in and never run on untrusted pull requests.
