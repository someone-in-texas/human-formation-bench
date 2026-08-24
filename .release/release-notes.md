# Human Formation Benchmark v0.2.0-alpha.1

This is an experimental, not construct-validated alpha. It evaluates observable assistant behavior and
synthetic trajectories; it does not measure a real person's psychological or spiritual state.

This prerelease adds the namespaced Gravity experimental extension: a declarative extension seam,
12 synthetic scenarios, 10 construct rubrics, four profiles, opt-in research controls, packaged
schemas, policy-attributed detector evidence, and complete extension provenance. Gravity remains a
small internally reviewed vertical slice, not a validated scale or evidence about effects on people.

The release also updates Node 24-native Actions, removes an expired dependency-audit exception through
upstream upgrades, and closes shard-merge and resume provenance gaps. Dependabot PR automation is
paused while dependency review, unfiltered audit, CodeQL, Scorecard, and pinned Actions stay active.

ADR 0007 makes unavailable external specialist approval advisory only for this experimental alpha.
External review becomes blocking before larger packs, calibrated/comparative claims, human studies,
or beta/stable promotion; disability, accessibility, and care review remains the priority gap.

Verify artifacts with `gh attestation verify <artifact> --repo someone-in-texas/human-formation-bench`
and `shasum -a 256 -c SHA256SUMS`.
