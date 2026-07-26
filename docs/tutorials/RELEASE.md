# Release process

Update the changelog and citation version, resolve all Critical/High review findings, obtain five
domain approvals, and run `uv run python scripts/pre_release.py`. Build the wheel and sdist, install
the wheel in a clean environment, run the fake benchmark, generate schemas, SBOM, checksums, source
registry snapshot, review summary, and sample report.

Dispatch the prerelease workflow with `prerelease=true`, verify attestations, publish
`v0.1.0-alpha.1`, and test the downloaded wheel. Do not promote an unvalidated alpha to 1.0.
