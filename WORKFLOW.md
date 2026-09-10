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
