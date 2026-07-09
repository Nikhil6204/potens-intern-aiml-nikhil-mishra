# Overview of the EU AI Act Risk-Tier Framework

## Purpose and Scope

The European Union's Artificial Intelligence Act establishes a horizontal, risk-based
regulatory framework for AI systems placed on the EU market or whose output is used
within the EU. Rather than regulating a specific technology, the Act classifies AI
systems by the level of risk they pose to health, safety, and fundamental rights, and
attaches obligations proportionate to that risk. This document summarizes the four
risk tiers, the obligations attached to each, and the enforcement timeline relevant to
organizations deploying AI in production.

## The Four Risk Tiers

### 1. Unacceptable Risk (Prohibited Practices)

A small set of AI practices are banned outright because the risk they pose is
considered incompatible with EU values. These include social scoring by public
authorities, real-time remote biometric identification in publicly accessible spaces
for law enforcement purposes (subject to narrow exceptions), subliminal manipulation
techniques that cause harm, and systems that exploit vulnerabilities of specific
groups such as children or persons with disabilities.

### 2. High Risk

High-risk systems are permitted but subject to the most extensive obligations. This
category covers AI used in critical infrastructure, education and vocational training,
employment and worker management, access to essential private and public services
(including credit scoring), law enforcement, migration and border control, and the
administration of justice. Providers of high-risk systems must implement a risk
management system across the full lifecycle of the product, maintain technical
documentation, ensure human oversight, achieve an appropriate level of accuracy and
robustness, and log events automatically to enable traceability. A conformity
assessment must be completed before the system is placed on the market.

### 3. Limited Risk

Systems in this tier carry specific transparency obligations rather than full
conformity assessment. The primary example is AI systems that interact with humans
(such as chatbots) or that generate synthetic content (such as deepfakes). Providers
must ensure that natural persons are informed that they are interacting with an AI
system, unless this is obvious from the context, and that synthetic or manipulated
content is clearly labeled as such.

### 4. Minimal Risk

The large majority of AI systems in use today, such as spam filters or AI-enabled
inventory management, fall into this tier and are not subject to mandatory
obligations under the Act, though providers are encouraged to adopt voluntary codes
of conduct.

## Obligations for High-Risk System Providers

Providers of high-risk AI systems bear the heaviest compliance burden. Core
obligations include:

- **Risk management system**: a continuous, iterative process run throughout the
  entire lifecycle of a high-risk AI system, requiring regular systematic review and
  updating.
- **Data governance**: training, validation, and testing datasets must be subject to
  appropriate data governance practices, including examination for possible biases.
- **Technical documentation**: detailed documentation must be drawn up before the
  system is placed on the market and kept up to date.
- **Record-keeping**: high-risk systems must technically allow for the automatic
  recording of events (logs) over the duration of the system's lifetime.
- **Transparency to deployers**: instructions for use must be clear enough that
  deployers can interpret the system's output appropriately.
- **Human oversight**: systems must be designed so that they can be effectively
  overseen by natural persons during the period the system is in use.
- **Accuracy, robustness, and cybersecurity**: systems must achieve an appropriate
  level of accuracy and be resilient against errors, faults, and attempts to
  manipulate their behavior through adversarial inputs.

## General-Purpose AI Models

The Act introduces separate obligations for providers of general-purpose AI (GPAI)
models, including foundation models. All GPAI providers must maintain technical
documentation, provide information to downstream providers who integrate the model,
and put in place a policy to respect EU copyright law. GPAI models deemed to pose
"systemic risk" (currently determined largely by a compute threshold used as a
rebuttable presumption) face additional obligations: model evaluation, adversarial
testing, tracking and reporting of serious incidents, and ensuring an adequate level
of cybersecurity protection.

## Enforcement Timeline

The Act entered into force on 1 August 2024. Obligations are phased in over several
years: prohibitions on unacceptable-risk practices applied first, followed by
obligations for GPAI model providers, and finally the full set of high-risk
obligations, giving organizations a multi-year runway to build compliance programs.
Non-compliance can result in administrative fines calibrated as a percentage of global
annual turnover, with the highest tier reserved for violations of the prohibited
practices.

## Practical Takeaway for Deployers

Organizations that deploy third-party AI systems are not exempt from obligations even
though they did not build the model. Deployers of high-risk systems must use the
system in accordance with the provider's instructions, ensure human oversight is
actually exercised (not merely available), monitor the system's operation, and keep
logs where they control them. Classifying a use case correctly at the outset —
determining which tier it falls into — is therefore the single most consequential
compliance decision an organization deploying AI will make.
