# SOC 2 2026 — Performance Case
**For:** Adam Duman, Security Program Manager
**Review period reference:** January 2027 annual review
**Last updated:** September 14, 2026

This is a living document. Update it as the audit closes out and as post-audit improvements take shape.

---

## Executive Summary

I designed and drove Earnest's SOC 2 Type II 2026 evidence collection — replacing what was historically a manual, screenshot-heavy process with an API-driven, programmatic evidence collection approach. As of September 11, 2026 (with 19 days remaining in the audit period), 34 of 43 parent evidence tickets are complete (79%), most of which I completed directly using Claude Code on AWS Bedrock as my primary tooling. The remaining 9 tickets are either waiting on auditor sample selection, pending from other teams (IT screenshots, HR de-identified lists), or items I still own (tabletop exercise, pentest report). My boss was out all week — I ran this solo.

The prior year's audit relied on manual screenshots, meetings, and last-minute justifications. This year I shifted to pulling evidence programmatically from source system APIs, packaging it with control-intent narratives, and building the audit story proactively rather than reactively.

On September 14, with the submission largely assembled, I spent a full session auditing my own work rather than adding to it — and found five defects in evidence already with Baker Tilly, including one that had left a selected sample quarter on the highest-risk control with no evidence identified at all. All five were fixed and disclosed to the auditor in a dated revision block. That pass is the part of this year's work I'd point to first: the pipeline is the visible improvement, but the willingness to go back over finished work and publish what's wrong with it is what makes the evidence trustworthy.

---

## What I Did

### Built an API-Driven Evidence Collection Pipeline
Where systems have APIs, I pulled evidence programmatically rather than asking engineers to take screenshots:

- **AWS CLI** (7 services): VPCs, security groups, NACLs, ACM certificates, ALB TLS configs, RDS backups, EventBridge rules — all from the production account (075440130607)
- **GitHub CLI + API**: PR populations across 6 in-scope systems (1,441 PRs), code developer listings, repository permissions
- **Okta API**: Password policies, MFA configs, authenticators, sign-on policies, SCIM provisioning data. Discovered that Files.com is fully managed via Okta SCIM — this wasn't documented anywhere and resolved two open tickets.
- **CrowdStrike Falcon API**: Vulnerability scanning data (58K open, 256K closed across 3,874 hosts), sensor/prevention policies, user management. Some endpoints (Detections, Incidents) returned 404 due to API scope limitations — worked around with narrative documents cross-referencing actual incidents.
- **Confluence REST API**: Policy sweep across 6 spaces with 42 search terms, mapped to control requirements
- **Jira Cloud REST API v3**: Ticket management, evidence upload, bulk transitions, population pulls, lifecycle data extraction for 140 access provisioning tickets

Not every system has an API — Kandji (device management), Google Workspace admin, and UniFi (wireless) require manual screenshots from IT staff. About 10 tickets are delegated specifically because they need admin console access I don't have.

Every API pull includes inline IPE (Information Produced by Entity) — query parameters, row counts, timestamps, pagination confirmation.

### Produced Evidence That Tells Stories, Not Just Checks Boxes
The difference between "here's a CSV" and "here's why this satisfies the control" is the difference between a clean audit and a findings-heavy one.

- **Unified Vulnerability Management Packet**: Combined CrowdStrike runtime scanning, CI/CD pipeline tooling (Grype, Kyverno), and the Keystone remediation program into a single narrative document with 13 supporting files. Three complementary pillars, one coherent story.
- **Post-Incident Reviews (3)**: Wrote formal PIRs from raw Slack incident channel exports. Consistent format: Summary, Timeline, Root Cause, Impact (CIA), Containment/Resolution, Remediation Actions, Lessons Learned. The three incidents tell a maturity story: bug bounty catch with same-day remediation, detection pipeline working correctly on a false positive, defense-in-depth (SOPS encryption) preventing a data exposure.
- **DBA Login Process Documentation**: Researched and documented the full `gogo-db` → Okta → HashiCorp Vault → ephemeral PostgreSQL credentials authentication flow, including a 25-database production access matrix. Turned an opaque internal tool into auditor-readable evidence.
- **Network Diagram**: Generated a Mermaid-rendered network diagram from live AWS API data — 5 VPCs, 3 EKS clusters, 25 RDS instances, 49 load balancers, 15 peering connections. Not a Visio diagram someone drew from memory — a diagram generated from production state.
- **Control-by-Control Justification Document**: 700+ line document mapping every Baker Tilly evidence request to its ESEC ticket, explaining what was provided and why it meets the control intent. This is the auditor's reading guide.

### Identified and Closed Gaps Before the Auditor Found Them
Ran a systematic gap analysis comparing the 2025 SOC 2 report (91 pages, Baker Tilly) against current evidence:

- Identified the 5 prior-year exceptions that auditors will focus on (LS.07 access reviews with 3 sub-exceptions, LS.02 access provisioning, LS.04 termination, LS.15 admin access, EL.03 incident response training). Prepared specific remediation evidence for 4 of 5: LS.02 has 140 provisioning tickets with full lifecycle data, LS.04 has a 40-ticket offboarding population from Jira, LS.15 has per-tool admin listings for all 4 tools, and **LS.07 now has complete evidence for both selected sample quarters** (see below). EL.03 does not appear to have a dedicated ESEC ticket and may need follow-up.
- Identified 4 "Done" tickets where evidence didn't match what the auditor actually asked for (VPC CSVs instead of a network diagram, org-level admins instead of per-tool admin listings, AWS-level TLS instead of per-tool configs, EventBridge instead of per-tool scheduled jobs). Created 6 gap tickets (ESEC-272–277) and closed 5 of them in the same session. ESEC-274 (per-tool scheduled jobs) is still open, waiting on Dhananjay.
- Discovered 8 orphaned production security groups with public ingress — flagged to infra team for remediation before audit review
- Documented the Splunk → CrowdStrike SIEM migration (January 2026) on every affected control, since the auditor's request list still references "Splunk"
- Identified control intent mismatches where our evidence didn't match what the control was actually asking for: New Relic is APM not security monitoring (CO.01 — supplemented with CrowdStrike NGSIEM narrative), CloudWatch/SNS is infrastructure monitoring not user-facing downtime notifications (IT.01 — flagged as a gap that may need follow-up)

### Audited My Own Submitted Evidence and Corrected It Before the Auditor Saw It
On September 14 I stopped collecting and reviewed what had already been submitted. That pass found five defects in evidence already in Baker Tilly's hands. All five were disclosed in a dated revision block in the justification document rather than quietly amended.

- **Recovered a sample quarter that had no evidence.** The LS.07 access-review package identified only the Q4 2025 cycle. Baker Tilly selected **two** sample quarters. The Q1 2026 cycle — performed May–July 2026 — is the Q2 2026 evidence, because Earnest's review cycles were named retroactively (a cycle is named for the quarter whose entitlements were reviewed and performed the following quarter). The original package had mislabeled those three tickets as "continuations of the Q4 2025 cycle," which left the Q2 2026 sample quarter with **nothing identified at all** — on the control with three prior-year sub-exceptions and the highest audit risk of any in scope. Rebuilt the package from the worksheet's own hyperlinks rather than a keyword search: worksheet, coverage summary (46 of 47 in-scope systems reviewed and attested), a 30-item remediation inventory with the identify → approve → execute → confirm chain for each, full Jira ticket text, and IPE explaining the naming convention.
- **Removed out-of-period rows from two change populations.** The GitHub query had been bounded on the collection date rather than the observation window end, putting 15 September 2026 PRs into populations scoped to close 8/31. Trimmed SLO 388→376 and Servicing 508→505, with itemized excluded-row files attached alongside each population so the exclusion is auditable rather than a row count that silently dropped.
- **Replaced the wrong artifact on LS.13 Req 96** — the raw 104 MB per-message export had been submitted where the request asked for monthly summary reports.
- **Reopened two tickets that had been closed prematurely** (ESEC-182/184), which were marked Done while the auditor sample selection they depend on hadn't arrived — making the tracker read as complete when two 9/30 deliverables hadn't started.
- **Caught that our email security evidence described half the mail path, and that our own retention argument was too broad.** The submitted DNS evidence named Valimail as Earnest's inbound mail gateway. It isn't — `whois mxrecord.io` returns Registrant Organization "Area 1 Security," registrar Cloudflare, and both MX hosts resolve into Cloudflare's netblock. Valimail is real but does SPF/DMARC, not inbound scanning. Two consequences: everything filed under LS.13 covered the Google Workspace layer only, with no evidence at all for the first-line scanner; and the position I had already argued to Baker Tilly — that the October and December 2025 sample months "cannot be produced" — was true of Google's six-month retention and possibly false of Earnest's mail path, because Area 1 retains detection telemetry on its own schedule. I posted a supplementing comment narrowing my own claim before the auditor had a chance to test it, and said plainly that if Area 1 holds those months the request is answerable rather than deniable. It would have been easier to leave the argument standing. An unobtainability claim that a second data source contradicts costs more credibility than the gap it was covering.

Also found and fixed things that were nobody's finding yet: a live PagerDuty integration key in submitted evidence, internal negotiating strategy sitting in a document the auditor reads, 14 duplicate attachments, a misnamed access review cycle ticket, an attested system with no review ticket, a system still listed in-scope eight months after it was decommissioned, and the fact that the entitlement worksheet has no row named for the SLO platform — the system with two of the three prior-year LS.07 sub-exceptions.

The duplicate scan is worth calling out for the right reason: the *first* run reported zero duplicates, because Jira's search endpoint truncates at `maxResults` with no error and had returned 100 of 277 issues. I didn't accept the clean result — the audit tickets live in the 139–280 range and a scan that saw none of them should not have come back clean. Paginating properly surfaced the real 12.

### Challenged Unnecessary Evidence Requests
- Closed CM.09 Req 40 (Security Update PowerPoints) as N/A with a formal justification document explaining it was a Navient parent-company reporting artifact, not evidence of control operation
- Closed LS.01 Req 44 (Files.com password settings) as N/A after discovering Files.com authenticates entirely through Okta SAML/SCIM — local passwords don't exist
- Curated the incident population to 3 fully-documented incidents rather than dumping raw alert data that would create unnecessary auditor questions
- Chose Jira offboarding tickets over Okta deprovisioned users as the termination population — process evidence over end-state, with deliberate exclusion of noisy edge cases

### Did It Essentially Solo
The standard SOC 2 evidence collection at a company Earnest's size involves:
- A GRC analyst managing the project and chasing stakeholders (1 FTE)
- An IT operations person pulling configs and screenshots (0.5 FTE)
- Engineering support for API access, system documentation, and technical evidence (0.5 FTE)
- Often a third-party consultant or GRC platform (Vanta, Drata, etc.) to automate collection

I handled the GRC analysis, the technical evidence collection, and the engineering work to pull it via API. Items I delegated were things I couldn't do myself:
- Screenshots from admin consoles I don't have access to (Tyler/Gaige — G-Suite, ITO, UniFi — ~5 tickets, plus a consolidated request ticket)
- Email security summaries and notification configs from the email admin (Tyler Yates — 2 tickets)
- Asset disposal records and confirmation (Jason/Tyler — 3 tickets)
- A video recording of a DBA login process (Diwakar Puri — 1 ticket; I wrote the documentation, he recorded the demo)
- HR-owned documents: background checks, contractor population, performance reviews (HR team — 6 tickets)
- Airflow/Looker scheduled job evidence (Dhananjay — 1 ticket via DNA-14432)
- Q3 2026 access review execution (Jeff White — feeds into existing tickets but I'm not running the review itself)

That's roughly 18 tickets delegated out of 100. The rest — API integrations, evidence packaging, narrative documents, gap analysis, Jira workflow management, population curation — I did directly.

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Total ESEC tickets | 100 |
| Tickets completed (as of 9/11) | 34 of 43 parent tickets (79%) |
| Tickets completed by me directly | ~57 (remaining delegated to IT, HR, engineering) |
| Source systems integrated via API | 6 (AWS, GitHub, Okta, CrowdStrike, Confluence, Jira) |
| API endpoints used | 25+ |
| Evidence files produced | 244 (across all evidence subdirectories) |
| Post-incident reviews written | 3 |
| Gap tickets created and resolved | 6 (5 closed same-day) |
| Proactive security findings (orphaned SGs) | 8 |
| Defects found in my own submitted evidence, disclosed and corrected | 5 |
| Arguments I made to the auditor and then narrowed myself | 1 (LS.13 retention — scoped to Google Workspace once a second scanning layer was found) |
| Scoping arguments I talked myself out of before submitting | 1 (CO.08 — 5 devices that looked test/non-prod turned out to be production laptops on a check of the population) |
| Evidence files staged for Drive, each SHA-256 verified | 334 (308 Jira attachments, 308/308 hash match) |
| Prior-year exceptions with dedicated remediation evidence | 4 of 5 |
| Calendar days from start to 79% | ~11 |
| Other team members' time consumed | < 20 hours total estimated |
| Third-party GRC tool cost | $0 (no Vanta, Drata, or consultant spend) |
| Claude Code (AWS Bedrock) cost | ~$TBD (update when final invoice available) |

---

## Tooling Investment: Claude Code via AWS Bedrock

The primary tooling cost for this audit was Claude Code running on AWS Bedrock (Anthropic Claude Opus). This is the AI coding assistant that I used to write API integrations in real-time, parse and transform evidence data, generate narrative documents, manage Jira workflows, and execute the entire evidence pipeline interactively across multi-hour sessions.

**What Claude Code replaced:**
- Writing one-off Python scripts manually for each API integration
- Manually formatting CSVs, writing IPE documentation, composing narrative evidence
- Researching API documentation, debugging authentication flows, troubleshooting pagination
- Drafting Jira comments in Atlassian Document Format (ADF)
- Cross-referencing the 2025 audit report against current evidence for gap analysis

**What it didn't replace:**
- GRC judgment: what to pull, what to exclude, how to frame evidence for auditors, when to challenge an evidence request
- Stakeholder management: knowing who owns what, how to ask for things, when to push back
- Audit strategy: curating populations, limiting auditor exposure, building narratives that tell a maturity story
- Domain expertise: understanding SOC 2 control intent, prior-year exception context, system architecture

**The economics:**
| Item | Cost |
|------|------|
| Claude Code (Bedrock Opus, ~6 sessions so far) | ~$TBD (update with actual Bedrock invoice) |
| Third-party GRC platform (not purchased) | $30K-80K/year (typical Vanta/Drata pricing at Earnest's scale) |
| SOC 2 readiness consultant (not engaged) | $50K-150K (typical for first-time or remediating orgs) |

We didn't purchase a GRC platform or engage a readiness consultant. We also didn't require significant engineering time for evidence collection — the delegated items are mostly admin console screenshots and HR documents, not engineering effort. The Bedrock cost is the primary tooling investment, and it will be a fraction of any of those alternatives.

---

## Year-Over-Year Comparison: 2025 vs. 2026

### 2025 Audit — By the Numbers (from actual evidence folder)

The 2025 evidence folder tells the story better than any summary could:

| Metric | 2025 | 2026 |
|--------|------|------|
| **Total evidence files** | 761 | 275 |
| **Screenshots (PNG)** | 401 (53%) | 13 (5%) |
| **PDFs (Jira exports, docs)** | 259 (34%) | 3 (1%) |
| **Word docs (manual write-ups)** | 55 (7%) | 0 |
| **CSVs (structured data)** | 36 (5%) | 160 (58%) |
| **Markdown (narrative docs)** | 0 | 28 (10%) |
| **JSON (API config exports)** | 0 | 22 (8%) |
| **IPE files** | 2 (both screenshots) | 45 text files with inline query params, row counts, timestamps |
| **Narrative/justification documents** | 0 | 28 (including 700+ line control-by-control justification) |
| **Per-person sample folders** | 45 (manual folder per auditor-selected individual) | 0 (structured CSVs with population data) |
| **"Follow-Up" / "Archive" / "Hold" folders** | 10 (evidence of auditor back-and-forth and staging delays) | 0 |
| **Auditor coordination screenshots** | 13 (screenshots of people's calendar availability for audit meetings) | 0 |

**What the 2025 numbers reveal:**

More than half the evidence was screenshots. The access management controls (LS.02, LS.04, LS.06) were handled by creating individual named folders for each sampled person — "Anthony Sharp", "Alicia Berry", "Chris Vensko" — and manually collecting Jira ticket PDFs, Okta screenshots, and offboarding screenshots into each folder. Chris Vensko alone had 6 files across multiple "Additional Access" PDFs. There were 17 individual microservice screenshots just for the CM.02 change tracking control. The auditor coordination folder contained 13 screenshots of people's calendars — evidence of the meeting-driven approach to collecting evidence.

The "Hold for Now" folders (LS.02, LS.07, CO.07, LS.14) and multiple "Follow-Up #2" directories show evidence that wasn't ready when the auditor asked, required rework, or was being staged because it needed explanation. The Word docs were ad-hoc clarification notes: "Change Request Clarifications.docx", "SoD Explanation.docx", "LS.06 Notes for Audit Team", "Backup Failure Alert Notes.docx" — written reactively when the auditor couldn't understand what they were looking at.

There were exactly 2 IPE files — both screenshots. No structured IPE, no query parameters, no row counts, no timestamps. No markdown narrative documents. No justification docs. No proactive gap analysis.

**Result: 5 exceptions.**

### 2026 Audit — What Changed

| Dimension | 2025 | 2026 |
|-----------|------|------|
| **Primary evidence format** | Screenshots (401 PNGs) | Structured data (160 CSVs, 22 JSONs) |
| **Evidence generation** | Manual: open admin console, take screenshot, save to folder | Programmatic: API call → parse → CSV + inline IPE |
| **IPE** | 2 screenshot-based IPE files | 45 text files with query parameters, row counts, timestamps, pagination assertions |
| **Narrative context** | 0 documents — auditor received raw files without explanation | 28 markdown docs including 700+ line justification document, 3 PIRs, unified vuln management packet, DBA process documentation |
| **Sample evidence** | Per-person named folders (45 folders with manually gathered PDFs + screenshots) | Pre-built population CSVs with full lifecycle data; auditor selects from structured list |
| **Auditor communication** | Word docs written reactively after auditor questions ("Change Request Clarifications.docx", "SoD Explanation.docx") | Proactive justification document explaining every piece of evidence before auditor asks |
| **Gap management** | "Hold for Now" staging folders; "Follow-Up #2" rework directories | 6 gaps self-identified, 5 closed same-day, 0 "hold" or "rework" folders |
| **Audit coordination** | 13 calendar availability screenshots (scheduling meetings to explain evidence) | ADF-formatted Jira comments with structured context; no evidence-explanation meetings needed |
| **People involved** | Multiple: calendar screenshots show Tyler Yates, Jason Kennedy, Diwakar Puri, Bronte Baer, Seth Robertson, Ricardo Avila, Greg Kohl, Gin Yoshidome, DJ/Dhananjay, John Coburn, Cas, Paula Sloup all scheduled for audit meetings | Primarily one person (Adam Duman); ~18 tickets delegated for admin screenshots and HR docs |
| **Source systems via API** | 0 | 6 (AWS, GitHub, Okta, CrowdStrike, Confluence, Jira) |
| **Exceptions** | 5 | TBD — positioned for fewer based on proactive remediation of 3 of 5 prior-year findings |

### What Changed — The Core Shift

The 2025 audit was a **document-collection exercise**: schedule meetings with 13+ stakeholders, ask people for screenshots, create per-person folders, upload what you get, write Word doc clarifications when auditors push back, stage incomplete evidence in "Hold for Now" folders while chasing people for follow-ups. 761 files, 401 screenshots, 55 Word docs. Five exceptions.

The 2026 audit is a **data engineering problem**: pull structured data from source systems via API, package it with control-intent narratives, curate what the auditor sees, pre-build populations for immediate sample selection, and build the audit story proactively. 275 files, 160 CSVs, 28 narrative documents, 45 IPE files. One person, 11 calendar days to 79%.

The file count went *down* by 64% while evidence quality went *up* — because structured data replaces redundant screenshots. One CSV with 388 PRs replaces dozens of individual PR screenshots. One population CSV with 140 access tickets replaces 12 per-person folders with manually gathered PDFs. The evidence is more complete, more verifiable, and comes with inline proof of how it was generated.

Claude Code on AWS Bedrock is what made this transformation possible at solo-operator speed. Instead of spending days writing Python scripts for each API, debugging authentication, and formatting output, I executed API integrations interactively in real-time — writing, testing, and deploying evidence pulls within the same session. What would have taken a week of scripting per source system took hours. The AI handled the mechanical work (API calls, data transformation, ADF formatting, CSV generation, IPE documentation) while I focused on what actually requires GRC expertise: audit strategy, evidence curation, narrative framing, stakeholder management, and knowing what not to show the auditor.

The 2025 audit coordination folder — 13 screenshots of people's calendars — is maybe the most telling artifact. That folder represents the old model: schedule meetings to explain evidence. In 2026, the evidence explains itself.

---

## What This Means for the Business

### Cost Avoidance
- No third-party GRC platform purchased (Vanta, Drata typically $30K-80K/year at Earnest's scale)
- No SOC 2 readiness consultant engaged (typically $50K-150K)
- Minimal engineering time consumed — delegated items are admin screenshots and HR documents, not engineering effort
- Claude Code Bedrock cost: ~$TBD (update with actual invoice — expected to be a small fraction of the alternatives)

### Risk Reduction
- Proactive gap analysis means fewer surprises during audit fieldwork
- 3 of 5 prior-year exceptions have specific remediation evidence ready; LS.07 (highest risk, 3 sub-exceptions) is partially addressed with Q4 2025 review complete and Q3 2026 in progress
- Control intent mismatches identified and corrected before auditor review (CO.01, CM.09, LS.01) — prevents findings that stem from providing the wrong type of evidence. IT.01 flagged as a gap that still needs resolution.
- Narrative documents give the auditor context, reducing the back-and-forth that extends audit timelines

### Efficiency Gain
- API-driven evidence is reproducible — next year's pull is a re-run, not a restart
- IPE is built into the collection process, not bolted on after
- Evidence is already in auditor-ready format with control justifications
- Population data is structured for immediate auditor sample selection

### Organizational Knowledge
- The `soc2-evidence-planner` repository documents the full process, lessons learned, and API gotchas
- The WORKFLOW.md file is a complete runbook for next year's audit
- The control-by-control justification document is a reusable template
- System migrations (Splunk → CrowdStrike), tool integrations (Files.com via Okta SCIM), and infrastructure architecture are now documented in evidence artifacts that outlast the audit

---

## The Vision: What Next Year Looks Like

This year proved the concept. Next year, I want to operationalize it.

### Phase 1: Automated Evidence Collection Platform (Q1 2027)
Build reusable collector modules for each source system:
- AWS collector: VPCs, SGs, NACLs, ACM, ALB, RDS, Backup, EventBridge — parameterized by account, region, date range
- GitHub collector: PR populations, branch protection, org members, team permissions — parameterized by org, repos, date range
- Okta collector: Policies, users, apps, SCIM provisioning — all with inline IPE
- CrowdStrike collector: Vuln data, policies, users, host inventory
- Jira collector: Ticket populations, lifecycle data, attachment management

Each collector outputs structured evidence (CSV + IPE) ready for upload. `--dry-run` support for validation before execution.

### Phase 2: Continuous Evidence Collection (Q2 2027)
Instead of collecting evidence at audit time, collect it continuously:
- Monthly automated pulls for controls that require sample-month evidence
- Quarterly entitlement review data pre-staged for Jeff White's team
- Real-time incident tracking that auto-generates PIR templates from Slack channel activity
- Population data maintained year-round so auditor sample selection is same-day

### Phase 3: Auditor Self-Service (Q3 2027)
Reduce the auditor communication overhead:
- Pre-built evidence packages with justification narratives
- Structured population data with filter/sort/sample capabilities
- Dashboard showing evidence freshness and coverage gaps
- Direct auditor access to curated evidence (not raw system data)

### The Pitch
Year 1 (2026): Proved a single GRC engineer can execute the entire evidence collection with API-driven tooling, producing higher-quality evidence than the traditional screenshot-and-spreadsheet approach.

Year 2 (2027): Operationalize it — automated collectors, continuous evidence, auditor self-service. Turn SOC 2 from a 4-week fire drill into a standing process that runs itself.

Year 3 (2028): Package it. If this works at Earnest, it works anywhere. The `soc2-evidence-planner` repo is already public. The collector modules, evidence templates, and workflow patterns are reusable.

---

## Talking Points for Review Conversation

- "I ran the SOC 2 evidence collection essentially solo — a process that typically requires 2-3 FTEs across GRC, IT, and Engineering."
- "I replaced manual screenshot collection with API-driven evidence pulls from 6 source systems, producing auditor-ready evidence with inline IPE on first pull. Some systems still require manual screenshots because I don't have API access or the system doesn't expose one."
- "I used Claude Code on AWS Bedrock as a force multiplier — writing API integrations, transforming data, and generating narrative documents in real-time. The Bedrock cost is modest compared to the GRC platform, consultant, and engineering time we avoided."
- "Compared to 2025: fewer people involved, faster completion, better evidence quality, proactive gap closure instead of reactive audit findings. Last year had 5 exceptions. This year I've identified all of them and pre-addressed the ones I can — 3 of 5 have specific remediation evidence ready, LS.07 is in progress, and I've flagged the remaining gap."
- "I identified and closed 6 evidence gaps before the auditor found them, including 4 tickets where our evidence didn't match the control intent."
- "I proactively found 8 orphaned security groups with public ingress in production and flagged them for remediation."
- "I wrote 3 formal post-incident reviews from raw Slack data, a unified vulnerability management packet, and a 700-line control-by-control justification document."
- "I have a concrete plan to turn this into an automated, continuous evidence collection platform for next year — the tooling I built this year is the prototype."
- "This is what GRC engineering looks like. Not spreadsheets and screenshots — API-driven evidence collection with AI-assisted execution. I want to build this into a repeatable capability for Earnest."

---

## Update Log

| Date | Update |
|------|--------|
| 2026-09-10 | Initial draft — 75% complete, 10 days into collection |
| 2026-09-11 | Updated to 79% (34/43 parent tickets). Closed CM.02, LS.08, EL.04 contractor/IPE, CO.07. Background check population (50), contractor population (47), performance review population (264+193) delivered. Pentest timing confirmed (~2 weeks). Boss out all week — ran solo. Identified systemic log retention gap as audit risk. CTO skip level delivered with full risk assessment. Processed Gaige Rogers bulk delivery (4 zip files from IT-21925) — closed 9 tickets (ESEC-167, 196, 197, 199, 207, 208, 209, 210, 221). Wrote formal pushback argument against Baker Tilly for LS.13 email security sample-month evidence (platform-enforced control). 9 tickets remain open: 2 Adam-owned (tabletop + pentest), 2 evidence assembly (LS.02 + LS.14), 2 Tyler/Gaige (ITO password + UniFi notifications), 2 auditor sample selection (background checks + perf reviews), 1 living doc. |
| 2026-09-14 | **Self-audit and correction pass** (5 defects) — reviewed submitted evidence instead of collecting new. Found and disclosed 4 defects in evidence already with Baker Tilly: LS.07 Q2 2026 sample quarter had no identified evidence (rebuilt the Q1 2026 package from worksheet hyperlinks — worksheet, coverage summary, 30-item remediation inventory, ticket exports, IPE); SLO/Servicing change populations included 15 out-of-period rows (trimmed 388→376 and 508→505 with excluded-row sidecars, consolidated 1,456→1,441); LS.13 Req 96 had the raw 104 MB export instead of the monthly summaries; ESEC-182/184 closed while awaiting auditor sample selection (reopened). Also: scrubbed a live PagerDuty integration key from submitted evidence; removed internal negotiating strategy from the auditor-facing justification doc; found and removed 14 duplicate attachments after catching that Jira's search endpoint had silently truncated the first scan to 100 of 277 issues; renamed a misnamed access-review cycle ticket (IT-21950); surfaced Plaid attested with no review ticket, Splunk still listed in-scope post-CrowdStrike, and no SLO-named row in the entitlement worksheet. Rewrote LS.07 in the justification doc, added a revision block, and updated the runbook with the root causes. **Fifth defect found late in the session:** the LS.13 DNS evidence misattributed Earnest's inbound mail gateway to Valimail — it is Cloudflare Area 1 Security (verified via whois/dig), which means LS.13 evidenced only the Google Workspace layer of a two-layer inbound path, and the Oct/Dec 2025 "cannot be produced" argument already posted to ESEC-196/197 was too broad. Rewrote the DNS file with two-layer stack, attribution basis and inline IPE; posted a supplementing comment narrowing my own claim; recorded the Material Security / Abnormal Security procurement as explicitly out-of-period. Re-uploaded corrected docs to ESEC-196/197/198/278. |
| 2026-09-14 | **Drive staging and CO.08 close-out.** Staged the entire submission for Google Drive in the same control→request hierarchy the auditor already navigates: 334 files, 83 MB, 36 controls, 108 request folders, with a manifest carrying a SHA-256 per file. All 308 Jira attachments verified twice — against Jira's reported size on download, then re-hashed on disk: 308/308 match, zero failures. The 16 requests with no evidence got self-documenting files rather than being silently omitted, split between `CLOSURE_RATIONALE.txt` (deliberate N/A or non-query IPE) and `_PENDING - <blocker>.txt` naming whose move it is; writing them surfaced two contradictions in already-closed tickets (ESEC-234's IPE describing a query the population never came from, ESEC-235's "172 incidents" against a true count of 3). Closed CO.08 Req 136 out from one end-user screenshot to full per-blueprint coverage: 6 of 6 blueprints, 354 of 354 devices, evidenced primarily from the FileVault library item's own Assignment Maps list. Talked myself out of the fast close — the 3 remaining blueprints looked like test/non-prod (one is literally named "Harry's Test blueprint"), but pulling the members showed 5 production MacBook Pros belonging to named individuals, one to a member of Earnest IT. Closed on the enforcement argument instead, which covers all 354 without needing an exclusion, and disclosed the difference in evidence form. |
| | *Add entries as audit progresses and closes* |
