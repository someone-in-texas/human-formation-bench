# Dependency-audit exceptions

## Active exceptions

None.

## Resolved: PYSEC-2026-2132 / CVE-2026-7246

- Package: Click 8.2.1
- Fixed version: 8.3.3
- Review deadline: 2026-08-15
- Status: resolved 2026-08-23 by upgrading Inspect AI to 0.3.260 and Click to 8.4.2
- Reviewed dependency: Inspect AI 0.3.249
- Advisory aliases: GHSA-47fr-3ffg-hgmw, CVE-2026-7246
- Owner: security maintainers

The advisory concerned command injection through `click.edit()`. HFB does not call `click.edit`, and a
source scan of the installed Inspect AI package found no call. Inspect AI 0.3.249 requires Click below
8.2.2 because of its documented compatibility constraint, so resolving to the fixed release is
was unsatisfiable at the time. The former executable exception gate bound both package versions and scanned HFB and
the installed Inspect package for a `click.edit` call. Any dependency drift or new call fails closed.
The security workflow still audits every other dependency and names this one exception explicitly.

This is not a claim that vulnerable code is harmless in every downstream environment. Do not add a
call to `click.edit`; the security test should be extended if the dependency graph changes. The
prerelease gate failed at the review date. The dependency was upgraded, the audit ignore was removed,
and the normal unfiltered `pip-audit` gate now covers this advisory.
