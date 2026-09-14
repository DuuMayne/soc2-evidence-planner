# SOC 2 Evidence Collection Workflow

How we ran the 2026 SOC 2 Type II evidence collection at Earnest, what worked, what didn't, and how to replicate it.

## Architecture

```
Auditor Request List (.xlsx)
    ↓ parsed into
Jira ESEC tickets (100 tickets across ~35 controls)
    ↓ evidence collected via
Source Systems: AWS, GitHub, Okta, CrowdStrike, Confluence, Kandji, Jira, Google Workspace
    ↓ stored in
Local evidence directories → uploaded to Jira tickets → shared via Google Drive
```

### Key directories
- `~/Downloads/2026 SOC II/evidence/` — all collected evidence, organized by source
- `~/Projects/soc2-evidence-planner/` — templates, workflow docs, this file
- Evidence shared with auditors via Google Drive (not all evidence needs to be in Jira)

### Key tools
- **Jira Cloud API v3** — ticket management, evidence upload, status tracking
- **GitHub CLI (`gh`)** — PR populations, branch protection, code review data
- **AWS CLI** — infrastructure evidence (VPCs, SGs, NACLs, ACM, ELB, RDS, Backup, EventBridge)
- **Okta API** — MFA/SSO policies, authenticators, app provisioning (Files.com, etc.)
- **CrowdStrike Falcon API** — vulnerability scanning, sensor policies, prevention policies, user management
- **Confluence REST API** — policy documentation sweep
- **Python scripts** — inline API calls (no persistent script files, run in Claude Code sessions)

---

## Workflow Phases

### Phase 1: Setup (Week 1)
1. Parse auditor request list (.xlsx) into structured requirements
2. Create Jira epic + tickets using naming convention: `Req {N} - {Type} - {Description}`
3. Set up Jira dashboard with 5 filters for progress tracking
4. Map control families to evidence owners

### Phase 2: Automated Collection (Weeks 1-2)
Run automated pulls in priority order:
1. **Policies (Confluence)** — CQL search across 6 spaces, 42 search terms, map to tickets
2. **Change populations (GitHub)** — PR-based, scoped to observation window
3. **AWS infrastructure** — VPCs, SGs, NACLs, ACM, ALB, EventBridge, RDS backups
4. **Okta configs** — MFA, SSO, authenticators, app provisioning
5. **CrowdStrike** — vulnerability scans, sensor/prevention policies, users, host inventory
6. **Device management (Kandji)** — FileVault, compliance policies

### Phase 3: Stakeholder Chase (Weeks 2-3)
For evidence that requires other teams:
1. Create Jira tickets with clear ADF comments explaining what's needed
2. Send Slack messages for urgency
3. Draft specific ask templates (not generic "please provide evidence")
4. Track who owes what — Jira dashboard "Open No Attachments" filter
5. Create a consolidated IT team ticket (like ESEC-269) with all screenshot requests and a deadline

### Phase 4: Gap Analysis & Remediation (Week 3)
1. Review all open tickets against the auditor request list
2. Identify known gaps (tabletop, pentest, BC/DR) — escalate or plan
3. Re-pull any evidence that was from the wrong source (e.g., wrong AWS account)
4. Update evidence for any infra remediations (e.g., orphaned SG cleanup)
5. Build narrative documents for complex control areas (vulnerability management, incident response)

### Phase 5: Closeout (Week 4)
1. Transition all completed tickets to Done
2. Prepare curated populations for auditor sample selection (9/30 deadline)
3. Share evidence via Google Drive
4. Update this workflow doc for next year

---

## Hard-Won Lessons

### API Gotchas

| System | Gotcha | Fix |
|--------|--------|-----|
| Jira Cloud | `/rest/api/3/search` deprecated → returns 410 | Use `/rest/api/3/search/jql` endpoint |
| Jira Cloud | Pagination is cursor-based (`nextPageToken`/`isLast`), NOT `startAt` | Always use cursor pagination |
| Jira Cloud | Filter sharePermissions need `project.id` not `project.key` | Look up project ID first |
| Jira Cloud | Dashboard gadgets use Forge moduleKeys, not legacy `com.atlassian.jira:gadgets:*` | List available gadgets via API |
| Jira Cloud | Some users can't be assigned to project issues | Add comments naming the intended owner instead |
| GitHub | `gh search prs` rate limits at ~30 req/min | Retry with backoff; some 403s are transient |
| GitHub | Branch protection API returns 404 for non-admins | Use PR review data as proxy evidence |
| GitHub | `mergedAt` not in search JSON fields | Use `updatedAt` or PR detail API |
| AWS | CloudFront `list-distributions` returns empty string, not `{"DistributionList": {"Items": []}}` | Check for empty stdout before JSON parse |
| AWS | Security-dev account has different resources than production | Always verify account with `sts get-caller-identity` |
| AWS | Inspector NOT active in production (075440130607) | Don't rely on it for vuln evidence |
| AWS | Security Hub returns `InvalidAccessException` in production | Not subscribed — can't use |
| AWS | ECR scan coverage mixed (3/6 repos) | Not reliable as primary vuln evidence |
| Okta | API token is session-provided, never stored | User provides at session start |
| CrowdStrike | Combined vuln endpoint (`/spotlight/combined/vulnerabilities/v1`) returns NO severity data | Must use query endpoint for IDs, then `/spotlight/entities/vulnerabilities/v2` for full details |
| CrowdStrike | Zero vulns before November 2025 | Spotlight wasn't active — not a bug |
| CrowdStrike | Zero closed vulns before July 2026 | No remediation happening before Linux fleet onboarded — real data |
| CrowdStrike | Detections/incidents endpoints return 404 | API scope doesn't include those — need different key |
| CrowdStrike | Users API returns no role assignments | Roles managed via Okta SSO, not CrowdStrike native RBAC |
| Slack | App config tokens (`xoxe.xoxp`) only have `identify,app_configurations:read/write` | Need a token with `channels:history`, `channels:read` to read messages |
| macOS | `cp` fails with special characters (Unicode non-breaking spaces) in filenames | Use Python `shutil.copy2(glob.glob(...)[0], dest)` |

### Evidence Strategy

1. **Always use production account for AWS evidence.** We burned a day pulling backup data from security-dev (2 RDS instances) when production had 25 instances and full monitoring.

2. **Limit auditor exposure.** Use observation window filters (`--merged-at`, date ranges in JQL) to scope evidence to exactly the audit period. Don't show them more than they asked for.

3. **GitHub PRs > Jira tickets for change populations.** GitHub captured 388 SLO PRs vs. 107 Jira tickets. PRs are the actual code changes; Jira tickets are work tracking.

4. **IPE is not optional.** Every evidence file needs inline IPE: query parameters, row counts, timestamps, pagination assertions. Build it into collection scripts, not after the fact.

5. **Curate incident evidence manually.** Automated pulls captured 178 items including alerts, bugs, and operational incidents. Auditors should only see incidents with complete PIRs.

6. **Pre-scan for remediation items.** We found 8 orphaned security groups with public ingress. Flagging these to infra early gave them time to clean up before audit review.

7. **Repo-to-product mapping is essential.** Without the "Repo List with Unit Test Coverage" spreadsheet, we couldn't map GitHub repos to auditor-facing product names.

8. **Screenshots are sometimes the only option.** Kandji MDM has no API, G-Suite admin settings need manual capture, Okta MFA prompts need actual login screenshots.

9. **When a system migrates mid-audit-period, lead with the new system.** CrowdStrike replaced Splunk in Jan 2026. All "Splunk" evidence requests answered with CrowdStrike data + migration note. The SaaS model (immutable cloud-hosted logs) is actually a stronger story.

10. **Check Okta for unexpected provisioning.** Files.com turned out to be fully managed via Okta SCIM (SAML 2.0 + push/deactivation/group push) — we didn't know that until we checked. Found 62 users, 30 new in audit period, which resolved two tickets (ESEC-201/202).

11. **Build unified evidence packets for complex controls.** Vulnerability management spanned 3 pillars (CrowdStrike runtime, CI/CD pipeline, Keystone program). A single narrative document with an evidence index is far more effective than loose files.

12. **Slack channel exports are legitimate evidence.** The #keystone-swarm channel export (PDF + structured markdown) provided governance, remediation, verification, and incident response evidence all in one place. Use channel canvases for AI-assisted summaries, but always include the raw export.

### Jira Workflow

- **Transition IDs:** To Do = 21, In Progress = 31, Done = 41, False Positive = 42
- **ADF comments** are critical for stakeholder communication — use panel(), bulletList, heading, inlineCard structures
- **Attachment upload** requires `X-Atlassian-Token: no-check` header and multipart/form-data
- **Rate limit:** 100 req/60s — use sliding window tracker
- **Batch closing pattern:** Transition To Do → In Progress (31) → Done (41) with 0.5s sleep between

### Evidence Directory Structure

```
~/Downloads/2026 SOC II/evidence/
├── aws/
│   ├── backup_monitoring/       # RDS event subs, backup plans, vault notifications
│   ├── backup_production/       # Backup events, no-failures confirmation
│   ├── env_segregation/         # Org accounts, VPCs, resource inventory
│   ├── network_security/        # Security groups, NACLs, detailed rules
│   ├── scheduled_jobs/          # EventBridge rules and targets
│   ├── secure_transmission/     # ACM certs, ALB TLS, CloudFront
│   └── vpn_access/              # VPN security groups (Pritunl)
├── network_security/
│   ├── earnest_network_diagram.md   # Mermaid diagram (all VPCs, EKS, RDS, LBs, VPN)
│   ├── earnest_network_diagram.png  # Rendered PNG
│   └── co06_tls_vendor_documentation.md  # Vendor TLS proof for Airflow, Looker, Files.com
├── confluence/
│   ├── developer_training/      # Training page catalog
│   └── policy_sweep/            # Policy mapping + PDFs
├── crowdstrike/                 # UNIFIED VULN MGMT PACKET
│   ├── 00_VULNERABILITY_MANAGEMENT_PACKET.md  # Lead document — start here
│   ├── SOC2_Keystone_Evidence_Canvas.pdf       # CC7.1/CC7.2 control mapping
│   ├── Keystone_Swarm_Channel_Export.pdf        # 20-page Slack export
│   ├── Keystone_Upgrade_Dependencies_Canvas.pdf # Roadmap + target services
│   ├── keystone_swarm_channel_screenshot.png    # Visual corroboration
│   ├── keystone_swarm_channel_export.md         # Structured/searchable export
│   ├── vulnerability_summary.csv                # Counts by severity/platform
│   ├── vulnerability_open_sample.csv            # 400 open vulns (full detail)
│   ├── vulnerability_scan_sample_months.csv     # 100 vulns (Dec 2025, Jun 2026)
│   ├── sensor_update_policies.csv               # 14 auto-update policies
│   ├── prevention_policies.csv                  # 14 prevention policies
│   ├── prevention_policy_settings.json          # 213KB detailed config
│   ├── crowdstrike_users.csv                    # 18 console users (basic)
│   ├── crowdstrike_users_with_roles.csv         # 18 users with Okta SSO note
│   ├── crowdstrike_role_definitions.csv         # 81 available roles (reference)
│   └── IPE_documentation.txt                    # IPE for all CS API pulls
├── database_access/
│   └── ls08_dba_login_process.md                # gogo-db → Okta → Vault → ephemeral creds flow
├── files_com/
│   ├── files_com_okta_users.csv                 # 62 users via Okta SCIM
│   ├── files_com_new_accounts_audit_period.csv  # 30 new accounts in period
│   ├── files_com_change_population.csv          # 11 PRs from file-transfer-service
│   ├── files_com_change_population_ipe.txt      # IPE for change population
│   └── IPE_documentation.txt                    # IPE for Okta API pull
├── github/
│   ├── *_change_population.csv  # Per-product change populations
│   ├── pr_review_separation_of_duties.csv
│   └── entitlements_and_devs/   # Org members, teams, permissions
├── incidents/
│   ├── SEC-INC-031126_storyblok_mapi_token_exposure.md   # PIR: bug bounty, MAPI token in JS bundle
│   ├── SEC-INC-081726_suspicious_okta_logins.md          # PIR: impossible travel, ACT contractor VPN (false positive)
│   └── SEC-INC-083126_infra_secrets_exposure.md          # PIR: SOPS-encrypted secrets on public GitHub
├── patching_evidence/
│   ├── cm09_req40_security_update_powerpoints_justification.md  # N/A justification
│   └── ...                      # EKS updates, RDS configs, Jira tickets
├── terminations/
│   ├── it_offboarding_population.csv     # 40 Jira IT offboarding tickets in audit period
│   └── it_offboarding_population_ipe.txt # IPE (JQL, exclusions, row count)
└── vpn_mfa_combined/            # Okta MFA + VPN MFA screenshots
```

---

## Auditor Date Selections (2026)

Pulled from "Date Selections" tab — these determine which samples/months the auditor reviews:

| Type | Selections |
|------|-----------|
| Monthly | October 2025, December 2025, June 2026 |
| Quarterly | Q4 2025, Q2 2026 |
| Daily | 25 specific dates (10/1/25 through 8/12/26) |
| Weekly | 7 specific weeks |

---

## System Migration Notes

### Splunk → CrowdStrike (Jan 2026)
- **When:** CrowdStrike contract signed ~January 2026. Spotlight (vuln scanning) activated November 7, 2025 during eval/onboarding.
- **Impact on evidence:** All "Splunk" evidence requests (CO.02, LS.11) answered with CrowdStrike. The SaaS model gives a stronger audit log protection story (immutable, cloud-hosted, no customer edit access).
- **Gap:** October 2025 has no CrowdStrike Spotlight data. Management response: migration in progress, Grype CI scanning was active.
- **Roles:** All 18 CrowdStrike users authenticated via Okta SSO. No native RBAC assignments — roles managed through Okta. Environment managed by Falcon Complete.

### Files.com Provisioning via Okta
- **Discovery:** Checked Okta on a hunch — Files.com IS fully managed via SCIM (SAML 2.0 + push/deactivation/group push). App ID: 0oa1bicu49zskHd5b0x8.
- **Evidence:** 62 total users, 30 new accounts in audit period. Resolved ESEC-201/202 (LS.14).

---

## Session Log

### September 8, 2026 (Session 1)
**Tickets closed:** ~20+ (batch parent closures, Files.com evidence, CrowdStrike initial pulls)
- Pulled CrowdStrike Falcon Spotlight vulnerability data (58K open, 256K closed, 3,874 hosts)
- Discovered Files.com is managed via Okta SCIM — resolved ESEC-201/202
- Built initial vuln management narrative
- Attempted Slack connection (insufficient token scopes)
- Reviewed all stakeholder comments (Jason Kennedy, Tyler Yates, Gaige Rogers)
- Drafted team update and compared 2025 vs 2026 evidence

### September 8, 2026 (Session 2 — continued)
**Focus:** Keystone program integration into vulnerability management evidence
- User provided full #keystone-swarm Slack channel export (text dump of entire channel history)
- Created structured channel export (`keystone_swarm_channel_export.md`) organized by evidence category
- Rewrote vulnerability management narrative to incorporate Keystone program (governance, tooling, remediation outcomes, verification process)
- Updated narrative with specific channel export cross-references

### September 9, 2026 (Session 1)
**Tickets closed:** ESEC-190, 189, 217, 218, 219, 216, 249, 224, 223, 226, 225 (11 tickets)
- User provided 4 desktop files: Keystone Swarm Export PDF (20 pages), SOC 2 Evidence Canvas PDF, Upgrade Dependencies Canvas PDF, channel screenshot
- Built unified vulnerability management evidence packet (`00_VULNERABILITY_MANAGEMENT_PACKET.md`) combining all sources:
  - CrowdStrike runtime scanning data
  - Keystone program evidence (Slack exports, canvases)
  - CI/CD tooling stack (Grype, Kyverno, dep-swarm-audit)
  - Verification process documentation
  - Known gaps with management responses
  - Auditor Q&A talking points
- Uploaded 13 files to ESEC-252, closed ESEC-251/252/253 (IT.06 complete)
- Pulled CrowdStrike users with RBAC detail — confirmed all 18 users via Okta SSO, roles managed through Okta (not native CS RBAC)
- Uploaded sensor/prevention policies to ESEC-190 (LS.11 anti-malware auto-updates)
- Uploaded user evidence to ESEC-217/218/219 (CO.02 audit log protection) — CrowdStrike cloud-hosted = immutable logs
- Closed bonus parent tickets (IT.01, CO.06, CO.07) that had all children done
- Learned: CrowdStrike replaced Splunk as SIEM in January 2026 (contract signing), not just November 2025 (Spotlight activation)

### September 9, 2026 (Session 2 — continued)
**Focus:** Evidence cleanup, overshare audit, 2025 report comparison, system info completion
- Filtered ESEC-171 access population to 140 in-scope-system tickets (SLO, MMAX, CASHI, SchoolHub, Files.com, Servicing + onboarding)
- Pre-built full lifecycle data for all 140 access tickets (transitions, approvers, completion records, approval comments)
- Uploaded org chart screenshots to ESEC-238, closed EL.01
- Analyzed separation of duties — only 2 true gaps (Tyler Yates Navient transition work), documented explanations for all 7 edge cases
- Ran full overshare/gap audit across all 36 parent + 94 child tickets:
  - Cleaned ESEC-195 (replaced orphaned SG file with clean re-pull from production)
  - Stripped ESEC-150-156 to per-system data only
  - Removed excess attachments from ESEC-162/166/159/160
  - Reopened gap tickets: ESEC-146, ESEC-219, ESEC-216
- Compared 2025 SOC 2 Type II report (Baker Tilly, 91 pages) against current ESEC evidence:
  - Identified 5 prior-year exceptions that auditors will focus on (LS.07 access reviews, LS.02 access provisioning, LS.04 termination, LS.15 data transmission admin, EL.03 incident response training)
  - Found evidence mismatches: LS.08 CyberArk/DBA access, CO.02 logging standard policy, IT.07 CISP patch language, CO.06/CO.07 Files.com encryption+jobs
  - Flagged system description changes: Navient DC migration complete, Splunk→CrowdStrike, Cyxtera DR status
  - Identified ~9 controls with no obvious ESEC ticket (CO.04 wireless, CO.05 threat intel, LS.13 email scanning, etc.)
  - Identified misunderstood control intent for LS.12 (needs network diagram, not just SGs), CM.07/CM.08 (deployment pipeline access)
- Filled blank columns in `Earnest SOC 2 In-Scope System Information.xlsx`:
  - SLO Platform: Ubuntu/EKS/Aurora PostgreSQL 17.7 + PostgreSQL 16.13
  - School Hub: Ubuntu/EKS/PostgreSQL 16.13 (production-encrypted)
  - MMAX: Ubuntu/EKS/Aurora PostgreSQL 17.7 (personal-loans)
  - CASHI: Ubuntu/EKS/Aurora PostgreSQL 17.7 (new-products)
  - Servicing Platform: Windows/RDS managed/SQL Server SE 15.00 (fulfillment-rds-prod-use1)

### September 9, 2026 (Session 3 — continued)
**Focus:** Gap analysis against auditor request list, per-tool admin evidence, ESEC gap ticket creation
- Cross-referenced full auditor request list (Earnest SOC 2 2026 Request List.xlsx) against all ESEC ticket status
- Identified 4 tickets marked Done that don't match what auditor asked for:
  - ESEC-192 (LS.12): Has VPC CSVs but auditor asked for visual network diagram
  - ESEC-224 (CO.06): Has AWS ACM/ALB TLS but auditor asked for per-tool configs (Airflow, Looker, Sign Service, Files.com)
  - ESEC-226 (CO.07): Has EventBridge rules but auditor asked for per-tool scheduled jobs
  - ESEC-205 (LS.15): Has Okta org admins but auditor asked for per-tool admin listings
- Pulled Okta data for all 4 tools:
  - Airflow Production: 61 users, 13 RBAC groups via Okta OIDC. 6 admins in airflow_admin group.
  - Looker: 200+ users via SAML. Groups: All Employees, Data, Credit Ops, etc. No Okta-level admin group — admin managed within Looker.
  - Files.com: 62 users via SAML/SCIM. 8 groups including Dev Admin (21 users), Staging Admin (22 users), Prod Read Only.
  - Sign Service: NOT FOUND in Okta. Only Signadot (CI/CD) and DocuSign variants. Needs clarification.
- Created evidence files: airflow_admin_users.csv, airflow_all_users.csv, airflow_role_structure.csv, files_com_admin_users.csv, files_com_group_structure.csv, IPE_documentation.txt
- Created 6 gap ESEC tickets:
  - ESEC-272: LS.15 per-tool admin listings gap
  - ESEC-273: CO.06 per-tool secure transmission config gap
  - ESEC-274: CO.07 per-tool scheduled jobs gap
  - ESEC-275: LS.12 network diagram gap
  - ESEC-276: CO.02 CrowdStrike IPE (resolved immediately)
  - ESEC-277: Sign Service identification
- Closed tickets: ESEC-219 (CO.02 IPE — uploaded CrowdStrike IPE), ESEC-216 (CO.02 parent), ESEC-276 (resolved)
- Confirmed Looker is default entitlement for all employees (Okta "All Employees" group)
- Found AWS Okta Groups Confluence page documenting default access entitlements

### Status as of September 9, 2026 (end of session 3)
- **Parent tickets:** 22 Done / 14 remaining (+ 6 new gap tickets)
- **Child tickets:** 37 Done / 31 remaining
- **9/11 deadline (configs/policies):** Most config evidence collected; key outstanding items are IT team screenshots (Tyler/Gaige due 9/10), per-tool evidence for CO.06/CO.07/LS.15, network diagram, and policy verification for CISP/logging standard
- **9/30 deadline (samples):** Access provisioning population ready (140 tickets with full lifecycle), change populations ready, incident response / tabletop / BC-DR still pending
- **Highest risk controls:** LS.07 (access reviews — repeat finding risk), IT.08 (tabletop), CO.03 (IRP document), IT.10 (BC/DR plans)
- **New gap tickets needing action:** ESEC-272 (Looker admins from tool owner), ESEC-273 (per-tool TLS), ESEC-274 (per-tool scheduled jobs), ESEC-275 (network diagram from infra team), ESEC-277 (identify Sign Service)

### September 9, 2026 (Session 4 — continued)
**Tickets closed:** ESEC-273, ESEC-275 (2 tickets)
**Ticket created:** ESEC-278 (control-by-control evidence justification write-up)
- Researched vendor documentation for Airflow, Looker, and Files.com to prove TLS is enforced by default at the platform level
- Compiled comprehensive TLS vendor documentation (`co06_tls_vendor_documentation.md`) with specific URLs, direct quotes, and live TLS verification for Looker:
  - **Airflow**: AWS requires TLS 1.2+ (docs.aws.amazon.com/mwaa/infrastructure-security). No opt-out. ALB + ACM certs. Okta OIDC requires HTTPS for OAuth redirects.
  - **Looker**: Google enforces TLS 1.3 on earnest.looker.com. HTTP auto-redirects (301) to HTTPS. HSTS with preload enabled. Certificate from Google Trust Services. SOC 2 certified (cloud.google.com/security/compliance/services-in-scope).
  - **Files.com**: TLS 1.2/1.3 enforced by default. **Cannot be disabled** (files.com/docs/settings-and-usage/security/tls-ssl-security). SFTP uses SSH encryption. Qualys SSL Labs A+ rating. SOC 2 Type II audited annually by Kirkpatrick Price (report issued May 2026).
  - **Sign Service**: Internal ALB with ACM TLS (already covered in ESEC-224).
- Uploaded vendor TLS doc to ESEC-273 with summary comment, transitioned to Done
- Closed ESEC-275 (network diagram gap) — Mermaid diagram was already generated from live AWS data and uploaded in session 3
- Created ESEC-278 to track a comprehensive control-by-control evidence justification document for auditor submission and internal reference

### Status as of September 9, 2026 (end of session 4)
- **Parent tickets:** 25 Done / 11 remaining
- **Gap tickets resolved:** ESEC-272 Done, ESEC-273 Done, ESEC-275 Done, ESEC-276 Done, ESEC-277 Done (5 of 6 gap tickets closed; ESEC-274 still open)
- **Still open gap ticket:** ESEC-274 (CO.07 per-tool scheduled jobs — needs Bronte Baer/Data team for Airflow DAGs, tool owners for Looker/Files.com)
- **9/11 deadline:** IT team screenshots (Tyler/Gaige due 9/10), ESEC-163 (security update PowerPoints), ESEC-186 (DBA login recording), ESEC-274 (scheduled jobs)
- **9/30 deadline:** Sample tickets waiting on auditor selection, LS.07 access reviews (repeat finding risk), CO.09 incidents, IT.08 tabletop, IT.09 pentest, HR items
- **New ticket:** ESEC-278 (control-by-control evidence justification write-up — to be completed after all evidence collected)

### September 10, 2026 (Session 5)
**Tickets closed:** ESEC-232, ESEC-233, ESEC-234, ESEC-235, ESEC-236 (CO.09 complete), ESEC-163 (CM.09 PowerPoints N/A), ESEC-161 (CM.09 parent)
**Tickets created:** DNA-14432 (Dhananjay — Airflow ArgoCD + Looker SLO scheduled reports)
- Wrote third post-incident review: SEC-INC-081726 (suspicious Okta logins / impossible travel from Guatemala IP — confirmed false positive, ACT contractor VPN routing)
- Uploaded all 3 PIRs to ESEC-233 (population) and ESEC-236 (samples), with IPE on ESEC-234, N/A on ESEC-235
- Closed all CO.09 tickets — population is small (N=3) so full population serves as sample
- Closed ESEC-163 (CM.09 security update PowerPoints) as N/A — the PowerPoint was a Navient parent-company reporting artifact, not evidence of control operation. Jira patching tickets (Req 39, ESEC-162) are the actual evidence. Wrote standalone justification document.
- Closed ESEC-161 (CM.09 parent) — both sub-tickets done
- Packaged LS.08 DBA login process documentation: researched meetearnest/gogo-db (Go CLI, Okta → Vault → ephemeral PostgreSQL credentials) and meetearnest/gogodb (deprecated Python predecessor). Pulled Confluence docs: "Database Access - Production DBs" (25 databases with Okta group mappings, updated 9/2/2026) and "How to Request Common Access" (Jira-based access request process). Wrote comprehensive evidence doc covering authentication flow, key security properties, access matrix. Uploaded to ESEC-186 — waiting on Diwakar Puri's video recording to close.
- Created DNA-14432 on Data & Analytics board for Dhananjay Patil: ArgoCD screenshot for Airflow + SLO-only Looker scheduled reports (ESEC-274 dependency)
- Updated evidence_request_justification.md for CO.09 (full rewrite with all 3 incidents, auditor narrative) and CM.09 (Req 40 N/A), re-uploaded to ESEC-278
- HR (Lateesha/Cas) providing EL.04 background checks and EL.06 performance reviews directly. Performance review population may be needed — Baker Tilly will likely want to select their own samples.
- Diwakar Puri working on LS.08 DBA login recording independently.

### Status as of September 10, 2026 (end of session 5)
- **Overall progress:** 72/100 ESEC tickets Done (72%), up from ~65% at start of session
- **Parent controls remaining:** 13 (including epic ESEC-137 and living doc ESEC-278)
- **9/11 blockers (others):** G-Suite + ITO passwords (Tyler/Gaige), UniFi screenshots (Tyler/Gaige), email security summaries (Tyler Yates), per-tool scheduled jobs (Dhananjay via DNA-14432), DBA video (Diwakar)
- **9/11 blockers (Adam):** Tabletop exercise (ESEC-257/258), pentest report (ESEC-260)
- **9/30 items:** 6 sample-selection tickets blocked on Baker Tilly, HR items in progress, termination population needed, asset disposal (Jason/Tyler)
- **Key wins this session:** CO.09 fully closed with 3 well-documented PIRs, CM.09 PowerPoints eliminated as N/A with justification, DBA login process documented with full toolchain explanation

### September 10, 2026 (Session 6 — continued)
**Tickets closed:** ESEC-186 (LS.08 DBA login — video uploaded by Diwakar), ESEC-176 (LS.04 termination population)
- Closed ESEC-186 after user uploaded Diwakar Puri's gogo-db video recording. Documentation was already attached from session 5.
- Re-uploaded justification doc to ESEC-278 (ESEC-146 status fix from prior session wasn't synced)
- Pulled IT offboarding population from Jira: 40 individual offboarding tickets (IT project, issue type "Offboarding Request") during audit period. Excluded 4 edge cases: 1 email access grant (IT-20700), 3 bulk contractor tickets (IT-20060, IT-20968, IT-21046). Uploaded CSV + IPE to ESEC-176, closed.
- Decision: Use Jira IT offboarding tickets as termination population source, not Okta deprovisioned users. Jira captures the offboarding *process* (request, approvals, access removal steps), which is what the auditor tests. Okta is not the universal IDP — it only shows end-state.
- Remaining population gaps for auditor sample selection: ESEC-241 (independent contractor population, HR/Lateesha) and ESEC-243 (performance review population, HR/Cas Varao)

### Status as of September 10, 2026 (end of session 6)
- **Overall progress:** 75/100 SOC 2 ESEC tickets Done (75%), plus 148 non-SOC2 ESEC tickets Done
- **Jira totals:** 223 Done, 2 In Progress, 50 To Do (includes non-SOC2 security tickets)
- **SOC 2 tickets remaining:** ~25 (13 waiting on auditor sample selection or others, 7 waiting on Tyler/Gaige/Tyler Yates, 2 Adam-owned, 3 HR-owned)
- **9/11 deadline blockers (others):** G-Suite + ITO passwords (Tyler/Gaige), UniFi screenshots (Tyler/Gaige), email security summaries + notification config (Tyler Yates), per-tool scheduled jobs (Dhananjay via DNA-14432), asset disposal (Jason/Tyler)
- **9/11 deadline blockers (Adam):** Tabletop exercise (ESEC-257/258), pentest report (ESEC-260)
- **9/30 items:** 7 sample-selection tickets waiting on Baker Tilly, HR items for contractor pop + performance reviews, asset disposal certificates
- **Populations complete:** Change tickets (6 systems), code developers, access provisioning (140 tickets), Files.com new accounts (30), admin listings (4 tools), CrowdStrike users, laptop listing, security incidents (3 PIRs), server backups, backup failures, **termination offboarding (40 tickets)**
- **Populations still needed:** Independent contractors (HR), performance reviews (HR)

### September 11, 2026 (Session 7)
**Tickets closed:** ESEC-141 (CM.02 parent), ESEC-185 (LS.08 parent), ESEC-241 (contractor population), ESEC-242 (contractor IPE), ESEC-274 (CO.07 per-tool scheduled jobs)
- Exported 15 access review Jira tickets (IT project) as full markdown documents — descriptions, comments, status transitions. Caught 2 false positives (IT-19820 access provisioning, IT-20897 Navient GitHub access) and excluded them. Combined doc + individual exports uploaded to ESEC-181 and ESEC-183. Created PDF export checklist for if/when Baker Tilly demands native Jira PDF exports.
- Background check population: Parsed Navient SD15-DataDump report — 575 raw rows across 50 unique Applicant IDs (Bill Code: 42212 - Earnest), orders 10/1/2025 – 8/27/2026. De-identified. Uploaded population CSV, raw source file, and IPE to ESEC-239.
- Contractor population: Parsed Workday report — 47 Earnest LLC contingent workers (21 active, 26 termed). De-identified. Uploaded to ESEC-241, closed.
- Performance review population: Cas Varao confirmed counts — 264 EOY 2025 (full company annual), 193 Mid-Year 2026 (excludes Ops/ICP employees who get quarterly check-ins instead). Wrote population summary, uploaded to ESEC-243. Requested de-identified lists from HR for auditor sample selection.
- Closed ESEC-274 (CO.07 per-tool scheduled jobs): Dhananjay provided 3 screenshots — Airflow ArgoCD deployment (Healthy/Synced), Airflow DAG scheduled run (Success, 8 tasks), Looker scheduled jobs admin. Uploaded with ADF comment covering all 4 tools (Airflow: scheduled, Looker: scheduled but some failures, Files.com: event-driven, Sign Service: event-driven per ESEC-277).
- Looker schedule failure discovery: Dhananjay confirmed scheduled reports to Navient have been failing and nobody on Navient's end complained. Not a SOC 2 control failure — CO.07 is about schedules existing, not SLA monitoring.
- Pentest timing confirmed: Cam says SLO pentest can't start for ~2 weeks. Will kick off before 9/30 but won't have final report or remediation within observation window.
- Updated justification doc: IT.08/IT.09 due dates moved from 9/11 to EOM 9/30, EL.04 section rewritten with population data, open items table updated. Re-uploaded to ESEC-278 multiple times.
- CTO skip level with Meetesh Karia: Delivered updated status (34/43 = 79%), 5 audit risks including new items on log retention and access provisioning sample risk.
- **Gaige Rogers bulk delivery (IT-21925):** Processed 4 zip files containing evidence for 9 ESEC tickets:
  - ESEC-167 (LS.01 G-Suite password): Google password policy screenshot — uploaded and closed
  - ESEC-196 (LS.13 email security): Oct/Dec summaries empty due to 180-day retention gap; Jun 2026 has data. Safety configs, compliance configs, alert sample — uploaded
  - ESEC-197 (LS.13 Gmail safety settings): Uploaded and closed
  - ESEC-199 (LS.13 email notification): Uploaded and closed
  - ESEC-207 (LS.16 asset disposal parent): Archived assets CSV (562 rows), Use of Services letter, Certificate of Destruction (COD #10905)
  - ESEC-208 (LS.16 archived assets): Uploaded and closed
  - ESEC-209 (LS.16 disposal evidence): Uploaded and closed
  - ESEC-210 (LS.16 data destruction cert): Uploaded and closed
  - ESEC-221 (CO.04 wireless security): UniFi firewall rules (2) + WPA configs for Oakland + SLC (4 screenshots) — uploaded and closed
  - Note: ESEC-222 (CO.04 UniFi notification/alert settings) NOT included in delivery — still outstanding
- **LS.13 email security pushback:** Wrote formal pushback argument in justification doc against Baker Tilly demanding sample-month email security summaries. Platform-enforced vendor control — Google scans all email by default, no customer opt-out. Configuration proves design, Google's SOC 2 covers operation. Historical log retention (~180 days) means Oct/Dec 2025 data doesn't exist and never will. Documented in ESEC-278.
- **User entitlements (IT-21925):** 7 onboarding, 4 offboarding, 1 transfer screenshots extracted — staged for ESEC-170 (LS.02) and ESEC-200 (LS.14)

### Status as of September 11, 2026 (end of session 7)
- **Overall progress:** 34 of 43 parent ESEC tickets Done (79%), up from 29 (67%) at start of day
- **Tickets remaining:** 9 open
  - **Adam-owned:** ESEC-256 (IT.08 tabletop, needs scheduling before 9/30), ESEC-259 (IT.09 pentest, vendor starting in ~2 weeks)
  - **Adam — evidence assembly:** ESEC-170 (LS.02 user access provisioning — 140-ticket population ready, need to assemble sample evidence), ESEC-200 (LS.14 data transmission account management — need to compile per-tool evidence)
  - **Tyler/Gaige:** ESEC-164 (LS.01 ITO password settings — G-Suite password done via ESEC-167), ESEC-220 (CO.04 UniFi notification screenshots — ESEC-222 still missing)
  - **Auditor selects:** ESEC-239 (EL.04 background check samples), ESEC-243 (EL.06 performance review samples)
  - **Living doc:** ESEC-278 (justification write-up)
- **Engineering dependency:** NS-534 (app-level change populations + access mods for SLO/CASHI/MMAX/SchoolHub/Servicing) needs follow-up push early next week
- **Populations delivered:** Change tickets (6 systems), code developers, access provisioning (140), Files.com accounts (30), admin listings (4 tools), CrowdStrike users, laptop listing, incidents (3), server backups, backup failures, terminations (40), background checks (50), contractors (47), performance reviews (264 EOY + 193 MY documented, de-identified lists pending from HR)

### September 14, 2026 (Session 8 — self-audit and correction pass)

A review of what had already been submitted, rather than new collection. Found and fixed four
defects in evidence already in the auditor's hands. Everything was disclosed in the justification
doc rather than quietly amended.

**1. LS.07 — the Q2 2026 sample quarter had no identified evidence (most serious finding).**
The Session 7 access-review export was built from the JQL keyword search
`project = IT AND summary ~ "access review"`, got 17 rows, and mislabeled IT-21054/21195/21430 as
"continuations of the Q4 2025 review cycle." They are the **Q1 2026 cycle**, performed
May 13 – Jul 14 2026 — which, under Earnest's then-retroactive naming convention, *is* the Q2 2026
sample-quarter review. As filed, ESEC-181/183 covered only Q4 2025.
- Confirmed the convention with Adam: cycles were named for the quarter whose entitlements were
  reviewed and performed the following quarter; the convention has since flipped. The worksheet
  filename `2026 Q1_2 Entitlement Review Worksheet` encodes it. I had renamed that file to
  "2026 Q1" earlier in the session, stripping the `_2` that proves coverage — restored and verified
  SHA-256 against the source.
- Built the Q1 2026 package from the worksheet's own **hyperlinks** (`cell.hyperlink.target`, cols
  F/I/L → 12 tickets) instead of a keyword search: worksheet, coverage summary, 30-item remediation
  inventory, full ticket exports, ticket CSVs, package IPE. Uploaded to ESEC-181/183.
- Rebuilt `it_access_review_tickets.csv` to a corrected 8-ticket scope pulled live from Jira, with
  an `EXCLUDED` list documenting why each of 10 tickets was dropped. Rewrote
  `access_review_tickets_ipe.txt` (the old one was 853 bytes and wrong on three counts) and
  regenerated `00_ALL_ACCESS_REVIEW_TICKETS.md`, which had been grouping Q4 2025 and Q1 2026 under
  one heading and filing IT-20632 under "Q3 2025 Remediation."
- Per Adam, dropped all Q3 material entirely — neither Q3 cycle is a selected sample quarter. Kept
  the correction of the prior ESEC-181/183 comments but made it non-specific, since leaving a false
  statement in the audit record would be worse than an awkward correction.
- **IT-21950 renamed** from "Q2 2026 Access Review" to "Q3 2026 Access Review" (created 2026-09-11
  alongside every other Q3 2026 cycle ticket). Surfaced it to Adam first; renamed only after
  he confirmed, with an explanatory comment on the ticket.
- New findings disclosed: Plaid attested with no review-ticket link (1 of 46); Splunk still listed
  in-scope post-CrowdStrike; the worksheet is organized by system-of-access so **SLO has no row of
  its own** — the system with two 2025 sub-exceptions.

**2. CM.02 — change populations included out-of-period rows.** The GitHub query used the collection
date as the upper bound (`merged:2025-10-01..2026-09-04`) instead of the observation window end
(8/31/2026). SLO 388→376, Servicing 508→505, consolidated 1,456→1,441. Trimmed with
`*_excluded_out_of_period.csv` sidecars so the exclusion is auditable, patched all three IPEs with a
dated correction block, re-uploaded to ESEC-142/147/148.

**3. LS.13 Req 96 — wrong artifact submitted.** The attachment was the raw 104 MB per-message export,
not the monthly summary reports the request asked for. Replaced with 5 summary files and the June
2026 figures (94,431 scanned / 93,735 spam / 696 phishing / 0 malware; 89,109 external / 5,322
internal; all 30 days present).

**4. ESEC-182/184 reopened.** Both had been closed while the remediation samples they ask for still
await Baker Tilly's sample selection. Reopened to To Do with the 30-item inventory staged.

**Also done:**
- Scrubbed a live PagerDuty integration key from submitted evidence.
- ESEC-197 message-log summary written; auditor Q&A removed from ESEC-252.
- **Duplicate attachment sweep across all 277 ESEC issues / 345 attachments** — the first scan had
  reported zero duplicates because `jira.search()` silently truncates at `maxResults` and returned
  ESEC-1..100 when the audit tickets live at ESEC-139..280. Added `search_all()` with cursor
  pagination; the real 12 duplicates surfaced. 14 deletions executed, each guarded by a live
  byte-size check on the keeper, 0 blocked. Two ESEC-208 files consolidated onto ESEC-208. The
  certificate of destruction was left on **both** ESEC-209 and ESEC-210 since Req 248 and 249 each
  call for it, with a comment saying so.
- Removed the "Pushback on this request" section from the justification doc. The technical argument
  was sound; the framing ("analogous to asking for proof that AWS didn't disable encryption at rest
  on S3") is internal strategy and does not belong in a document the auditor reads.
- Justification doc rerun: LS.07 section rewritten, CM.02 window correction documented, revision
  block added at the top, open-items table updated, dated 9/14.

### Key Audit Risks Identified (Session 7)

1. **Pentest timing (IT.09):** Cam confirmed ~2 weeks before SLO pentest can start. Test will initiate within observation window (before 9/30) but final report and remediation will not be complete. Defensible — "testing performed" — but will likely get noted by Baker Tilly. Similar to last year's finding where the pentest covered the prior period.

2. **Tabletop exercise (IT.08):** Must happen before 9/30. Adam has format and scenario ready but needs participants and a calendar slot. If it slips past the observation window, it's a finding.

3. **Vulnerability management format (IT.06):** Evidence is submitted and the program is genuinely strong (CrowdStrike Spotlight + Grype CI/CD + Kyverno + Keystone governance). Risk is that our remediation story is built around the Keystone program (structured dependency upgrades across service teams) rather than traditional "scan → ticket → fix → rescan" cycles. Baker Tilly may want individual CVE remediation tickets. Narrative packet explains the three-pillar approach but this requires the auditor to engage with a different model than they're used to.

4. **User access provisioning samples (LS.02):** Population of 140 Jira tickets is solid. Risk is at the sample level — when Baker Tilly picks specific users, every sampled provisioning must show documented approval *before* access was granted. Any sample with approval after the fact or missing documentation is a repeat finding on a control they're already watching from the 2025 exception. Engineering populations from NS-534 (SLO/CASHI/MMAX/SchoolHub/Servicing app-level access modifications) are still outstanding.

5. **Log retention gaps (systemic):** Google Workspace audit logs default to 6 months retention. Anything before ~March 2026 is gone. If Baker Tilly picks October/November/December 2025 as sample months for email security (LS.13), those logs don't exist. This isn't just Gmail — any system with <365 days retention has the same gap for the early observation window. The configuration evidence proves the control was operating, but historical output has aged out. Fix for next year: extended retention (Google Workspace Enterprise) or log export pipeline to longer-retention storage (BigQuery, CrowdStrike ingestion).

6. **Baker Tilly evidence format receptivity:** Evidence is objectively stronger than last year but formatted differently from what Baker Tilly is used to (CSVs, API outputs, narrative documents vs. screenshots). Justification document is designed to bridge the gap but auditor may still push back. Three-layer plan: justification doc → supplement with screenshots if needed → escalation via personal contact to BT head of assurance if they reject stronger evidence for format reasons.

---

## For Next Year

1. Build proper collectors for each evidence type — automate the full pull-to-upload pipeline
2. Add `--dry-run` support to all collectors
3. Create a CLI that reads the auditor request list and generates a collection plan
4. Consider storing evidence in S3 with presigned URLs instead of Jira attachments
5. Pre-build IPE templates so they're consistent across all evidence types
6. Start stakeholder outreach 4 weeks before deadline, not 2
7. Maintain the repo-to-product mapping spreadsheet year-round
8. Run the orphaned SG scan monthly, not just during audit prep
9. Get Slack token with proper scopes early — `channels:history`, `channels:read`, `search:read`
10. Build a CrowdStrike evidence collector (auth, vuln pull, policy pull, user pull, IPE generation) as a reusable script
11. Document all system migrations at the time they happen, not during audit season
12. Build unified evidence packets from the start for multi-pillar controls instead of loose files
13. Track the Keystone-style remediation programs year-round — they make the best audit stories
14. **Ensure 365-day log retention on all in-scope systems before the observation window opens.** Google Workspace, Okta, CrowdStrike — check every system's default retention and extend or forward logs where needed. Budget for Google Workspace Enterprise or set up log export pipelines to BigQuery/S3/SIEM. This is an infrastructure ask that needs to happen in Q4 before the next observation period.
14. **Vendor documentation can replace tool-specific screenshots for SaaS TLS evidence.** When the auditor asks for "screenshots of configurations showing secure data transmission," cloud-hosted SaaS tools (Looker, Files.com) enforce TLS at the platform level with no customer opt-out. Official vendor docs citing "cannot be disabled" + live TLS verification (openssl) is stronger than a screenshot of a setting the customer can't change. Compile vendor URLs, direct quotes, and live verification into a single evidence document.
15. **Differentiate between customer-configurable and platform-enforced controls.** For SaaS tools, many security controls (TLS, encryption at rest, log immutability) are platform-enforced — the customer has no "disable" button. This is actually a *stronger* audit story than showing a screenshot of a toggle that could be changed. Cite the vendor's security docs + SOC 2 certification as evidence.
16. **Create a control-by-control justification document early.** A narrative tying each evidence artifact to the control intent and auditor request prevents misunderstanding at review time. Start it as evidence is collected, not at the end.
17. **Close gap tickets immediately when evidence is available.** Gap tickets created during analysis (ESEC-272–277) should be resolved in the same session if the evidence already exists — e.g., ESEC-275 (network diagram) was closeable immediately because the diagram was generated in the prior session but the gap ticket wasn't closed.
18. **Challenge arbitrary evidence requests against the actual control language.** CM.09 asks for monthly patches applied with review and approval. Baker Tilly asked for "Security Update PowerPoints sent to Navient" — that's a parent-company reporting artifact, not evidence the control operated. The Jira patching tickets are the primary evidence. Producing a retroactive PowerPoint would be less credible than the source system records. Write a justification doc and close the ticket as N/A.
19. **Convert raw Slack incident channels into formal PIRs.** Auditors need structured evidence: Summary, Timeline, Root Cause, Impact (CIA), Containment/Resolution, Remediation Actions (owner + status), Lessons Learned. A consistent PIR template across all incidents makes the program look mature. Include false-positive investigations (like impossible travel) — they show the detection pipeline works.
20. **Small incident populations don't need sample selection.** With N=3 incidents, provide the full population as the sample. This avoids the auditor sample-selection round trip and shows completeness.
21. **Document internal tooling as evidence.** For LS.08 (DBA login recording), the `gogo-db` tool's architecture (Okta → Vault → ephemeral credentials) tells a stronger security story than a video alone. Document the authentication flow, credential properties (ephemeral, identity-tied, time-limited, read-only default), and access request process. The video becomes supplementary to the documentation, not the other way around.
22. **Use Confluence as a source of architectural evidence.** Internal runbooks like "Database Access - Production DBs" and "How to Request Common Access" are maintained by engineering and updated regularly (Jason Kennedy updated the DB access page on 9/2/2026). These are living documents that prove processes exist outside of audit season — stronger than audit-time screenshots.
23. **Create tickets on the owning team's board, not just ESEC.** Asking Dhananjay for Airflow/Looker evidence works better with a DNA ticket (his team's board) than an ESEC ticket he'll never look at. Cross-reference back to the ESEC ticket for your own tracking.
24. **Audit log retention must cover the full observation window.** Google Workspace audit logs default to 6 months. If your observation window is 12 months, the first 6 months have no log data by the time the auditor asks. This affects any system with less than 365-day retention. Either upgrade to extended retention (Google Workspace Enterprise) or set up log forwarding to longer-retention storage (BigQuery, S3, CrowdStrike SIEM ingestion) *before* the observation window opens. You can't retroactively produce logs that don't exist.

25. **Bound every population query on the observation window end, never on `date`/today.** Set
    `WINDOW_START`/`WINDOW_END` as constants at the top of the script and assert
    `max(date) <= WINDOW_END` after every pull. The 2026 SLO and Servicing populations were pulled
    with `merged:2025-10-01..2026-09-04` because 9/04 was the day the script ran, putting 15
    out-of-period PRs into submitted evidence. Caught on 9/14, after submission.
26. **Derive populations from the artifact's own links, not from a keyword search.** The access
    review ticket population came from `summary ~ "access review"` and was wrong four ways —
    including mislabeling the entire Q1 2026 cycle, which left a selected sample quarter with no
    identified evidence. The worksheet's hyperlinks (`openpyxl` → `cell.hyperlink.target`) are the
    authoritative population. A keyword search finds tickets that *mention* the thing; the artifact's
    links are the thing.
27. **Never trust a single-page API search when completeness matters.** Jira's
    `/rest/api/3/search/jql` truncates at `maxResults` with no error and no flag. A duplicate scan
    reported zero duplicates because it had seen 100 of 277 issues. Always page to `isLast`.
28. **Record the *reason* a cycle maps to a sample quarter, not just the mapping.** Earnest's review
    cycles were named retroactively (Q1 cycle = reviewed in Q2) and the convention changed mid-audit,
    so **cycle names alone are meaningless for timing.** Resolve by created/resolved dates, add a
    `Covers Sample Quarter` column, and explain the convention in the IPE. And do not "clean up"
    filenames that encode this — `2026 Q1_2` is evidence, not a typo.
29. **Structure the entitlement worksheet by the audit's application scope, not only by
    system-of-access.** Four in-scope apps had their own rows; Servicing was buried in "Admin
    Internal"; SLO — the system with two 2025 sub-exceptions — had no row at all, even though its
    access paths were all reviewed. Add an explicit row per in-scope audit application so coverage is
    self-evident rather than inferred.
30. **Reconcile owner attestations against an authoritative source yourself.** Security's
    verification role is what caught 4 Okta accounts (vs. the Navient Workday active-employee export)
    and 5 Admin Internal accounts (vs. Google Workspace last-sign-in) that the owners' reviews
    missed. It's also the cleanest demonstration of segregation of duties in the review process.
31. **Self-audit submitted evidence before the auditor does, and disclose what you find.** A dated
    revision block listing four self-identified corrections reads as a functioning control
    environment. The same four found by Baker Tilly after a silent edit reads as the opposite. When
    trimming a submitted population, always attach an itemized `*_excluded_out_of_period.csv` — a row
    count that quietly drops between submissions is an IPE completeness problem.
32. **Keep negotiating strategy out of auditor-facing documents.** Keep the technical argument; drop
    the framing. State what the evidence is, why it meets the control intent, and offer to discuss
    what would satisfy the requirement.
33. **Don't close a ticket that's waiting on someone else's input.** ESEC-182/184 were marked Done
    while still awaiting auditor sample selection, which made the tracker read as complete when two
    9/30 deliverables hadn't started. Stage the evidence, leave the ticket open.
34. **Explain discontinued controls as decisions, not gaps.** The worksheet's "Ready for Exec
    Review?" / "Exec Reviewer" / "Sign Off" columns are vestigial — executive sign-off was
    deliberately dropped because it consumed leadership time for no practical assurance; the signing
    executive had no knowledge of whether a given user's access was appropriate. System owners own
    the review, Security orchestrates and verifies. Explain the accountability model affirmatively
    and recommend removing the columns. Never let blank columns be read as a skipped control step.
35. **Delete a duplicate attachment only when it's on the same ticket.** If the same file is
    responsive to multiple requests, leave a copy on each and say so in a comment. Guard every
    deletion with a live byte-size check on the keeper, and post a dated provenance comment for
    anything removed or moved — an attachment that vanishes from an audit ticket with no explanation
    is worse than the duplicate was.
36. **Use Jira process tickets as population sources, not IDP end-state.** For termination populations, Jira IT offboarding tickets (issue type "Offboarding Request") show the offboarding *process* operated — request filed, tasks completed, access removed. Okta deprovisioned user lists only show end-state and include noise (test accounts, celebrity-named accounts, cross-org users). The auditor is testing whether the *control* operated, not whether the account eventually got deactivated. Exclude bulk tickets and non-offboarding tickets (email access grants) — it's incumbent on the auditor to notice omissions, not on you to volunteer edge cases.
