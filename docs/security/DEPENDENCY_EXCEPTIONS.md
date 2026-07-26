# Dependency-audit exceptions

## PYSEC-2026-2132 / CVE-2026-7246

- Package: Click 8.2.1
- Fixed version: 8.3.3
- Review deadline: 2026-08-15
- Status: temporary, explicit transitive exception

The advisory concerns command injection through `click.edit()`. HFB does not call `click.edit`, and a
source scan of the installed Inspect AI package found no call. Inspect AI 0.3.249 requires Click below
8.2.2 because of its documented compatibility constraint, so resolving to the fixed release is
currently unsatisfiable. The security workflow still audits every other dependency and names this one
exception explicitly.

This is not a claim that vulnerable code is harmless in every downstream environment. Do not add a
call to `click.edit`; the security test should be extended if the dependency graph changes. The
prerelease gate fails at the review date, requiring removal, upstream upgrade, a safe patch, or an
explicitly renewed decision with evidence.
