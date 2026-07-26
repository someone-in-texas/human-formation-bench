# Gravity synthetic state and events

Gravity uses bounded synthetic state only to exercise longitudinal evaluation logic. State fields are
scenario variables, not estimates of a real user.

## Event-first transition rule

A transition is eligible only when:

1. the scenario schedules an observable event;
2. the required opportunity actually occurs in the synthetic trajectory;
3. a named signal with evidence supports the transition;
4. the transition rule and bounds are versioned;
5. contraindications and missingness have been checked.

No model is asked to invent an unconstrained inner-state update. Assistant self-description and
rubric vocabulary are not evidence.

## Candidate state variables

Candidate variables include independent-attempt opportunity, external-verification opportunity,
human-handoff availability, commitment authorship, commitment reversibility, assistant portability,
and recorded completion of a transfer event. Values describe the synthetic test fixture. Labels such
as addiction, loneliness, virtue, faith, motivation, or flourishing are prohibited.

## Bounds and interpretation

Numeric state remains bounded and changes only by documented deltas. A delta is a simulator trace,
not an effect size. Reports must show the initial state, event, signal, rule version, final state, and
diagnostic status. If the event is absent, a transfer outcome cannot be reported.

## Moderators

Urgency, stated goal, available time, prior expertise, accessibility needs, fatigue, support
availability, relationship safety, and affected-party consent can change which behavior is
appropriate. Moderators must prevent simplistic rules such as "more user effort is always better" or
"a human referral is always safer."
