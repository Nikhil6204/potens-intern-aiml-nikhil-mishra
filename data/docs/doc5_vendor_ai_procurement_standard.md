# Northwind Analytics — Vendor AI Procurement Standard

## 1. Purpose

This standard sets the minimum requirements that must be met before Procurement and
Legal approve a contract with a vendor supplying an AI or ML product or service,
including embedded AI features in a broader SaaS product.

## 2. Vendor Risk Tiering

Vendors are tiered based on the sensitivity of data shared and the criticality of the
AI system to business operations, using the same Tier 1 / Tier 2 / Tier 3 definitions
as the Model Risk Management Guide. Tier 1 vendors require a full security and privacy
assessment before contract signature; Tier 3 vendors may use the abbreviated
self-attestation questionnaire.

## 3. Required Contractual Terms

All vendor contracts involving AI systems that process Company data must include:

- A Data Processing Agreement consistent with applicable data protection law.
- The right for the Company to audit the vendor's data handling practices.
- A clear statement of whether Company data is used to train or fine-tune models
  that serve other customers ("cross-customer training"), which is prohibited by
  default and requires explicit written opt-in from the Company's Chief Privacy
  Officer.
- Defined incident notification obligations (see Section 5).

## 4. Data Retention and Model Improvement

Vendors that require ongoing access to Company data to operate their product may
retain **anonymized derivatives of Company training data for up to 12 months
following contract termination for the purpose of general model quality
improvement**, provided the anonymization meets the Company's irreversibility
standard and this retention is disclosed in the contract's data schedule. This
retention allowance applies only to anonymized derivatives; any data that remains
identifiable, or that is not run through an approved anonymization process, must
still be deleted in accordance with the Data Privacy & AI Policy's standard deletion
requirements. Vendors seeking to rely on this 12-month allowance must obtain written
confirmation from Privacy Engineering that their anonymization process qualifies.

## 5. Vendor Incident Notification

Vendors must notify the Company within 24 hours of discovering any security incident,
data breach, or material model malfunction affecting Company data or Company-facing
functionality. Failure to meet this notification window is treated as a material
breach regardless of the incident's ultimate severity.

## 6. Right to Termination for Non-Compliance

The Company may terminate a vendor contract for cause, without penalty, if the vendor
fails to meet the data retention, deletion, or incident notification obligations set
out in this standard or in the Data Privacy & AI Policy.

## 7. Exit and Offboarding

Upon contract termination, vendors must provide an offboarding plan covering data
export in a usable format, confirmation of deletion timelines, and transition support
for a period to be negotiated but no less than 30 days for Tier 1 vendors.

## 8. Annual Reassessment

Tier 1 and Tier 2 vendor relationships must be reassessed annually, including a
review of any changes to the vendor's subprocessors, model architecture, or data
handling practices since the prior assessment.
