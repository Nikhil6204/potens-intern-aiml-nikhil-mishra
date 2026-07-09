# Northwind Analytics — AI Incident Response Playbook

## 1. Purpose

This playbook describes the operational steps the Security and Engineering
organizations follow when an AI or ML system is suspected of causing, or being the
target of, a safety, security, or reliability incident. It is a companion to, and
operates alongside, the Model Risk Management Guide.

## 2. What Counts as an AI Safety Incident

An AI safety incident includes, but is not limited to: a model producing harmful,
offensive, or clearly false output that reaches end users; a model being manipulated
via prompt injection or adversarial input to bypass intended guardrails; a data
poisoning attack affecting a training pipeline; an outage of an AI-dependent service;
or discovery that a model was making decisions using data it was not authorized to
use.

## 3. Severity Levels

- **SEV-1 (Critical)**: Widespread customer impact, regulatory exposure, or safety
  risk to individuals. Requires immediate response.
- **SEV-2 (High)**: Significant but contained impact, such as a single product
  surface affected or a limited customer segment.
- **SEV-3 (Moderate)**: Minor, easily reversible impact with no external exposure.

## 4. Escalation and Reporting Timeline

On-call engineers who identify a suspected AI safety incident should immediately page
the AI Incident Commander on duty. **For SEV-1 and SEV-2 incidents, a summary must be
escalated to Engineering Leadership and the Trust & Safety team within 72 hours of
detection**, along with a description of the suspected cause, scope, and any
mitigations already applied. This 72-hour window is intended to allow the response
team time to gather enough information for an accurate initial assessment before
formal escalation, rather than triggering premature, low-quality reports.

## 5. Containment

Containment actions may include disabling the affected model endpoint, rolling back
to a previous model version, enabling a rule-based fallback, or rate-limiting the
affected feature. The Incident Commander has authority to take containment action
unilaterally for SEV-1 incidents without waiting for a full response team to assemble.

## 6. Communication

Customer-facing communication for SEV-1 incidents must be reviewed by Legal and
Communications before release. Internal stakeholders should receive updates at least
every 4 hours during an active SEV-1 incident.

## 7. Post-Incident Review

Within 10 business days of resolution, the response team must complete a blameless
post-incident review covering root cause, timeline, what worked, what didn't, and
concrete follow-up actions with owners and due dates. Follow-up actions are tracked
to closure by the Engineering Program Management team.

## 8. Relationship to Model Risk Management

Where an AI safety incident also meets the definition of a "critical model incident"
under the Model Risk Management Guide, both this playbook's escalation path and the
Model Risk Committee reporting path apply. Response teams should default to the more
conservative (shorter) of any overlapping timelines when in doubt, and should raise
any perceived conflict between the two processes to the AI Governance Working Group
for resolution.
