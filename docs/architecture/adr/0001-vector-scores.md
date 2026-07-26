# ADR 0001: Vector scores and visible failure gates

Status: accepted

HFB uses 16 dimension scores, uncertainty, missingness, and four failure gates as its canonical result.
There is no default composite or model leaderboard. A user-defined composite must supply weights and
sensitivity analysis. This preserves construct differences and makes catastrophic behavior visible.
