# SOC 2 2026 — Performance Case
**For:** Adam Duman, Security Program Manager
**Review period reference:** January 2027 annual review
**Last updated:** September 10, 2026

This is a living document. Update it as the audit closes out and as post-audit improvements take shape.

---

## Executive Summary

I independently designed and executed Earnest's SOC 2 Type II 2026 evidence collection — a process that at most organizations requires a dedicated team of 3-5 people across GRC, IT, and Engineering. I replaced what was historically a manual, screenshot-heavy, stakeholder-chasing process with an API-driven, programmatic evidence collection pipeline that completed 75% of 100 evidence tickets in under two weeks, with minimal support from other teams.

This is not how GRC is normally done. The standard playbook is: send spreadsheets to engineering, wait weeks for screenshots, chase people on Slack, manually upload files, hope nothing is stale by the time the auditor looks at it. I wrote the playbook differently.

---

## What I Did

### Built an API-Driven Evidence Collection Pipeline
Instead of asking engineers to take screenshots, I pulled evidence directly from source systems via their APIs:

- **AWS** (7 services): VPCs, security groups, NACLs, ACM certificates, ALB TLS configs, RDS backups, EventBridge rules — all from the production account (075440130607), programmatically verified
- **GitHub** (3 endpoints): PR populations across 6 in-scope systems (388+ PRs), branch protection evidence, code developer listings, repository permissions
- **Okta** (5 endpoints): Password policies, MFA configs, authenticators, sign-on policies, SCIM provisioning data for Files.com (discovered Okta manages Files.com — nobody knew)
- **CrowdStrike Falcon** (6 endpoints): Vulnerability scanning data (58K open, 256K closed across 3,874 hosts), sensor/prevention policies, user management, role definitions
- **Confluence** (CQL search): Policy sweep across 6 spaces with 42 search terms, mapped to control requirements
- **Jira Cloud** (REST API v3): Ticket management, evidence upload, bulk transitions, population pulls, lifecycle data extraction for 140 access provisioning tickets

Every API pull includes inline IPE (Information Produced by Entity) — query parameters, row counts, timestamps, pagination confirmation. This is auditor-ready evidence on first pull, not evidence that needs to be re-explained later.

### Produced Evidence That Tells Stories, Not Just Checks Boxes
The difference between "here's a CSV" and "here's why this satisfies the control" is the difference between a clean audit and a findings-heavy one.

- **Unified Vulnerability Management Packet**: Combined CrowdStrike runtime scanning, CI/CD pipeline tooling (Grype, Kyverno), and the Keystone remediation program into a single narrative document with 13 supporting files. Three complementary pillars, one coherent story.
- **Post-Incident Reviews (3)**: Wrote formal PIRs from raw Slack incident channel exports. Consistent format: Summary, Timeline, Root Cause, Impact (CIA), Containment/Resolution, Remediation Actions, Lessons Learned. The three incidents tell a maturity story: bug bounty catch with same-day remediation, detection pipeline working correctly on a false positive, defense-in-depth (SOPS encryption) preventing a data exposure.
- **DBA Login Process Documentation**: Researched and documented the full `gogo-db` → Okta → HashiCorp Vault → ephemeral PostgreSQL credentials authentication flow, including a 25-database production access matrix. Turned an opaque internal tool into auditor-readable evidence.
- **Network Diagram**: Generated a Mermaid-rendered network diagram from live AWS API data — 5 VPCs, 3 EKS clusters, 25 RDS instances, 49 load balancers, 15 peering connections. Not a Visio diagram someone drew from memory — a diagram generated from production state.
- **Control-by-Control Justification Document**: 700+ line document mapping every Baker Tilly evidence request to its ESEC ticket, explaining what was provided and why it meets the control intent. This is the auditor's reading guide.

### Identified and Closed Gaps Before the Auditor Found Them
Ran a systematic gap analysis comparing the 2025 SOC 2 report (91 pages, Baker Tilly) against current evidence:

- Found 5 prior-year exceptions that auditors will focus on — prepared specific evidence and talking points for each
- Identified 4 "Done" tickets where evidence didn't match what the auditor actually asked for (VPC CSVs instead of a network diagram, org-level admins instead of per-tool admin listings, AWS-level TLS instead of per-tool configs)
- Created 6 gap tickets (ESEC-272–277) and closed 5 of them in the same session
- Discovered 8 orphaned production security groups with public ingress — flagged to infra team for remediation before audit review
- Found and documented the Splunk → CrowdStrike SIEM migration (January 2026) that changes how 4+ controls should be evidenced
- Identified control intent mismatches: New Relic is APM not security monitoring (CO.01), CloudWatch/SNS is infrastructure monitoring not user-facing downtime notifications (IT.01)

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

I did the GRC analyst work, the IT operations work, and the engineering work. The only items I delegated were:
- Screenshots that require physical access to admin consoles (Tyler/Gaige — ~10 tickets)
- A video recording of a DBA login (Diwakar Puri — 1 ticket)
- HR-owned documents (background checks, performance reviews — 4 tickets)
- A Jira ticket on another team's board (Dhananjay — 1 ticket)

Everything else — API integrations, evidence packaging, narrative documents, gap analysis, Jira workflow management, auditor communication prep — was me.

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Total ESEC tickets | 100 |
| Tickets completed (as of 9/10) | 75 (75%) |
| Tickets completed by me directly | ~65 |
| Source systems integrated via API | 7 (AWS, GitHub, Okta, CrowdStrike, Confluence, Jira, Kandji) |
| API endpoints used | 25+ |
| Evidence files produced | 100+ |
| Post-incident reviews written | 3 |
| Gap tickets created and resolved | 6 (5 closed same-day) |
| Proactive security findings (orphaned SGs) | 8 |
| Calendar days from start to 75% | ~10 |
| Other team members' time consumed | < 20 hours total estimated |
| Third-party GRC tool cost | $0 (no Vanta, Drata, or consultant spend) |

---

## What This Means for the Business

### Cost Avoidance
- A third-party GRC platform (Vanta, Drata) runs $30K-80K/year for a company Earnest's size
- A SOC 2 readiness consultant engagement runs $50K-150K
- Additional engineering time for evidence collection at other companies: 200-400 hours across multiple engineers
- **Conservative estimate: $80K-200K in avoided cost this audit cycle**

### Risk Reduction
- Proactive gap analysis means fewer surprises during audit fieldwork
- Prior-year exceptions have specific, documented remediation evidence ready
- Control intent mismatches identified and fixed before auditor review — prevents findings that stem from providing the wrong type of evidence
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
- "I replaced manual screenshot collection with API-driven evidence pulls from 7 source systems, producing auditor-ready evidence with inline IPE on first pull."
- "I identified and closed 6 evidence gaps before the auditor found them, including 4 tickets where our evidence didn't match the control intent."
- "I proactively found 8 orphaned security groups with public ingress in production and flagged them for remediation."
- "I wrote 3 formal post-incident reviews from raw Slack data, a unified vulnerability management packet, and a 700-line control-by-control justification document."
- "I saved the company an estimated $80K-200K by not requiring a GRC platform, consultant, or significant engineering time."
- "I have a concrete plan to turn this into an automated, continuous evidence collection platform for next year."

---

## Update Log

| Date | Update |
|------|--------|
| 2026-09-10 | Initial draft — 75% complete, 10 days into collection |
| | *Add entries as audit progresses and closes* |
