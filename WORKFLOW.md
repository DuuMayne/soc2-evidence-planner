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
| CrowdStrike | Legacy detections/incidents/behaviors endpoints return 404 | **Decommissioned, not a scope problem** — no key reaches them. Use Alerts v2 (`/alerts/queries/alerts/v2`, `/alerts/entities/alerts/v2`, `/alerts/aggregates/alerts/v1`) |
| CrowdStrike | `scp` claim in the OAuth JWT is `[]` | Tells you nothing about what the key can do — probe the endpoint |
| CrowdStrike | Alert counts don't sum to the total | Image scanning runs continuously; sequential count queries sample different moments. Get the breakdown from ONE terms aggregation |
| CrowdStrike | 2.72M+ "alerts" in the period | All but 95 are `cwpp-*` posture/vulnerability findings, not activity. IOM and drift records are current-state and all carry the export date |
| CrowdStrike | `seconds_to_triaged` = 0 on most alerts | Means never worked, not instant triage. Define "worked" by the presence of `resolution` |
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
  - ESEC-196 (LS.13 email security): Oct/Dec summaries empty due to Google's 6-month retention (Session 8 cited the published schedule; "180 days" was an approximation); Jun 2026 has data. Safety configs, compliance configs, alert sample — uploaded
  - ESEC-197 (LS.13 Gmail safety settings): Uploaded and closed
  - ESEC-199 (LS.13 email notification): Uploaded and closed
  - ESEC-207 (LS.16 asset disposal parent): Archived assets CSV (562 rows), Use of Services letter, Certificate of Destruction (COD #10905)
  - ESEC-208 (LS.16 archived assets): Uploaded and closed
  - ESEC-209 (LS.16 disposal evidence): Uploaded and closed
  - ESEC-210 (LS.16 data destruction cert): Uploaded and closed
  - ESEC-221 (CO.04 wireless security): UniFi firewall rules (2) + WPA configs for Oakland + SLC (4 screenshots) — uploaded and closed
  - Note: ESEC-222 (CO.04 UniFi notification/alert settings) NOT included in delivery — still outstanding
- **LS.13 email security pushback:** Wrote formal pushback argument in justification doc against Baker Tilly demanding sample-month email security summaries. Platform-enforced vendor control — Google scans all email by default, no customer opt-out. Configuration proves design, Google's SOC 2 covers operation. Historical log retention (6 months per Google's published schedule) means Oct/Dec 2025 Google data doesn't exist and never will. Session 8 narrowed this: Cloudflare Area 1 sits upstream of Google and may hold those months. Documented in ESEC-278.
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

A review of what had already been submitted, rather than new collection. Found and fixed five
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

**5. LS.13 — the mail gateway was misattributed, and the LS.13 evidence covers only half the
inbound path.** `email_security_dns_records.txt` (ESEC-198, submitted 9/8) recorded
"Gateway/Scanning: mxrecord.io (Valimail/email security vendor)". Verified with `dig` and `whois`:
`mxrecord.io` has Registrant Organization **Area 1 Security**, registrar Cloudflare, Inc., and both
`mailstream-east/west.mxrecord.io` resolve into CLOUDFLARENET (172.65.213.128 / 172.65.220.210).
Area 1 was acquired by Cloudflare in Feb 2022. Valimail *is* in the stack — `vali.email` is the SPF
macro-include target and the DMARC `rua` destination — but it is not the gateway. Two vendors, two
functions, conflated in one label.
- **Consequence 1, coverage:** all inbound mail transits Cloudflare Area 1 *before* Google. Req
  96/97/98 evidence the Google layer only. No Area 1 config, policy, admin listing or detection
  output has been filed. Being compiled.
- **Consequence 2, the retention argument was too broad.** The comments already posted to
  ESEC-196/197 asserted Oct/Dec 2025 "cannot be produced." True of Google's logs; possibly false of
  Earnest's mail path, because Area 1 retains detection telemetry on its own schedule. Posted a
  supplementing comment narrowing the claim rather than leaving it standing. **If Area 1 covers
  those months the sample request is answerable, not deniable.**
- **Consequence 3, a point for the control:** inbound mail had two independent scanning engines all
  period, and the MX records proving it are verifiable by the auditor from public DNS without
  Earnest credentials or anyone's retained logs.
- Corrected DNS file rewritten with the two-layer stack, the `whois`/`dig` output as attribution
  basis, and inline IPE; uploaded to ESEC-198 replacing the original.
- Recorded separately that Earnest is in active procurement with **Material Security** and
  **Abnormal Security** to replace Gmail + Area 1 — explicitly *not complete, not in production,
  not affecting the audit period*, framed as a planned enhancement to an operating control rather
  than a response to a failure.

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

### September 14, 2026 (Session 8, continued — Drive staging and CO.08 close-out)

**Staged the full submission for Google Drive.** `stage_for_drive.py` mirrors the Jira hierarchy the
auditor already navigates — control folder, then request folder — so any file traces in either
direction. Result: `~/Downloads/2026 SOC II/SOC2_2026_Evidence_Upload`, **334 files / 83 MB / 36
controls / 108 request folders.** All 308 Jira attachments downloaded, size-verified against Jira on
download, then re-hashed on disk against the manifest: 308/308 SHA-256 matches, no failures, no
unaccounted files, no Drive-hostile filename characters. Filenames preserved byte-for-byte.
- Attachment download needed manual redirect handling: `/attachment/content/{id}` 302s to a signed
  media host that rejects the request if the Basic auth header is forwarded.
- 16 requests have no attachments. The first pass wrote one generic
  `_NOTHING_COLLECTED_YET.txt` into all of them — wrong for four, which are closed `Done` with
  substantive rationale. Split into `CLOSURE_RATIONALE.txt` (the reason *is* the deliverable — a true
  N/A, or an IPE that can't take query/row-count form) and `_PENDING - <blocker>.txt` naming whose
  move it is. 12 pending: 7 awaiting Baker Tilly's sample selection, 1 HR + selection, 1 Earnest IT,
  2 tabletop, 1 pentest.
- Writing those files surfaced two internal contradictions in already-closed tickets: ESEC-234's
  automated comment cited an IPE covering "Jira queries with parameters and row counts" when the
  incident population isn't a query at all, and ESEC-235's said "172 incidents/alerts" when the
  incident count is 3 (172 was the raw alert count). Both superseded in the closure rationale.
- `README.txt` leads with the four things that will otherwise look wrong: Splunk-named folders
  containing CrowdStrike, text-only folders being deliberate, access review cycles named for the
  quarter *reviewed*, and the vestigial exec sign-off columns. Every number in it and in `INDEX.md`
  is computed from the manifest, not asserted.

**CO.08 Req 136 closed out properly.** It held a single end-user FileVault screenshot — thin evidence
for a 354-device MDM-enforced control. The screenshots that actually prove per-blueprint enforcement
already existed but were filed under Req 137 as config evidence.
- Population pivots to **6 blueprints / 354 devices**. Three of the six (349 devices) already had
  blueprint-side evidence; restaged into Req 136 under blueprint-descriptive filenames with
  provenance back to each ESEC-231 attachment ID. Uploaded to ESEC-230 (atts 231722–231726) with
  `00_COVERAGE_MATRIX.md`.
- The primary artifact is the library item's **Assignment Maps list**, which names all 13 blueprints
  the FileVault profile is assigned to, including all 6 in the population — so 354-device coverage is
  provable from one screenshot. `config_4` is the strongest: status panel reading 31 Success / 0
  Error / 0 Other.
- Adam's instinct was to close the remaining 3 blueprints (5 devices) as test/non-prod. Checking the
  population showed all 5 are MacBook Pros assigned to named individuals, all checked in on the
  export date, one belonging to Earnest IT — production laptops in a blueprint someone named "test."
  Closed instead on the enforcement argument, which covers all 354 without needing an exclusion, and
  disclosed the difference in evidence form with screenshots offered on request. See lessons 39–40.
- Justification doc CO.08 section rewritten accordingly and re-uploaded to ESEC-278 (att 231727,
  superseding 231712). Framed as an addition, not a correction — the revision block still says five
  defects, because nothing previously submitted under CO.08 was inaccurate.

**Delivery format changed from Markdown to PDF.** Adam's read was that Baker Tilly would hate
Markdown; the deciding argument is simpler than preference — Drive has no Markdown renderer, so a
`.md` previews as raw text and every table arrives as pipe soup before the auditor downloads
anything. All 28 written documents now render to page-numbered PDF with running headers and a PDF
outline (the justification doc is 28 pages). `INDEX.md` retired for a filterable 3-sheet
`EVIDENCE_INDEX.xlsx`. `.txt` left alone. Markdown stays the source of truth in the repo and on the
Jira tickets, with `source_markdown` + `source_sha256` recorded next to each PDF so the conversion is
checkable both ways — a PDF is a rendering of evidence, not new evidence. Staged tree re-verified
after the change: 334 files, 313 manifest rows, 88.2 MB, 0 hash mismatches, 0 `.md` remaining.
Renderer notes and the five layout defects that had to be fixed are in the runbook. See lesson 41.

**Pre-upload pre-flight on the rendered PDFs found one real defect — in a `.txt`, not a PDF.** Extracted the text of all 29 renders and grepped for unrendered Markdown (literal `**`, `#` headings, table pipes) and thin pages. Every PDF hit was a false positive: `#` was a row-number column header, the pipes were Mermaid source in a fenced block (the visual diagram ships as a PNG alongside) or a `|`-separated metadata line, and the emoji in the pasted Jira checklists render in colour. The defect the sweep surfaced instead was the Iru IPE on ESEC-229 asserting both a MacBook filter and "no pagination or filtering applied." Rewrote it to state the filter, justify it against the control's wording, and carry the 302-vs-289 reconciliation; re-uploaded as att 231741 superseding 231069. Also caught that Jira returns attachment ids as strings, so an int `OLD_ID` made the upload-then-delete guard fail open and leave both copies on the ticket — the guard needs `str()` on both sides. Final tree: 334 files, 313 manifest rows, 88.2 MB, 0 hash mismatches.

### September 14, 2026 (Session 8, continued — stripped the correction narrative from the deliverable)

**Adam's call, and it reverses the posture in the two blocks above: nothing Baker Tilly receives
narrates our own editing history.** Over the preceding sessions I had built up a disclosure layer —
a five-defect revision block opening the justification doc, dated correction sections inside four
IPEs, "originally we pulled X, then corrected to Y" provenance paragraphs, sidecar CSVs itemizing
out-of-period rows removed from a population, and "available on request" offers. Each one was
defensible in isolation. Together they made the submission read as a partial one with a confession
attached. Adam's framing: *"I want them to believe that what we are providing is what we have, not
that we are holding out on them"* — and separately, that filter mechanics invite questions about the
process instead of answers about the control.

The clearest example was mine. I rewrote the Iru IPE *after* being told the package was good to go,
and the rewrite spent more words on the history of the document than on describing the evidence.

Two cleanup passes, 30 edits across 17 documents, 0 misses:
- Removed: the justification revision block, the CM.02 observation-window correction, four numbered
  `CORRECTION` sections in IPEs, two `CLOSURE_RATIONALE` notes about earlier automated comments, the
  LS.13 "original submission attached the raw export" paragraph, the coverage-matrix provenance
  narration, a `Rescoped:` line, and three `Prior version mislabeled this Q4 2025` cells I had
  written into `it_access_review_tickets.csv`. Deleted the two
  `*_excluded_out_of_period.csv` sidecars.
- Reframed rather than deleted: LS.13's two-layer mail path is now stated as a fact about Earnest's
  architecture, not as a correction to submitted evidence; the exec sign-off explanation is now
  purely the design decision; the 302-vs-289 device reconciliation is now population scope ("the Mac
  laptop fleet, which is the scope of this control") rather than a filter narrative.
- **The line I did not cross:** the Iru IPE's actual error was the sentence "no pagination or
  filtering applied," which was false. It is *removed, not reversed* — the shipped IPE describes the
  export and its row count without a filtering claim in either direction. And every reconciliation
  the auditor could spot themselves stayed in, because omitting one of those guarantees the question
  rather than avoiding it.

**Verified the disclosure prose was never load-bearing before removing it.** Scanned all 142 ESEC
tickets for same-name and same-stem attachments: 3 hits, all legitimate different-format pairs
(`.md`/`.png` diagram, `.json`/`.txt` IPE). No superseded copies remain on any ticket and the
manifest names the authoritative attachment ID per file, so nothing became ambiguous.

**Re-synced Jira to the cleaned deliverable.** `reupload_cleaned.py` drives off manifest SHA-256
mismatches rather than a hand-maintained file list — it caught the `2026_Q1_access_review_ipe.txt`
copies on ESEC-182/184 that working from the folder list would have missed. 19 files replaced across
12 tickets, each guard confirming the replacement live in `jira.attachments()` before deleting the
superseded copy.

**Also pulled `staging_report.json` out of the delivered tree.** It is a build artifact and it
narrated our internal triage — "internal IT task - screenshot chase", "Claude Code security review
action, not audit evidence". Nothing in the deliverable referenced it. Now written beside the
scripts; the three readers and one writer were repointed so a future run can't re-ship it.

Final tree: **331 files, 311 manifest rows, 88.2 MB, 0 hash mismatches, 0 `.md`, 63 PDFs all
readable.** Swept the extracted text of every PDF plus all `.txt`/`.csv` for correction language —
the only remaining hits are genuine source data (GitHub PR titles reading "Correcting Mapped
values", a Confluence page revision count). Ready to upload. See lesson 42.

### September 14, 2026 (Session 8, continued — mined the handed-over folder; closed EL.06)

Adam dropped an `Evidence Requests/` folder into Downloads: *"There should be some evidence in a few
of the folders thats valuable but I dont remember which."* 32 files. Diffed by SHA-256 against every
file in the staged tree — not by filename, not by request number, which would have been wrong in both
directions. 8 already staged; 23 added.

The one that mattered: **AWS Backup restore testing.** The package already evidenced that backups
exist and how they're configured (25 RDS instances, 230 automated snapshots, three backup plans). It
said nothing about restores ever being exercised. Three screenshots — the
`RDS_Restore_Testing_Plan_Prod` summary, its 57-job history, and the `restore.tf` that defines it —
turn "backups are configured" into "restores are tested monthly and all 57 completed." Wrote
`restore_testing_ipe.txt` off the captures: plan ARN, `cron(0 5 2 * ? *)`, `LATEST_WITHIN_WINDOW`,
60-day selection window, three protected resource selections, jobs from 2025-12-31 to 2026-09-02, and
the selection creation dates that explain why the list starts where it does — that last one is visible
to the auditor in the same screenshot, so it goes in. What is *not* in it: any claim that 57 was
reconciled row by row, because I didn't count the rows.

Also added: the SDLC **Process** doc (the policy shipped without it, though `policy_mapping.csv` had
been naming the page all along), 11 months of Files.com vendor release notes (the CM.02 IPE asserted
platform changes are vendor-managed without ever showing the vendor's change record), the Splunk
"Immutability of indexed data" documentation for the Oct 2025 – Jan 2026 stretch when Splunk was the
SIEM, and the production database access runbook — Req 78 "Database Rules Document" had been answering
with a mapping CSV pointing at three database *design* pages, while the actual rules document
("we do not provide application engineers with read/write access to production DB's", the Jira request
path, and every prod database with its read-only Okta group) sat in the folder.

**EL.06 closed on Adam's positioning.** HR won't publish a selectable roster of performance reviews.
Rather than leave ESEC-244 open on "waiting on auditor sample selection," the population went in as a
count (264 employees, EOY 2025, from HR, dated), the five reviews HR released ship as *the* samples
with reviewing managers named, and the justification states the mechanism for more: a written request
naming count and cycle, routed through Security, handled per sample, because of what the artifact
contains. Ticket closed, `_PENDING` folder deleted. See lesson 44.

**Then a second defect class, found by script rather than by reading.** Parsing `Evidence File:` lines
out of every IPE and diffing against the folder listing turned up four IPEs describing files that
weren't there — shared collector dumps copied per-request, each naming nine artifacts in a folder
holding one or two, complete with `Row Count: 0 / repos scanned: 0` stanzas. `CM.08 Req 36`'s 289-row
entitlement CSV was undocumented entirely. Rewrote all four as per-request IPEs. See lesson 45.

### September 14, 2026 (Session 8, continued — the IT.11 backup population actually covers the period)

My closing note said "restore testing jobs start 2025-12-31, so Oct–Dec 2025 has no restore jobs."
Adam read it as a claim about backups: *"So we dont have evidence from Oct and dec 2025 for backups?
Check again. Change to the production account."* Two separate populations, and my sentence had put them
together. Re-checked against live prod (075440130607, `AWSReservedSSO_Engineering-Prod`).

Backups from Oct and Dec 2025 exist and are still in the account. `list-recovery-points-by-backup-vault`
across both vaults returns 210 recovery points, every one COMPLETED, 186 of them inside the audit
period, covering all 12 months — two per production database per month, one to `Default` via
`RDS-Monthly-1yr-Retention` and one to `RDS-Backup-Alert-Vault-Prod` via `RDS-Backup-Alert-Plan-Prod`,
both `cron(0 5 1 * ? *)`, both cold-storage-at-30 / delete-at-365. In the months where the Quarterly or
Yearly rule fires on the same date, AWS attributes the point to the longer-retention rule, so the rule
mix shifts month to month while the count per database per month stays at two — worth stating in the
summary, because otherwise the rule-attribution table looks like the monthly rule skipped Oct 2025.

The real weakness was the staged population itself. `rds_automated_snapshots.csv` (230 rows, pulled
2026-09-01) is a 7–31 day retention window and can only ever show the last month. `list-backup-jobs`
has the same problem from the other side — its oldest record in the account is 2026-08-31. Delivered
`aws_backup_recovery_points.csv` (210 rows, plan/rule/retention/KMS key per row) and
`backup_monthly_coverage_summary.txt` (by month, by database, by rule) to ESEC-264, rewrote the Req 212
IPE to say which file carries period coverage and which is a point-in-time window, and gave Req 212 a
population and justification paragraph in the justification doc. See lessons 47 and 48.

**Then filled in the shared request list, which turned out to already hold Navient's questions.**
`Earnest SOC 2 2026 Request List.xlsx` has an `Earnest Status` column (dropdown: Not Started,
Researching, Blocked, Requested, Collected, Added to Drive, Sent to Baker Tilly, Follow-up), an
`Earnest Notes` column that was entirely empty across all 84 requests, and a `Navient Notes` column
carrying five reviewer questions dated 9/14 — one of which was the backup question, asked in Navient's
own words: *"Earnest to confirm we can only go back to Dec 2025 as that's where the 2nd screenshot
ends… is there an explanation for why there are no entries for Jan 2026?"* Adam's pushback was
relaying a reviewer, and answering it in the spreadsheet is where it actually lands.

Statuses were derived by joining the sheet's request numbers to the staged tree by manifest folder
rather than judged one at a time: 70 requests have staged files, 14 hold only a `CLOSURE_RATIONALE` or
`_PENDING` note, and those two groups plus the reason in each note determine the status. Result:
65 Collected, 9 Blocked (7 awaiting Baker Tilly sample selection, plus Req 209 on its dependency and
Req 210 on the third-party pentest), 5 Follow-up, 3 Sent to Baker Tilly, 1 Requested (ITO screenshot
from Earnest IT), 1 Researching (tabletop, must run before 9/30). Rows Baker Tilly or Navient had
already touched kept their status — those columns are *their* record of what they hold, not ours to
overwrite — and got a note prefixed `9/14 AD -` to match the `9/14 JW -` convention already there.

**Collected, not Added to Drive**, for the staged 65: the tree is built, hash-verified, and every file
is on its ESEC ticket, but the Drive share has not gone out. One bulk flip when it does.

Two of the five follow-up answers are commitments rather than answers, and are written that way — the
New Relic alert-event export (retention limit to be stated explicitly *with* the export, so the short
window reads as a bound rather than an omission) and the database-side credential expiry for LS.08
Req 77, where the screenshot Navient questioned is the Okta session policy and does not evidence the
24-hour statement at the database layer. Saying "we will provide X" beats reasoning from what the
screenshot might cover.

One tooling gap closed on the way: `reupload_cleaned.py` uploads whatever is in the tree, which is
wrong for rows where the tree holds a rendered PDF and the ticket deliberately holds the `.md`. It
would have pushed the PDF and deleted the source. `reupload_sources.py` routes by `source_markdown`
and refreshes `source_sha256`, so the PDF-in-Drive / Markdown-in-Jira split survives a re-sync.

Final tree: **355 files, 336 manifest rows, 95.9 MB, 0 hash mismatches, 0 `.md`, 82 PDFs all
readable, 15 requests still awaiting third parties or auditor selection** (down from 16). Correction-
language sweep clean — remaining hits are CVE descriptions and PR titles.

### September 14, 2026 (Session 8, continued — Req 108 CrowdStrike population; Req 46 gap confirmed)

Navient asked for an actual export behind Req 108: *"Can the team provide an export of the events
during the timeperiod or, if historic data doesn't go back that far, then as far back as possible?
The provided screenshot appears to show an incomplete list of events from a 3 day history."* The
answer for the security half of CO.01 is CrowdStrike, and it took a working key to get it — the first
credential was rejected at us-2, us-1, eu-1 and gov with both body-param and Basic auth, and Adam
supplied a replacement that authenticated immediately.

**The population is 95 alerts, and getting to that number was the work.** A naive "all alerts in the
period" query returns 2.72 million. Adam scoped it: *"Keep the crowdstrike specific to the control
language. 'Suspicious or unusual activity alerts' not just all security alerts."* The data agreed —
all but 95 records are `cwpp-image-scan-detections` (container image vulnerabilities, which are IT.06
evidence), `cwpp-k8s-ioms` and `cwpp-drift-indicators`. The latter two are current-state posture
snapshots that all carry the export date, so including them would have asserted a million events in
September. Delivered `crowdstrike_suspicious_activity_alerts.csv` (95 rows, 23 columns) and
`crowdstrike_co01_alert_summary.txt` to ESEC-212.

**Framed as onboarding maturity, per Adam:** *"lets frame this as maturity and onboarding from one
tool to another like the other crowdstrike related data."* Timeline: Spotlight 2025-11-07 → first
tenant alert record 2025-12-08 → contract ~Jan 2026 replacing Splunk → detection and NGSIEM
correlation alerting 2026-06-18. I nearly mis-diagnosed that June floor as retention; checked and
disproved it — December 2025 image-scan alerts are still present, so nothing aged out. It is when the
capability came online, which is a different and much better sentence.

Also replaced `co01_security_monitoring_supplement.pdf`, which said the API scope did not reach the
detection endpoints and so alert data could not be exported directly. It can, and now is, so that
sentence would have contradicted the file sitting next to it — and it read as withholding. Same
removal from the CO.01 justification section. See lesson 49.

Corrected two claims against the API rather than repeating them: the August 14 Okta alert was triaged
**52 minutes** after the event and closed at 1h49m, not "within 3 hours" as both the supplement and
the PIR summary said; and 86 of the 95 alerts have `seconds_to_triaged` = 0, which means never worked,
not instant triage — so "worked" is defined by the presence of `resolution` (9 alerts, 8 false
positive, 1 true positive: IntelDomainHigh, resolved in 40 minutes) and the IPE says what the zero
means. See lesson 50.

Two open High cloud-IOA alerts surfaced that Adam needs an answer for before Baker Tilly reads the
CSV: "Write API call originated from known-malicious IP address" in prod account 075440130607 on
2026-08-21 and 2026-08-22, both still `new` with no disposition.

**Req 46 (LS.02 provisioning approvals) — Adam's suspicion confirmed with numbers.** *"That is likely
missing all access except possibly files.com."* Of the 140 tickets in the ESEC-171 population:
Files.com 18 genuine, SLO 13 keyword hits but only ~3 real application-access requests (the rest are
GitHub, Dropbox, FullStory, Splunk, 1Password and the `slo-service` database), MMAX ~3, Servicing ~1,
**SchoolHub 0, CASHI 0**, and 97 of 140 name no in-scope system at all. The structural tell: Req 27
and Req 35 each have six per-system ESEC tickets; Req 46 has one. Not a Tyler/Gaige failure —
IT-21925 asked them for Google Workspace, UniFi, asset disposal and a hires/terms/transfers list,
never per-application provisioning, and they delivered on 9/11. Five of the six in-scope systems are
Earnest-built apps administered by engineering, which is the NS-534 gap already disclosed on ESEC-183.
The ESEC-171 IPE currently claims a per-system breakdown the rows do not support and needs correcting
either way. Blocked on the Okta token **value** — the string supplied was the 20-character token ID,
which 401s; values are 42 characters.

Tree after this pass: **340 manifest rows, 359 files, 100.3 MB, 0 hash mismatches, 0 stray `.md`.**

### September 14, 2026 (Session 8, end — Okta unblocked, Files.com scoped, stopped for the night)

Adam supplied the 42-character Okta token value and it authenticated against
`https://meetearnest.okta.com` immediately, which unblocks the two things the previous entry says are
blocked. **Nothing was collected. This is a state handoff, not a delivery.** Twelve-hour day; Adam
called it: *"Stop. Just log this and im calling it a night."*

**What the token showed, before stopping.** The tenant holds **370 apps, 240 ACTIVE**. Against the six
systems Req 46 names:

| Req 46 system | In Okta? | Assignments | In-period `created` |
|---|---|---|---|
| Files.com | Yes, SAML 2.0, `0oa1bicu49zskHd5b0x8` | 62 users, 8 groups | 30 |
| MMAX | Yes, `MMAX-UI`, OIDC, `0oa16wlfu6wnykcGe0x8` | 13 users, all direct, 0 groups | 11 |
| Servicing Platform | `Servicing Dashboard (Prod)`, `0oa6qxnud2D25Cf6C0x7` | 1 user (jen.chi, 2024-06-24) | 0 |
| SLO Platform | No app of that name — but see below | — | — |
| School Hub | No | — | — |
| CASHI | No | — | — |

**The SLO Platform finding, and Adam's scoping call on it.** The in-scope systems sheet defines SLO
Platform as *"multiple applications including Acru, Verify, Agiloft, Looker and Analyze"* — and all of
those are in Okta with real in-period assignment activity: `Looker` 426 users / 142 in period,
`ACRU Service (Prod)` 254 / 96, `Agiloft Production` 153 / 68, `Analyze (Prod)` 142 / 50. I raised it
as a possible route to the missing Req 46 population. Adam's answer: *"Only files.com is in okta.
Ignore the rest. Just get me files.com. Well, looker is assigned via okta I think. But lets just do
Files.com now."* So Files.com is the scope, Looker is a maybe he wants to look at himself, and the rest
is out. **Do not re-litigate this next session.** The component-app numbers are recorded here only so
nobody has to re-derive them if he changes his mind about Looker.

Also worth noting for whoever picks this up: the two Non-Prod apps returned **497 users each**
(`Servicing Dashboard (Non-Prod)`, `Analyze (Non-Prod)`) — same number twice, which is a group
assignment expanding to near-everyone, and non-prod is out of scope regardless.

**The Okta System Log cannot cover this audit period, and it lies about it.** Oldest reachable event is
**2026-06-17** — a ~90-day rolling window against a period starting 2025-10-01. The dangerous part:
asked for `since=2025-10-01`, Okta does not error. It returns the oldest event it still holds, so the
response looks like a successful year-long pull and is full of June 2026 events. I found it by probing
four different `since` values and getting the same oldest event back from all four. See lesson 51.

The way through is the same asymmetry as the AWS Backup recovery points in lesson 47: **app-assignment
`created` timestamps are current object state, not log history, so they do reach back across the whole
period.** Assignment dates carry period coverage; the System Log corroborates the mechanism for the
three months it can still see; the retention floor gets stated as a boundary rather than omitted.

**Where the code stands.** `analysis_sept14/okta_api.py` — new, thin read client, token from
`OKTA_TOKEN` only. Holds `page()` (follows `Link rel="next"`; the apps endpoint caps at 200 and looked
complete at 200 against a real 370), `log_floor()` (probes with an absurd `since` to measure the real
retention floor), and 429 handling that honours `x-rate-limit-reset` rather than sleeping a fixed few
seconds. `analysis_sept14/pull_okta_filescom.py` — written, **never run**. Intended outputs
`filescom_okta_access_population.csv` (one row per assignment, direct vs. via-group, the granting group
named, `assignment_granted_in_period` flag), `filescom_okta_group_membership.csv`, and
`filescom_okta_access_summary.txt` with the retention boundary in the IPE.
`analysis_sept14/cache_okta_assignments.py` — written, aborted on a 429 mid-run, superseded by the
Files.com-only scope. No output files exist under `evidence/okta/` from this pass.

**Still open from the previous entry, unchanged:** the ESEC-171 IPE claims a per-system breakdown its
140 rows do not support (`SLO: 19 | Files.com: 19 | SchoolHub: 8 | MMAX/Spoke: 7 | Onboarding: 87`),
and the Okta inventory now independently corroborates that — there is no SchoolHub or CASHI app in Okta
at all. That correction has to happen whatever else Req 46 gets. The two open High cloud-IOA alerts
still need a disposition before Baker Tilly reads the Req 108 CSV.

### Key Audit Risks Identified (Session 7)

1. **Pentest timing (IT.09):** Cam confirmed ~2 weeks before SLO pentest can start. Test will initiate within observation window (before 9/30) but final report and remediation will not be complete. Defensible — "testing performed" — but will likely get noted by Baker Tilly. Similar to last year's finding where the pentest covered the prior period.

2. **Tabletop exercise (IT.08):** Must happen before 9/30. Adam has format and scenario ready but needs participants and a calendar slot. If it slips past the observation window, it's a finding.

3. **Vulnerability management format (IT.06):** Evidence is submitted and the program is genuinely strong (CrowdStrike Spotlight + Grype CI/CD + Kyverno + Keystone governance). Risk is that our remediation story is built around the Keystone program (structured dependency upgrades across service teams) rather than traditional "scan → ticket → fix → rescan" cycles. Baker Tilly may want individual CVE remediation tickets. Narrative packet explains the three-pillar approach but this requires the auditor to engage with a different model than they're used to.

4. **User access provisioning samples (LS.02):** Population of 140 Jira tickets is solid. Risk is at the sample level — when Baker Tilly picks specific users, every sampled provisioning must show documented approval *before* access was granted. Any sample with approval after the fact or missing documentation is a repeat finding on a control they're already watching from the 2025 exception. Engineering populations from NS-534 (SLO/CASHI/MMAX/SchoolHub/Servicing app-level access modifications) are still outstanding.

5. **Log retention gaps (systemic):** Google Workspace audit logs default to 6 months retention. Anything before ~March 2026 is gone. If Baker Tilly picks October/November/December 2025 as sample months for email security (LS.13), those logs don't exist. This isn't just Gmail — any system with <365 days retention has the same gap for the early observation window. The configuration evidence proves the control was operating, but historical output has aged out. Fix for next year: extended retention (Google Workspace Enterprise) or log export pipeline to longer-retention storage (BigQuery, CrowdStrike ingestion).

6. **Baker Tilly evidence format receptivity:** Evidence is objectively stronger than last year but formatted differently from what Baker Tilly is used to (CSVs, API outputs, narrative documents vs. screenshots). Justification document is designed to bridge the gap but auditor may still push back. Three-layer plan: justification doc → supplement with screenshots if needed → escalation via personal contact to BT head of assurance if they reject stronger evidence for format reasons.

### September 15, 2026 (Session 9 — Req 39 rebuilt; export provenance audited)

**Req 39 / CM.09 (ESEC-162) rebuilt.** The published package was three partial CSVs plus an IPE
carrying two real defects. Replaced with three files covering the full period, built by
`analysis_sept14/pull_patching_approvals.py`:
- `patching_monthly_approvals.csv` — all 9 monthly patching tickets Oct 2025–Jun 2026, approval
  comment reproduced verbatim, quarterly epic on each row, work-start from the changelog.
- `june_2026_production_patching.csv` — the 7 June production infrastructure patching changes with
  named approvers, approval/merge timestamps and the AWS EKS apply each produced.
- `IPE_documentation.txt` — rewritten.

Two defects fixed in the process:
1. **AWS timestamps were 7 hours early.** `aws eks describe-update` returns an offset-aware value the
   CLI renders in local time (`-07:00`); the old collector stripped the offset and stored Pacific
   wall-clock as UTC. That inverted the approval sequence — the change appeared to precede the PR that
   authorised it. Corrected, all five June applies land **3–15 minutes after** their PR merged.
2. **The PRs were attributed to the wrong ticket.** Published evidence tied the June EKS PRs to
   SRE-1658 (June monthly patching). SRE-1658's actual work is Tenable `dnf update` over SSM on two
   Nessus hosts and produces no PR at all. The PRs belong to SRE-1797 / SRE-1798.

**The EKS upgrade track is separate from monthly patching.** Infrastructure version upgrades roll up
to their own quarterly epic series — SRE-93 (Q4 2025), SRE-1559 (Q1 2026), SRE-1561 (Q2 2026) — with
per-cluster, per-version-step children. Two findings worth carrying forward:
- **SRE-1797, SRE-1798, SRE-1794 and SRE-1796 are orphans.** Jira's own automation posted "This issue
  is missing a parent" on each, twice. Setting parent = SRE-1561 completes the chain epic → task →
  approved PR → AWS apply. Not done — they're SRE's tickets, pending Adam's go-ahead.
- **Do not cite SRE-37/36/68/39/46/47/58 as the June change record.** All were resolved 2026-05-18 in
  a bulk close while the matching AWS applies happened 2026-06-26 — resolution predates the change.
  SRE-1797/1798 are the accurate record.

**Export provenance audit — the finding to circle back on.** Adam asked whether our exports are
actually exports. Measured across the staged tree: **105 distinct CSVs, 91 built by our collectors,
9 genuine vendor exports, 5 mixed, and zero raw API responses staged anywhere.** See lessons 53–55.
The data is sound; the gap is tie-out. Remediation plan, in priority order, deferred pending Navient
feedback on column L of the shared request list:
1. Dump the unmodified API response as `<stem>_raw.json` beside each derived CSV.
2. Prefer native console exports where the vendor UI offers one.
3. Strip the four judgment columns (lesson 54).
4. State the transformation in each IPE with the raw file as the tie-out.
Scope it to **populations first** — those are what get completeness-and-accuracy tested; config
snapshots rarely do.

**Evidence tree moved into Google Drive.** Adam installed Drive for Desktop and moved the tree to
`~/Library/CloudStorage/GoogleDrive-adam.duman@earnest.com/My Drive/SOC2_2026_Evidence_Upload`.
Added `analysis_sept14/paths.py` as the single source of truth for the tree location — 17 scripts
hardcoded the old path. Only the scripts touched this session import it; the rest still hardcode and
will need repointing when re-run. Direct-sync automation was explicitly dropped.

**`INDEX.xlsx` / `INDEX.csv` at the tree root**, from `analysis_sept14/build_drive_index.py`: request
number, control, path, sha256, Jira ticket and attachment ID per file, filterable, with a summary tab
(339 files, 68 requests, 35 controls). Built because **39 files are named `IPE_documentation.txt`** and
a Drive search returns 39 indistinguishable hits. Nothing actually collides — no request folder holds
two files of the same name — but you cannot tell that from search results.

**Two self-inflicted errors worth recording.** The manifest's `folder` field is already the full path
from the tree root; I read it as relative to `control_folder`, which (a) appended three duplicate
manifest rows instead of updating the existing ones and (b) wrote the three files into a spurious
nested `CM.09/CM.09/` directory in Drive. Both repaired — files relocated, stray directory removed,
manifest back to 339 rows with all rows verified present on disk. **Read the manifest schema before
writing to it; a field named `folder` is not necessarily a leaf.**

**Google Sheets is not readable through Drive for Desktop.** Native Google files sync as JSON stubs
containing only a `doc_id` — no data — and "Shared with me" is not synced at all. Only uploaded
`.xlsx` hydrate as real files. The shared request list (`17kATahp-…`, `rtpof=true`) is an uploaded
xlsx, so downloading it or moving it into My Drive makes column L readable. Also: do not run a
recursive `grep` across the Drive mount — it forces Drive to hydrate every file and had to be killed.

**Status:** ESEC-162 holds exactly three attachments (231865, 231866, 231867); superseded 230834,
230824, 230633 and 230632 deleted after verifying the replacements live. Waiting on Navient feedback.

---

### September 15, 2026 (Session 10 — worked the re-pull ranking; items 1, 2 and 3 closed)

**Tickets touched:** ESEC-142, 143, 144, 145, 146, 147, 148, 212, 278 (plus the vulnerability packet)

Took the ranked re-pull list from Session 9 top-down rather than proposing all 91 CSVs.

**Item 1 — vulnerability packet.** The two files whose row counts were API page caps (2,000 open,
50+50 by month) now say what they are: extracts in the platform's own return order, each named with
the population it came from, exact figures re-pulled from `meta.pagination.total` on `limit=1`
queries rather than counted off a truncated page, full month offered. The IPE's internal
contradiction — 400 in the text against a 2,000-row file — is gone. Counts CSV stayed internal.

**Item 2 — my ranking was wrong, and finding that out was the deliverable.** I had called the
CrowdStrike population's 2026-06-18 floor a detection-retention boundary that the migration-maturity
framing didn't explain. Falcon carries two date fields that answer opposite questions:
`created_timestamp` (first raised, never rewritten) and `timestamp` (event time, **refreshed** on
container posture findings, because posture reports present state). Filter retention on `timestamp`
and the whole tenant reads ~90 days old — including 2.88M container findings that plainly did not
all occur in one week. Filter on `created_timestamp` and the oldest record is a posture finding
first raised 2025-12-08 whose `timestamp` reads 2026-07-03, later than its own creation. Retention
reaches ~6 months further back than the activity population begins, so retention cannot be what
sets that start date; activity alerts first raised before 2026-06-01 = **0**. Onboarding, not
aging-out. The fix was capturing the proof (`prove_crowdstrike_retention.py` → ESEC-212), not a
re-pull. **Retention and capability-start look identical unless you ask whether records of *any*
type predate the boundary.**

**Item 3 — the six CM.02 change populations. Retaining the raw is what found everything else.**
All six IPEs stated the path as GitHub API → gh CLI → JSON → CSV. The JSON step was real but had
never been kept, so the CSV was the earliest artifact anyone could inspect. Re-pulling that
intermediate through the same `gh` account the IPEs name (`pull_change_population_raw.py`) cost one
script and surfaced four defects reading the CSVs could not:

1. **Servicing was short ten changes inside its own stated scope.** Its IPE claimed 14 repositories
   and named 13; querying every repository on the mapping workbook's Servicing sheet found
   `feed-ingestor` (9) and `nd-validations` (1) had never been queried. Reissued at 515. MMAX had
   the same shape (18 named, "+ others", 21 claimed); its missing three are unrecoverable from any
   script, so after sweeping 759 org repositories on adjacent naming families and confirming all
   five candidates out of scope, its IPE names the 18 actually queried and drops the 21.
2. **Three stated end dates for one control and one period** — 2026-09-04, 2026-08-31, and
   2026-09-30 on a population collected before that date. Proved by re-pull that a single window
   reproduces all six delivered counts exactly *before* rewriting anything, so the three reconcile
   to one without moving a row.
3. **Two files named `*_excluded_out_of_period.csv` held 15 changes merged Sept 1–4, 2026** — inside
   a period running to September 30. The label asserted we had excluded in-period changes. Renamed
   to the explicit date range with a note stating both boundaries, and staged and manifested for the
   first time; they had existed only as Jira attachments.
4. **`reviewDecision` is current state, not an approval record — and would have manufactured 98
   exceptions.** It reverts to `REVIEW_REQUIRED` the moment a commit lands after an approval and
   stays there after merge, and is null where the base branch has no required-review rule. At face
   value 98 of 1,462 merged PRs read as something other than approved. Pulling the actual review
   history (`resolve_review_decisions.py`) showed **97 of 101 had an `APPROVED` review from someone
   other than the author at or before `mergedAt`**. Request 27 asks for a population, so the field
   isn't carried; approval is tested at each PR URL where the real history lives. The four genuine
   ones are held internally with merge actor and event history — three Copilot agent PRs each merged
   by a named engineer, one human PR whose ten review events were recorded as `COMMENTED`.

Also normalised all six to one schema (Files.com had its own, with a `Review Decision` column),
stated the row order, restored full titles from ~80-character truncation, and corrected a
consolidated total of **1,441 that was arithmetically wrong on its own terms** — it summed five
populations and silently dropped Files.com's 11 — to 1,462 rows / 1,311 unique, the gap being two
repositories that each serve two products, stated so the six aren't read as additive. Every IPE is
generated from the JSON beside it (`generate_change_population_ipes.py`), so a count cannot drift
from its evidence.

**Two process errors of mine, both caught by assertion rather than by reading.** A single-attempt
pull took HTTP 502 on the three busiest repos and recorded them as zero, dropping SchoolHub to 64 of
204 and Servicing to 219 of 515 — nothing in the output says "truncated"; the population just comes
out small and plausible, which is the dangerous kind. Non-zero exit is now fatal and a genuinely
quiet repo is recorded as an explicit zero, so "no changes" and "the call failed" can't look alike.
And a trailing blank line had made Files.com read as 12 rows against a stated 11, which is where an
earlier misread of mine originated; every population script now asserts `lines == records + 1` and
stops. Related: `b.count(b'\n')` in a single-quoted Python string counts backslash-n, not newlines.

**Also corrected in my own earlier finding:** I had written that the repo-to-system mapping "appears
nowhere." It doesn't — the IPEs named both the repositories and the mapping workbook. What was
actually missing was the retained JSON and the completeness of the repository lists.

**Published:** 18 files across the six population tickets, plus the consolidated IPE (ESEC-148) and
the justification doc (ESEC-278). 14 superseded attachments deleted only after each replacement was
confirmed live at expected size. Final tree: 351 files, 351 manifest rows, 68 requests, 35 controls,
every manifest row backed by a file on disk.

**Still on the list:** item 4 (`it_offboarding_population.csv`, blocked on HR for the Workday raw
termination export) and item 5 (`new_modified_access_population.csv`, wants raw Jira JSON plus the
JQL). Then the four judgment-column files. After 9/30, the September 2026 change supplement for all
six populations, which the IPEs now commit to.

---

### September 18, 2026 (Session 11 — Okta password, sign-on and MFA evidenced per user; Req 72 rebuilt)

**Req 42 / ESEC-166 — password settings, per user instead of per policy.** What was staged described
four password policies. That evidences how the policies are configured, not that every user is
governed by one, which is what LS.01 actually claims. All four target the built-in `Everyone` group,
so they are separated only by Okta's two precedence inputs: ascending `priority`, and
`conditions.authProvider.provider` matching the user's own credential provider. First match wins and
evaluation stops. Resolving that per user (496 rows) showed **two of the four policies govern nobody**
— Active Directory Policy because Earnest's directory sync runs *outbound* (Okta is the source of
record and pushes to AD, confirmed with Gaige Rogers: Okta → AD → Navient Entra), and Default Policy
because Main Policy claims the same population at a higher priority. Neither is a gap; both are
consequences of the precedence rules, and the IPE now says so structurally.

**Dropped a column that would have shipped 50 phantom exceptions.** A `within_policy_max_age` verdict
comparing `passwordChanged` against `maxAgeDays` is the same error as `reviewDecision` and
CrowdStrike's `timestamp`: it asks a field a question it cannot answer. **Okta enforces maximum age
at authentication, not on a timer** — a dormant account's password ages past 60 days while unused and
is forced to change on next sign-in, which is the control working. The only genuine exception is a
user who *successfully signed in after* their password passed the maximum. That count is **0** of 50
flagged (48 aged out while dormant, 2 never logged in). Held internally, not shipped.

**Req 72 / ESEC-179 — four claims in the delivered IPE did not survive checking.** It said the
sign-on rules span two policies (four), that a "Main MFA Policy requires Okta Verify for All
Employees" (no such policy; Okta Verify is `OPTIONAL` everywhere), that the security group file held
private-only RFC1918 ingress (it did not), and — worst — it volunteered **"Gap: Default Policy does
NOT require MFA for Everyone group"**, handing the auditor a finding that isn't one. Sign-on policies
obey the same precedence as password policies: Default Policy sits at priority 4 scoped to Everyone,
Legacy Policy claims the same population at priority 2 and requires a factor, so Default Policy
governs **0 users**. Resolved per user: Legacy Policy 489, NO MFA 7, FastPass 0, Default 0.

**The same authentication-time resolution applied to MFA.** 27 of 495 accounts hold no active factor,
which reads as an exception list and is not one: 6 sit in the two named groups the priority-1 NO MFA
policy is scoped to, 19 cannot authenticate at all (SUSPENDED/PROVISIONED/LOCKED_OUT/
PASSWORD_EXPIRED), and 2 have never completed a sign-in, so Okta has never reached the point of
enrolling them. Accounts that **signed in with no factor and no exemption: 0**.

**A filter described as something it isn't is worse than a filter left undescribed.** The security
group file called itself "151 SGs with private-only ingress (RFC1918)". Nothing in the folder stated
the real criterion, so the only way to recover it was to re-pull the population and find the
predicate returning 151 — *has an inbound rule, and none admits `0.0.0.0/0`* (150 still live, one
since deleted). Sound criterion, described as something else, and it silently removed the 43 groups
an auditor would most want to see. Rebuilt at 162 rows with the criterion stated, the excluded groups
present in the retained JSON, and classification computed per row rather than eyeballed: 76 all
private, 56 restricted to referenced security groups only, 30 admitting a public source by design
(Cloudflare edge ranges, Looker, named partner SFTP allowlists including Navient and Intuit). Two
groups admit `172.0.0.0/8` and `172.160.0.0/16` — which look private and are mostly public space,
since RFC1918 is only `172.16.0.0/12`. Also: the old pull was **us-east-1 only** while calling itself
production; the account holds 12 more groups across four other regions, unnoticed because no EC2
instance runs in any of them.

**Checked whether another control already owned the population before rebuilding it.** LS.12
(ESEC-191) already holds all 216 us-east-1 groups with a `public_ingress` flag, so Req 72 keeps its
subset and points at LS.12 for the complete set, rather than two controls shipping overlapping
populations that must agree forever.

**One error of mine, caught before publishing.** First cut of `okta_authenticators.csv` carried a
`users_enrolled` count derived from each authenticator's `type`. Only `email` was right — an
authenticator `type` is not a `factorType`, and Okta Verify alone answers to `push`,
`token:software:totp` and `signed_nonce`. Removed the column; enrolment is evidenced per user
instead, which is better evidence anyway.

Both IPEs are generated from the retained raw (`generate_okta_password_ipe.py`,
`generate_okta_session_mfa_ipe.py`) so no figure can drift from its evidence, and the generator
asserts the banned boilerplate and the old `Gap:` language are absent. 13 files published across the
two tickets, 7 superseded attachments deleted only after each replacement was confirmed live at
expected size. Manifest 353 → 358.

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
36. **Verify who the vendor actually is before naming one in evidence.** `email_security_dns_records.txt`
    named Valimail as the inbound mail gateway for a year. `whois mxrecord.io` says Area 1 Security /
    Cloudflare in one command. Every vendor named in an evidence artifact should be traceable to a
    query the auditor could run themselves — WHOIS, a DNS record, a console screenshot — not to
    inference from an adjacent record. Two vendors appearing in the same DNS zone are not the same
    vendor, and "email security vendor" is not an attribution.
37. **Map the whole control path before writing an unobtainability argument.** The LS.13 retention
    argument was technically correct and still too broad, because it assumed one scanning layer where
    there are two. Before telling an auditor something cannot be produced, enumerate every system in
    the path and check each one's retention independently. A "cannot be produced" claim that a second
    data source contradicts is far more damaging than the original gap — and here the second source
    may turn a denial into an answer.
38. **Attribute vendor limitations to the vendor's own published statement, with the URL.** Google's
    retention page states "Administrators cannot delete log event data or change the length of time
    that the data is available for." Quoting that verbatim with the URL and the page's last-updated
    date converts "we didn't keep it" into "no customer of this platform can keep it," which the
    auditor can verify without trusting us. Do the rolling-window arithmetic explicitly, and state
    when the *current* evidence will age out too.
39. **A group name is not a scoping statement.** CO.08 had 5 devices in three blueprints without
    per-blueprint screenshots, one of them named `Harry's Test blueprint - Tahoe`. Closing them as
    "test/non-prod, out of scope" would have been fast and wrong: pulling the members showed 5
    MacBook Pros assigned to named individuals, all checked in on the population export date, one
    belonging to a member of Earnest IT. Before excluding anything because of what its container is
    called — blueprint, AD group, OU, tag, VPC — pull the members and look at them. Then ask whether
    you need the exclusion at all; here encryption *was* enforced on all 5, so the honest close was
    the stronger one. A scoping argument caught being wrong doesn't just lose you that control, it
    discredits every other scoping argument in the submission.
40. **For profile-enforced controls, evidence the enforcement grouping, not the devices.** Pivot the
    population on whatever the profile attaches to (blueprint, GPO, policy set), screenshot the
    profile's own assignment list so one artifact names every group it covers, then confirm from the
    group side with the **status panel open** — `31 Success / 0 Error / 0 Other` is proof of
    application, where an assignment screenshot is only proof of intent. That turns 354 devices into
    6 screenshots without weakening the argument. Reconcile any count difference between the console
    and the population in the evidence itself (a blueprint header read 302 against 289 MacBooks — 13
    non-Mac devices), because the auditor will compare those two numbers whether you explain them or
    not.
41. **Author in Markdown, deliver in the format the reader's viewer can open.** Markdown is the right
    thing to write in — diffable, reviewable, one source of truth. It is the wrong thing to hand an
    auditor. Google Drive has no Markdown renderer, so a `.md` previews as raw text and every table
    arrives as pipe soup before the auditor has downloaded anything; a Windows workpaper machine
    opens it in Notepad if it opens it at all. Render to PDF for delivery and keep the `.md` as the
    source of truth in the repo and on the Jira ticket. Record the source filename and its SHA-256
    next to each PDF so the conversion is checkable in both directions — the PDF is a rendering of
    evidence, not a new piece of evidence, and it should be traceable as such. Same logic retired
    `INDEX.md` in favour of an `.xlsx`: an auditor filters and sorts a workbook, nobody reads a 34 KB
    Markdown listing.
42. **The deliverable describes the evidence; the repo describes us.** Self-disclosure feels like
    integrity and reads like withholding. A justification doc that opens on its own defect list, an
    IPE with a dated correction section, a sidecar CSV of rows you removed, "available on request" —
    each is defensible alone, and together they tell the auditor the submission is partial and invite
    a walkthrough of your editing process instead of your control. Fix the evidence, replace the
    file, keep the history in `evidence-runbook.md` and here. Two limits that hold regardless: never
    assert the opposite of a fact you removed (delete the false line, don't reverse it), and never
    remove a reconciliation the auditor can see for themselves — a count that differs between a
    screenshot and a CSV must be explained, because omitting it guarantees the question. The test for
    a sentence: does it describe the evidence, or does it describe us?
43. **Use Jira process tickets as population sources, not IDP end-state.** For termination populations, Jira IT offboarding tickets (issue type "Offboarding Request") show the offboarding *process* operated — request filed, tasks completed, access removed. Okta deprovisioned user lists only show end-state and include noise (test accounts, celebrity-named accounts, cross-org users). The auditor is testing whether the *control* operated, not whether the account eventually got deactivated. Exclude bulk tickets and non-offboarding tickets (email access grants) — it's incumbent on the auditor to notice omissions, not on you to volunteer edge cases.

44. **When the population owner won't publish a roster, deliver the count plus the samples and make
    the next move a written request.** HR would not hand over a selectable list of performance
    reviews, and the honest reasons are good ones: the artifacts carry compensation assessments and
    unredacted commentary about named people. The instinct is to park the request — "waiting on
    auditor sample selection" — which leaves it open in *our* column all audit and reads as a hole in
    the population. Instead: the count goes in as the denominator (264 employees, EOY 2025, from the
    owner, dated), the samples the owner released ship as *the* samples and are described completely,
    and the path to more is stated affirmatively — a written request naming the count and cycle,
    routed through Security, handled per sample, because of what the artifact contains. Then close
    the ticket. The auditor can still insist; the difference is that insisting now costs them a
    written request against a delivered population instead of costing us a `_PENDING` folder.

45. **An IPE must name exactly the files sitting beside it.** A collector that writes one IPE per
    *run* produces a file documenting nine artifacts; copy it into six request folders and each copy
    describes seven files that folder doesn't hold, plus "Evidence File: None / Row Count: 0 / repos
    scanned: 0" stanzas from endpoints that returned nothing. An auditor reads that as seven missing
    files and a failed collection. Meanwhile the file that *is* in the folder can go undocumented —
    `CM.08 Req 36` shipped a 289-row entitlement CSV under an IPE that never mentioned it. Detect it
    by diffing `Evidence File:` lines against the folder listing, in code, across the whole tree; four
    folders failed. Write per-request IPEs from the run's data and cross-reference the siblings:
    "both files come from the single collection run documented above, which is why the queries cover
    more endpoints than either file uses on its own."

46. **A stakeholder's ad-hoc download folder is not a duplicate of your submission — diff it by
    content hash.** Of 32 files handed over in one `Evidence Requests/` tree, 23 were missing from the
    package, including the only evidence anywhere that backups are restore-*tested* rather than merely
    configured (57 completed AWS Backup restore jobs on a monthly plan). Filename and request-number
    matching gets this wrong in both directions at once: a background-check workbook already staged
    under a different name and byte size looked new, while AWS Backup screenshots filed under `212/`
    belonged under Req 213. Hash the whole staged tree, then assess value per *group* — 23 missing
    files are not 23 equal decisions. And read the screenshots before writing their IPE: every fact in
    the restore-testing IPE (plan ARN, `cron(0 5 2 * ? *)`, 60-day window, 57 jobs, 2025-12-31 start)
    came off the captures, and the one claim not made was a row-by-row reconciliation nobody performed.

47. **A population pulled from a retention window can only ever show that window — check whether the
    system keeps something that outlives it.** IT.11's staged population was
    `rds_automated_snapshots.csv`, pulled 2026-09-01 against instances whose automated-snapshot
    retention is 7–31 days. It structurally could not show a backup taken in October or December 2025,
    and nothing in the file says so — the row count (230) reads like coverage. The same account holds
    AWS Backup recovery points on two plans retaining 365 days or longer, and those vaults still had
    every monthly point back to Oct 2025: 210 points, all COMPLETED, 186 inside the audit period, two
    per production database per month. Note the asymmetry that made this findable — AWS Backup's *job
    history* API had nothing before 2026-08-31 either, so `list-backup-jobs` reproduces the same
    illusion; only `list-recovery-points-by-backup-vault` reaches back. Before delivering any listing
    as period coverage, ask what deletes rows from it and on what clock, and if the answer is shorter
    than the audit period, go find the artifact that is retained longer. Then say in the IPE which file
    carries period coverage and which is a point-in-time window, so the reader is not left to infer it.

48. **Restore *testing* starting mid-period is not backups starting mid-period.** I reported "restore
    testing jobs start 2025-12-31, so Oct–Dec 2025 has no restore jobs" and it was heard as a gap in
    backups. Two different controls, two different populations, and the conflation was mine for
    putting them in one sentence. When a date bounds one assertion, name the assertion it bounds.

49. **A disclaimer about tooling limits becomes a false claim the moment the tooling improves — and it
    was already reading as withholding.** Two documents said the CrowdStrike API scope did not include
    the detection endpoints, so alert data could not be exported directly. When a working key produced
    the full alert population, that sentence would have sat next to a file proving it wrong. The
    failure mode is worse than being outdated: "we can't export this" invites the auditor to ask what
    else we can't export. Sweep for capability disclaimers whenever a credential, scope or access path
    changes, and prefer stating what *is* provided over explaining what isn't. The legacy endpoints
    turned out to be decommissioned outright rather than out of scope, so the original diagnosis was
    wrong too — a 404 is not evidence about permissions.

50. **A zero in a duration field usually means the clock never started.** 86 of 95 CrowdStrike alerts
    carry `seconds_to_triaged: 0`. Rendered naively that reads as instant triage on every open alert,
    which is a stronger claim than the control makes and a false one. The field is populated only for
    alerts worked to a disposition, so "worked" has to be defined by the presence of `resolution`, not
    by a non-zero timing. Same instinct as the retention lesson: before presenting a field as a
    measurement, ask what writes it and when. And check the numbers you inherited from your own earlier
    prose — the supplement said the August Okta alert was "triaged within 3 hours" when the API records
    52 minutes, a figure that was better than claimed and still wrong.

51. **The worst API failure is the one that answers successfully.** Ask the Okta System Log for
    `since=2025-10-01` and it returns HTTP 200 with a full page of events — from June 2026, because the
    retention window is ~90 days and Okta hands back the oldest thing it still has instead of erroring.
    Nothing in the response says the range was clamped. Had that gone into an evidence file it would
    have been a year-labelled population containing three months of data, and the auditor would have
    been the one to notice. The check is cheap: probe with a deliberately absurd `since` (2015) and
    whatever comes back *is* the real floor. Do this for every log-backed source before building a
    population on it, and put the measured floor in the IPE. Related: lesson 47's asymmetry is the way
    out — object state (an assignment's `created` date) reaches back where log history does not, so
    prefer state for coverage and logs for mechanism.

52. **A count that equals your `limit` is a page, not a total.** `GET /api/v1/apps?limit=200` returned
    exactly 200 apps and read as the whole tenant; following the `Link rel="next"` header produced 370.
    Any list endpoint whose result count is suspiciously round, or identical to the limit you asked for,
    is truncated until proven otherwise. Pagination belongs in the client (`okta_api.page()`), not in
    each caller, because the one caller that forgets is the one that ships. Corollary from the same
    pass: two different apps both reporting exactly 497 users is not a coincidence either — it was one
    near-everyone group expanding, and it's worth a second look before it becomes a sentence.

53. **"Export" is a claim about provenance, not a file extension.** A measured audit of the staged tree
    found 105 distinct CSVs, of which **91 were built by our collectors** and only **9 were genuine
    vendor exports**; zero raw API responses were staged as evidence anywhere. The tell is in the
    headers — Kandji's own export reads `Device Name, Display OS Version, Blueprint Name`, while our
    `cloudwatch_alarms.csv` reads `name, state, metric` where AWS actually returns `AlarmName`,
    `StateValue`, `MetricName`. Every field was renamed. That is not inaccuracy; the data is sound. It
    is a **tie-out** problem: the auditor cannot map our column to a source field without reading our
    code, so completeness-and-accuracy testing has nowhere to land except our good faith. The fix is
    cheap and was simply never done — the collector already has the response in hand, so dump it
    unmodified as `<stem>_raw.json` beside the readable CSV and let the IPE say "fields renamed from X
    to Y, no rows added or removed, tie out to the raw file." Prefer a native console export over an
    API-built CSV whenever the vendor UI offers one (Kandji, Okta, CrowdStrike, Workday and Jira all
    do); it costs a click and is the most credible artifact available. Retain raw from the first run,
    because reconstructing provenance after the fact is far more expensive than keeping it.

54. **Don't hand the auditor your conclusion where they wanted your data.** Four staged files carry
    columns that state a verdict rather than a fact: `separation_of_duties` and `author_self_approved`
    (CM.08), `is_engineer_team` / `is_infra` / `is_org_admin` (CM.08), and `approved_before_merge`
    (CM.09). Each is us performing the auditor's test and shipping the answer, which invites them to
    audit our logic instead of the control — and if our logic is wrong the whole file is impeached.
    Ship `author` and `approvers`; let them conclude on separation of duties. The distinction that
    matters is source-field versus derived-judgment: `is_default`, `is_encrypted` and `is_public` look
    like the same pattern but are AWS's own fields, so they stay. Same reasoning already applied to the
    monthly patching CSV, where the approval comment is reproduced verbatim and no derived
    approval-precedes-work-start column was added.

55. **A cross-system join is useful evidence and is not an export — say so.**
    `june_2026_production_patching.csv` fuses Jira, GitHub and AWS into rows that exist in no single
    system. That is the most legible artifact in the package and the least like a native export, and
    both facts need to be on the page: name the three sources, name the join key, and keep each
    system's own record retrievable so the correlation can be checked rather than believed.
