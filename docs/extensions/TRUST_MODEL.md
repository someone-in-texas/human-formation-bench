# Extension trust model

An HFB extension is untrusted data until it has passed bounded parsing, schema validation, path
containment, sensitive-data checks, and project review. A manifest is provenance, not a sandbox.

## Current boundary

The proto-extension supports repository-bundled implementation code and declarative assets. Bundled
code has the same authority as HFB itself. Review it accordingly.

External configuration, packs, YAML, JSON, generated text, and web-derived material remain untrusted.
The current design does not promise safe automatic execution of third-party Python entry points.

## Required controls

- Read regular files only; reject symlinks at the trust boundary.
- Resolve paths beneath an explicit extension root.
- Bound bytes before parsing.
- Use safe YAML loading and strict models that reject unknown fields.
- Reject duplicate extension, scenario, policy, signal, and construct identifiers.
- Do not interpolate shell commands, templates, environment variables, or import paths from data.
- Do not expose provider credentials or private-pack content to extension reports or logs.
- Hash resolved behaviorally relevant inputs and fail resume closed when they change.
- Treat extension-provided prose as content, never as instructions to the evaluator.
- Keep research controls out of ordinary user deployment.

## Composition

Extensions are additive. There is no last-one-wins behavior. A proposed override requires a future
explicit capability with provenance, compatibility rules, and separate security review.

Resolution must be deterministic and order independent. Human-readable paths are not artifact
identity; manifests use stable IDs, versions, and content hashes. Absolute local paths should not be
published.

## External executable extensions

A future Python plugin system would allow code to read files, environment variables, private prompts,
and credentials available to the process. Package installation and extension activation would
therefore be security decisions. Before supporting it, HFB would need an explicit consent flow,
provenance and signature policy, dependency isolation guidance, capability restrictions where
practical, revocation, and adversarial tests. Declarative compatibility today must not be marketed as
that future sandbox.
