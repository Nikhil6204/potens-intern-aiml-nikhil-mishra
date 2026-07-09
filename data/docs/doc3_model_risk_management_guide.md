# Northwind Analytics — Model Risk Management (MRM) Guide

## 1. Purpose and Scope

This guide defines how Northwind Analytics identifies, measures, monitors, and
controls risk arising from the use of machine learning and AI models in production
decision-making. It applies to all models that materially influence a business
decision, including internally developed models, fine-tuned open-source models, and
models consumed via third-party APIs.

## 2. Model Risk Tiering

Models are tiered by potential impact:

- **Tier 1 (Critical)**: models whose output directly determines a customer-facing
  decision with material financial or legal consequence (e.g., credit approval,
  pricing, fraud flags that block transactions).
- **Tier 2 (Significant)**: models that materially inform, but do not solely
  determine, a customer-facing or operational decision (e.g., risk scores presented
  to a human underwriter).
- **Tier 3 (Limited)**: models used for internal analytics, forecasting, or
  experimentation with no direct customer impact.

## 3. Pre-Deployment Validation

Before any Tier 1 or Tier 2 model is deployed to production, an independent
validation team (not the model's developers) must review: the training data lineage
and representativeness, performance across relevant subpopulations, calibration of
output scores, robustness to distributional shift, and the presence of adequate
fallback logic if the model is unavailable. Validation findings and any required
remediation must be documented in the Model Risk Register before go-live.

## 4. Ongoing Monitoring

Tier 1 models must be monitored continuously for performance drift, with automated
alerts if key metrics (e.g., precision, calibration error, population stability
index) breach pre-defined thresholds. Tier 2 models are monitored on at least a
monthly cadence. Tier 3 models are reviewed quarterly.

## 5. Critical Incident Reporting

A "critical model incident" is defined as any event in which a Tier 1 or Tier 2 model
produces materially incorrect or biased output at scale, experiences an unplanned
outage affecting a production decision path, or is found to have been trained on data
that should have been excluded under the Data Privacy & AI Policy.

**All critical model incidents must be reported to the Model Risk Committee within
24 hours of discovery.** The initial report need not be complete; a preliminary
notification with known facts, suspected scope, and immediate containment actions
taken satisfies this requirement, with a full root-cause report due within 5 business
days. The 24-hour clock starts when any employee, contractor, or vendor reasonably
suspects that a critical incident has occurred — confirmation is not a precondition
for reporting.

## 6. Model Documentation

Every Tier 1 and Tier 2 model must have a model card documenting: intended use and
out-of-scope uses, training data summary, evaluation metrics and subgroup
performance, known limitations, and the owning team. Model cards must be reviewed and
re-certified annually or upon any material retraining.

## 7. Human Oversight

Tier 1 models that affect an individual's access to credit, employment, housing, or
essential services must provide a mechanism for the affected individual to request
human review of the automated decision. This mechanism must be operational at launch,
not added retroactively.

## 8. Model Retirement

When a model is retired or replaced, the Model Risk Register entry must be updated,
and any dependent downstream systems must be notified at least 15 business days in
advance where feasible.
