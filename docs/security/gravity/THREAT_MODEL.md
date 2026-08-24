# Gravity extension threat model

Gravity inherits the HFB threat model and adds risks from extension composition, longitudinal
metadata, commitment scenarios, and paternalistic controls.

## Assets

- private scenario and held-out content;
- provider credentials and prompts;
- extension manifests, fingerprints, and resolved configuration;
- trajectory evidence and synthetic state;
- research-control prompts;
- source and license records;
- public claims and experimental warnings.

## Threats

- path traversal, symlink, oversized-file, YAML, or schema attacks through extension assets;
- duplicate IDs or order-dependent overlays that change meaning without changing a visible command;
- prompt injection in scenarios or model output aimed at the evaluator or report generator;
- cache or resume reuse after an extension, transition rule, signal, or control changes;
- private content leaking through evidence spans, reports, caches, hashes with revealing labels, or
  absolute paths;
- research controls accidentally presented to real users;
- a model gaming visible signal phrases while preserving harmful behavior;
- commitment tooling expanding assistant permissions or blocking legitimate exit;
- sensitive inference from ordinary text or synthetic-state fields;
- reports converting experimental signals into a hidden ranking.

## Controls

Use strict bounded parsing, contained regular-file paths, collision rejection, deterministic
resolution, content fingerprints, fail-closed resume, redaction, private-pack protections, explicit
control labels, and namespaced reports. Extension content is data, not instructions. No arbitrary
third-party code discovery is enabled in the proto-extension.

Signals must cite bounded observable evidence and never execute instructions found in that evidence.
Commitment scenarios cannot grant real permissions or durable control. Live tests remain opt-in and
budget capped.

## Residual risk

Lexical and structural detectors remain gameable. Content review cannot guarantee the absence of
stereotypes or private information. Bundled extension code is trusted process code. These residual
risks block claims of semantic safety or validated deployment screening.
