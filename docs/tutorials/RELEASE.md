# Release process

Update the changelog and citation version, resolve all Critical/High review findings, satisfy the
machine-readable policy in `reviews/review-policy.yaml`, and run
`uv run python scripts/pre_release.py --tag v0.2.0-alpha.1`. Build the wheel and sdist, install
the wheel in a clean environment, run the fake benchmark, generate schemas, SBOM, checksums, source
registry snapshot, review summary, and sample report.

For the `internal_alpha` stage, internal independent review continuity and a current cross-cutting
review artifact are required; external specialist approval is advisory under ADR 0007. Switch the
policy to `external_review` with `external_verification.required: true` at any ADR 0007 trigger.

Push the PR, wait for every required check, and merge it. Fetch the exact resulting `origin/main`
commit, then dispatch the prerelease-candidate workflow on `main` with `prerelease=true`; verify its
`headSha` is that commit. After it passes, create and push the annotated tag at the same commit and
watch the release workflow. Download the published artifacts, verify `SHA256SUMS` and the
build-provenance attestation, then test the wheel in a clean environment. Do not promote an
unvalidated alpha to beta, stable, or 1.0.
