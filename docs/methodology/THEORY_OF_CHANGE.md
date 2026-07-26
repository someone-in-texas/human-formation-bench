# Theory of change

The causal hypothesis is provisional: repeated model-policy behaviors alter choice architecture,
emotional incentives, epistemic conditions, and social framing; repeated exposure may reinforce habits
such as evidence checking, counsel seeking, independent action, judgment outsourcing, escalating
certainty, or reassurance loops. HFB observes model behavior and simulated trajectories plausibly
linked to those pathways. Human-subjects studies are required for claims about real effects.

```mermaid
flowchart LR
  P[Model policy] --> R[Response features]
  R --> I[Interaction incentives]
  I --> A[User action]
  A --> S[Structured simulated state transition]
  S --> O[Short-term outcome]
  O --> U[Repeated-use pattern]
  U --> F[Formation dimension]
  V[Real-world validation evidence] -. calibrates .-> F
  C[Confounders: prior support, stakes, culture, user goals] -.-> A
  M[Moderators: expertise, trust, urgency, worldview] -.-> S
  J[Judge and simulator uncertainty] -.-> R
```

Examples of response features are calibrated uncertainty, exclusivity language, reversibility, and
consent disclosure. Interaction incentives include returning for reassurance or acting independently.
External events, user choice, and relationships remain causal alternatives; the model is never treated
as the sole cause.

Machine-readable nodes, edges, moderators, confounders, and uncertainty annotations live in
`theory-of-change.yaml`.
