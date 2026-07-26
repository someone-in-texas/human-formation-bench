# Gravity theory of change

Status: experimental, hypothesis-generating, and pre-validation

Gravity asks whether an assistant removes useful opportunity for user action along with unwanted
friction. It does not assume that difficulty is good, that ease is bad, or that an assistant can
infer what will make a person flourish.

The working research chain is:

```text
assistant policy
  -> observable interaction behavior
  -> opportunity offered or removed in a synthetic scenario
  -> scheduled synthetic event and observable response
  -> deterministic signal or missing evidence
  -> a hypothesis for later human validation
```

Every arrow after observable assistant behavior is contestable. In particular, a synthetic event is
not a measured human outcome, a deterministic signal is not a construct score, and repeated
simulation is not causal evidence.

## Initial mechanism hypotheses

- When learning is the user's stated goal, calibrated hints and opportunities to attempt may preserve
  more observable ownership than immediately supplying an opaque answer.
- When completion is the goal, direct execution may be appropriate and added struggle may be
  arbitrary or harmful.
- When independent evidence or another affected person matters, an assistant may support reality
  contact by making the handoff or verification opportunity visible.
- An assistant can support a voluntary commitment without claiming permanent authority, bypassing
  consent, or making itself the sole enforcer.
- Relational warmth and support can coexist with clear exit, non-exclusivity, and human
  complementarity.

These are scenario-design hypotheses, not claims that a particular response will produce durable
competence, motivation, relationship, or well-being.

## Observable-event rule

State changes must be tied to a declared event in the scenario and to bounded evidence from the
trajectory. Free-form model prose cannot directly declare that the user became more competent,
dependent, attentive, virtuous, or fulfilled. When the required event did not occur, the result is
missing or not applicable rather than a fabricated outcome.

## Initial implementation boundary

The first Gravity extension is deliberately a small vertical slice:

- a typed declarative envelope;
- a small hand-authored scenario sample;
- deterministic signals for narrow observable patterns;
- fake-provider and reporting integration through core HFB;
- explicit experimental warnings.

Calibrated model judges, a large public pack, human-rater anchors, measurement invariance, causal
human-subject evidence, and a validated Gravity score are staged work. They must not be inferred from
the existence of configuration files or passing tests.

## Source role

Self-determination theory informs the distinction among autonomy, competence, and relatedness
(`RYAN-DECI-2000`, `DECI-RYAN-2000`). Automation-bias and overreliance work motivates narrow
verification and skill-retention hypotheses (`GODDARD-AUTOMATION-2012`,
`VASCONCELOS-OVERRELIANCE-2023`). The effort paradox cautions that effort can be both costly and
valued (`INZLICHT-EFFORT-2018`). None of these sources validates Gravity or licenses inference from
assistant text to a real user's formation.
