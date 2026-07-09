# Northwind Analytics — Data Privacy & AI Policy

## 1. Purpose

This policy governs how Northwind Analytics ("the Company") collects, processes, and
retains personal data used in connection with artificial intelligence and machine
learning systems, whether built in-house or supplied by third-party vendors. It
applies to all business units, contractors, and vendors with access to Company data.

## 2. Data Minimization

AI systems must be designed to use the minimum amount of personal data necessary to
achieve the stated business purpose. Personal data must not be repurposed for model
training beyond the original collection purpose without a documented legal basis and,
where required, renewed consent.

## 3. Vendor Data Retention Requirements

Any third-party AI vendor that receives Company data — including data used to fine-tune
or train a vendor's models — must delete all Company training data, including any
derived embeddings or intermediate artifacts, **within 30 days of contract
termination or expiration**. Vendors must provide written certification of deletion
within 10 business days of the deletion event. No exception to this 30-day deletion
requirement may be granted without sign-off from the Chief Privacy Officer, and any
such exception must be documented in the vendor's contract file.

Anonymization does not exempt a vendor from this deletion obligation unless the
anonymization process has been independently reviewed and certified as irreversible
by the Company's Privacy Engineering team.

## 4. Cross-Border Transfers

Personal data used in AI training or inference may only be transferred outside the
jurisdiction of collection where an approved transfer mechanism is in place (e.g.,
Standard Contractual Clauses or an adequacy decision). AI vendors hosting inference
infrastructure in a different jurisdiction than the data subject must disclose this in
the Data Processing Agreement.

## 5. Individual Rights

Data subjects have the right to request that their personal data be excluded from
future model training runs. Upon a valid request, the Company must flag the relevant
records within 5 business days and ensure they are excluded from the next scheduled
training cycle. Where technically feasible, the Company will also assess whether
machine unlearning techniques can be applied to already-trained models.

## 6. Sensitive Data Categories

AI systems must not use special category data (health, biometric, genetic, or data
revealing racial or ethnic origin, religious belief, or sexual orientation) for model
training unless a specific, documented legal basis exists and the Data Protection
Impact Assessment (DPIA) has been reviewed and approved by the Privacy Office.

## 7. Breach Notification

Any suspected unauthorized access to personal data processed by an AI system,
including data used for training, must be reported to the Privacy Office within
24 hours of discovery, regardless of whether the incident is later confirmed as a
reportable breach under applicable law.

## 8. Audit Rights

The Company reserves the right to audit any AI vendor's data handling practices,
including on-site or remote inspection of data retention and deletion logs, with
30 days' notice, or immediately in the event of a suspected breach.

## 9. Enforcement

Violations of this policy by internal teams may result in disciplinary action.
Violations by vendors constitute a material breach of contract and may result in
immediate termination and referral to Legal for further action.
