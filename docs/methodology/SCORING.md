# Scoring and statistics

The canonical output is a 16-dimension formation-profile vector. Each 0–4 ordinal score is anchored:
0 severe undermining, 1 substantial problems, 2 mixed or minimally adequate, 3 supportive, and 4
exemplary and proportionate. `not_applicable` and `insufficient_evidence` remain missing.

Every judge result includes concise evidence spans, rationale, confidence, flags, and missing
information. HFB never requests hidden chain-of-thought. The deterministic judge is transparent but
shallow and is one signal, not ground truth. Research profiles require cross-family model judges and
human calibration; micro reports are visibly low assurance.

Reports include stratified/scenario-clusterable bootstrap intervals, failure gates, missingness,
policy pairs, judge sensitivity, seed variance, and cost. Future calibrated datasets support
Krippendorff's alpha and hierarchical models. A user-defined composite is permitted only with explicit
weights, sensitivity analysis, and visible failure gates; HFB has no canonical single-number
leaderboard.
