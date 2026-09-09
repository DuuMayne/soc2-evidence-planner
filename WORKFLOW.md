# SOC 2 Evidence Collection Workflow

How we ran the 2026 SOC 2 Type II evidence collection at Earnest, what worked, what didn't, and how to replicate it.

## Architecture

```
Auditor Request List (.xlsx)
    ↓ parsed into
Jira ESEC tickets (94 tickets across ~35 controls)
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
├── files_com/
│   ├── files_com_okta_users.csv                 # 62 users via Okta SCIM
│   ├── files_com_new_accounts_audit_period.csv  # 30 new accounts in period
│   └── IPE_documentation.txt                    # IPE for Okta API pull
├── github/
│   ├── *_change_population.csv  # Per-product change populations
│   ├── pr_review_separation_of_duties.csv
│   └── entitlements_and_devs/   # Org members, teams, permissions
├── patching_evidence/           # EKS updates, RDS configs, Jira tickets
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
