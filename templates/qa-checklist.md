# SOC 2 Evidence Collection — QA Checklist

> Use this checklist before submitting any evidence to the auditor. Run through the universal checks for every item, then the type-specific checks based on evidence type.

---

## QA Process

### Three Review Gates

| Gate | Who | When | Focus |
|------|-----|------|-------|
| Self-Review | Evidence collector | Same day as collection | Completeness, correct item, readable |
| Peer Review | Another team member | Within 24 hours | Fresh eyes, catches obvious gaps |
| Final Review | Audit coordinator | Within 48 hours | Standards compliance, consistency, submission-ready |

### QA Workflow

```
Evidence Collected
    ↓
Self-Review (collector checks own work)
    ↓ Pass
Peer Review (colleague spot-checks)
    ↓ Pass               ↓ Fail
Final Review         → Feedback to collector → Re-collect → Self-Review
    ↓ Pass
Mark "QA Approved"
    ↓
Add to submission package
```

---

## Universal Checks (All Evidence)

Run these for EVERY piece of evidence regardless of type:

### Date Verification
- [ ] Evidence falls within the audit period: [Start Date] - [End Date]
- [ ] If point-in-time: captured as recently as possible (within 30 days of submission)
- [ ] If periodic: covers the exact period requested (not broader, not narrower)
- [ ] No future dates (evidence from after the audit period end date is invalid)

### Completeness
- [ ] Addresses the FULL auditor request (re-read the exact request text)
- [ ] If multi-part request: all parts addressed
- [ ] If multi-system request: all systems covered (or tracked as separate tasks)
- [ ] Nothing obviously missing that the auditor would follow up on

### File Quality
- [ ] File is readable and not corrupted
- [ ] Text is legible (screenshots not blurry, exports not truncated)
- [ ] File format appropriate (PNG for screenshots, Excel for data, PDF for documents)
- [ ] File naming follows convention: `[ControlID]_[Type]_[System]_[Description]_[Date].[ext]`
- [ ] File uploaded to correct folder in shared evidence drive

### Sensitivity
- [ ] No unnecessary PII exposed (redact SSNs, personal email addresses, etc.)
- [ ] No credentials/secrets visible (API keys, passwords, tokens)
- [ ] No internal-only URLs that would confuse the auditor
- [ ] Redactions noted (don't silently redact — state what was removed and why)

### Traceability
- [ ] Can clearly identify WHICH control/request this evidence satisfies
- [ ] Source system is identifiable (URL, breadcrumb, system name visible)
- [ ] Evidence is self-contained (auditor can understand it without additional context)

---

## Type-Specific Checks

### Policy Documents

- [ ] Document is the version that was EFFECTIVE during the audit period
- [ ] Effective date or version date is visible
- [ ] If updated mid-period: both versions provided with transition date
- [ ] Approval evidence present (signature, approval email, change log entry)
- [ ] Content actually addresses the specific control being tested
- [ ] Document is complete (no "TBD" sections, no placeholder text)
- [ ] Owner/department identified
- [ ] Review/update cadence mentioned (shows it's maintained)

### Population Reports

- [ ] Date range matches EXACTLY what was requested
- [ ] All items included (no inappropriate filtering)
- [ ] Report parameters clearly documented (what filters were used)
- [ ] Total row count explicitly visible or stated
- [ ] System generation timestamp visible (screenshot for IPE)
- [ ] Export is complete (check last row — no truncation at system limits)
- [ ] Column headers are clear and meaningful
- [ ] Paired IPE documentation exists and is linked
- [ ] Format is sortable/filterable by auditor (Excel/CSV preferred over PDF)
- [ ] If items span multiple systems: all systems represented or documented as separate tasks

### IPE (Integrity of Processing Evidence)

- [ ] Links to the specific population/report it supports
- [ ] Screenshot shows query parameters/filters at time of generation
- [ ] Screenshot shows system clock at generation time
- [ ] Row count in screenshot matches row count in exported file
- [ ] Person who generated the report is identified
- [ ] Spot-check validation documented (2-3 items manually verified)
- [ ] Any discrepancies between system display and export are explained
- [ ] All attachments referenced in IPE doc are actually present

### Screenshots

- [ ] System clock (date AND time) clearly visible
- [ ] Full URL or navigation breadcrumb visible (identifies system and location)
- [ ] The specific setting/config the auditor asked about is visible and readable
- [ ] Taken from PRODUCTION environment (not staging, dev, or sandbox)
- [ ] Full window captured (not cropped to remove helpful context)
- [ ] If multiple screenshots for one request: all are present and numbered
- [ ] User context visible where relevant (who is viewing this)
- [ ] PNG format (no JPEG compression artifacts)
- [ ] Captured within last 30 days (as recent as possible)

### Configuration Exports

- [ ] Exported from PRODUCTION environment
- [ ] Shows the specific setting/rule the control requires
- [ ] Timestamp or export date documented
- [ ] Source system clearly identified
- [ ] Sensitive values appropriately redacted (but settings values preserved)
- [ ] Brief context provided (what does this configuration enforce?)
- [ ] If JSON/XML: formatted readably (not minified single-line)

### Sample Evidence

- [ ] Matches the EXACT item the auditor selected (correct person, date, transaction)
- [ ] Shows the control OPERATED (not just that the process exists)
- [ ] Full lifecycle visible:
  - [ ] Initiation/trigger (request, event, scheduled occurrence)
  - [ ] Action taken (review, approval, implementation)
  - [ ] Completion (closed, resolved, confirmed)
- [ ] If approval required: approval is visible from an AUTHORIZED person
- [ ] If timing requirement exists: timestamps demonstrate requirement was met
- [ ] If remediation required: evidence shows remediation completed (not just identified)
- [ ] Context sufficient (auditor can follow the story without additional explanation)
- [ ] No confusion with similar items (clearly THIS specific sample, not a different one)

### Reports

- [ ] Covers the exact time period requested (correct months, quarters, etc.)
- [ ] Generated from the authoritative source system
- [ ] Parameters/filters visible or documented
- [ ] Complete (not summarized unless summary was specifically requested)
- [ ] If "sample months" specified: providing the correct months (check auditor's date selections)
- [ ] Generation timestamp visible
- [ ] If regenerated for a past period: noted in IPE documentation

### Contracts

- [ ] Fully executed (all parties signed)
- [ ] Effective dates cover the audit period
- [ ] Correct legal entities named (not parent company if subsidiary is audited)
- [ ] Relevant sections identifiable (security, SLA, compliance terms)
- [ ] If amended: original + amendments both provided
- [ ] Commercial redactions noted if applied

---

## Control-Specific Checks

These additional checks apply to specific control families:

### Change Management (CM)
- [ ] Change tickets show development → testing → approval → implementation
- [ ] Approval is from someone OTHER than the developer (separation of duties)
- [ ] Testing evidence is present (not just a "tested" checkbox)
- [ ] Implementation date matches the population (item was deployed when claimed)

### Access Management (LS — Provisioning)
- [ ] Access request shows formal approval before access was granted
- [ ] Approver was authorized to approve (manager, system owner, etc.)
- [ ] Access granted matches what was approved (no scope creep)
- [ ] Timing: access granted AFTER approval (not before)

### Access Management (LS — Termination)
- [ ] Termination date is established (HR confirmation, last day)
- [ ] Network/primary access removed within required timeframe (often 1 business day)
- [ ] Application access removed within required timeframe (often 30-45 days)
- [ ] ALL in-scope systems covered (not just the easy ones)
- [ ] If access was removed BEFORE the deadline: still compliant

### Access Reviews (LS)
- [ ] Review was performed during the required frequency (quarterly, semi-annual)
- [ ] Review covers ALL users (not just a subset)
- [ ] Issues found during review have corresponding REMEDIATION evidence
- [ ] Remediation was completed (not just identified)
- [ ] Reviewer is appropriate (system owner, security team, not the users themselves)

### Incident Response (CO)
- [ ] If incidents occurred: full lifecycle evidence (detection → response → resolution)
- [ ] If NO incidents: confirmation from 2+ independent individuals
- [ ] Confirmation is explicit and covers the exact date range
- [ ] If incidents occurred: response followed documented procedure

### Vulnerability Management (IT)
- [ ] Scan reports cover all in-scope systems
- [ ] Scan frequency matches policy (monthly, quarterly, etc.)
- [ ] Findings have associated tickets/tracking
- [ ] Remediation evidence shows findings being addressed (not just logged)
- [ ] Reports are from the correct sample months (check auditor's date selections)

### Backup & Recovery (IT)
- [ ] Backup listings cover ALL in-scope systems
- [ ] Backup schedule matches policy
- [ ] Failure evidence shows: detection → notification → resolution
- [ ] If no failures: document that (but auditors will usually find SOME)

---

## Submission Packaging

Before each deadline, package evidence into a structured submission:

### Folder Structure
```
SOC2_[Year]_[Deadline]_Submission/
├── 00_Index_and_Mapping.[xlsx/md]
├── 01_Policies/
├── 02_Populations/
├── 03_Screenshots/
├── 04_Configurations/
├── 05_IPE/
├── 06_Reports/
├── 07_Contracts/
├── 08_Samples/
└── README.txt
```

### Index Document

Create a mapping file that connects each auditor request number to the specific evidence file(s):

| Request # | Control | Description | Evidence File(s) | Notes |
|-----------|---------|-------------|-----------------|-------|
| 26 | CM.01 | SDLC Policy | 01_Policies/CM01_Policy_SDLC_v3.2.pdf | |
| 27 | CM.02 | Change Population | 02_Populations/CM02_Population_SLO_2026-09-08.xlsx | Split by system |
| 28 | CM.02 | IPE for Changes | 05_IPE/CM02_IPE_SLO_2026-09-08.md + .png | |

### README Template
```
SOC 2 [Year] Evidence Submission — [Deadline Date]

Audit Period: [Start] - [End]
Submitted by: [Your Name], [Title]
Submission date: [Date]

FOLDER STRUCTURE:
- 00_Index: Maps evidence files to request numbers
- 01_Policies: All policy documents
- 02_Populations: Population reports with paired IPE
- 03_Screenshots: Configuration screenshots (organized by control family)
- 04_Configurations: Exported configuration files
- 05_IPE: Integrity of Processing Evidence documentation
- 06_Reports: System-generated reports
- 07_Contracts: Legal agreements
- 08_Samples: Sample evidence (Deadline 2 only)

NOTES:
- All screenshots include system clock as required
- All populations include IPE documentation
- Evidence dates fall within [Start] - [End]
- [Any known gaps or items requiring follow-up]

Contact: [Your email]
```

### Final Submission Checklist
- [ ] Every request number has at least one corresponding file in the submission
- [ ] Index/mapping document is complete and accurate
- [ ] Folder structure is organized and navigable
- [ ] README explains the structure
- [ ] No duplicate files (same evidence referenced from one location)
- [ ] File names are consistent and follow convention
- [ ] Total submission size is reasonable for the delivery method
- [ ] Zip/archive created for upload (if submitting via portal)
- [ ] Confirmation of receipt requested from auditor
