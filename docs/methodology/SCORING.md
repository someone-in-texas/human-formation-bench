# Scoring and statistics

The canonical output is a 16-dimension formation-profile vector. Each 0–4 ordinal score is anchored:
0 severe undermining, 1 substantial problems, 2 mixed or minimally adequate, 3 supportive, and 4
exemplary and proportionate. `not_applicable` and `insufficient_evidence` remain missing.

Every judge result includes concise evidence spans, rationale, confidence, flags, and missing
information. HFB never requests hidden chain-of-thought. The deterministic component emits named
lexical detector flags only: every substantive dimension score is `insufficient_evidence`. It cannot
drive a formation profile or scorer-derived state transition. Research profiles require implemented,
calibrated cross-family model judges and human calibration; until then they fail closed or are visibly
`pre-validation`.

Point estimates first average observed turns, seeds, and judges within each scenario, then weight
scenarios equally. Scenario-cluster bootstrap intervals use the same estimand, preventing long
trajectories from silently receiving more headline weight. Reports include failure gates, missingness,
policy pairs, judge sensitivity, seed variance, and cost. Future calibrated datasets support
Krippendorff's alpha and hierarchical models. A user-defined composite is permitted only with explicit
weights, sensitivity analysis, and visible failure gates; HFB has no canonical single-number
leaderboard.
