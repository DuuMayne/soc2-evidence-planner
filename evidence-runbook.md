# Evidence Collection Runbook

Operational playbook for SOC 2 Type II evidence collection at Earnest. Documents every evidence request, the exact steps to collect it, source systems, API calls, and automation status.

**Audit period:** 10/1/2025 – 9/30/2026
**ESEC project:** meetearnest.atlassian.net, workstream ESEC-137

---

## How to Read This Runbook

Each entry follows this structure:

```
### ESEC-NNN: Req X — [Title]
- **Control family:** Parent task name
- **Evidence type:** Population | Config | Screenshot | Report | Policy | Sample | IPE
- **Status:** ✅ Done | 🔄 In Progress | ⬜ To Do
- **Source systems:** Jira, GitHub, AWS, Okta, Confluence, Google Workspace, Files.com
- **Automation:** full | partial | manual | not started
- **Collection steps:** Numbered steps with exact API calls or CLI commands
- **Output files:** What gets generated
- **IPE requirements:** What auditors need to see for completeness/accuracy
- **Lessons learned:** Gotchas from the 2026 collection
```

---

## Change Management (ESEC-141)

### ESEC-142–147: Req 27 — Change Populations (per product)
- **Evidence type:** Population
- **Status:** ✅ Done (GitHub-based, 6 products)
- **Source systems:** GitHub Search API via `gh` CLI
- **Decision:** Switched from Jira tickets to GitHub PRs as source of truth — more complete coverage, limits auditor exposure to observation window only
- **Repo mapping:** `~/Downloads/Repo List with Unit Test Coverage .xlsx` — team sheets map repos to products
- **Collection steps:**
  1. For each product's repos (from mapping spreadsheet):
     `gh search prs "repo:meetearnest/{repo}" --merged --merged-at "2025-10-01..2026-09-04" --limit 1000 --json repository,number,title,url,author,updatedAt`
  2. Parse and combine into per-product CSVs
- **Output directory:** `evidence/github/`
- **Output files and counts:**
  - `slo_platform_change_population.csv` — 388 PRs (15 repos)
  - `schoolhub_spoke_change_population.csv` — 204 PRs (4 repos)
  - `cashi_change_population.csv` — 140 PRs (1 repo)
  - `mmax_change_population.csv` — 216 PRs (18 repos)
  - `servicing_platform_change_population.csv` — 508 PRs (12 repos)
- **Files.com:** ESEC-146 uses vendor change logs (not GitHub) — evidence in Google Drive
- **Lessons learned:**
  - GitHub Search API rate limits at ~30 req/min for search — add retries with backoff
  - Some repos return 403 briefly then succeed on retry
  - GitHub yields more complete change populations than Jira (388 PRs vs 107 tickets for SLO)
  - `--merged-at` filter defines the observation window — critical for limiting auditor scope
  - Product definitions: CASHI = Certification Approval School Hub Interface, MMAX = School Success Disbursement Platform, SchoolHub = also called Spoke

### ESEC-148: Req 28 — IPE for All Change Populations
- **Evidence type:** IPE
- **Status:** ✅ Done (included in GitHub pull metadata)

### ESEC-149: Req 29 — Change Ticket Samples
- **Evidence type:** Sample
- **Status:** ⬜ To Do (depends on auditor sample selection)
- **Source systems:** Jira Cloud API + GitHub API
- **Collection steps:** When auditor selects PRs from population:
  1. Pull full PR details: `gh pr view {num} --repo meetearnest/{repo} --json`
  2. Pull review approvals: `gh api repos/meetearnest/{repo}/pulls/{num}/reviews`
  3. Cross-reference with Jira ticket if linked in PR title
  4. Build correlation: GitHub PR → review approval → merge → (optional) Jira ticket

---

## Environment Segregation (ESEC-150)

### ESEC-150: CM.07 — Environment Segregation (parent)
- **Evidence type:** Config
- **Status:** ✅ Done
- **Source systems:** AWS Organizations, EC2
- **Output directory:** `evidence/aws/env_segregation/`
- **Output files:** `aws_organization_accounts.csv` (22 accounts), `vpc_configurations.csv` (10 VPCs), `environment_resource_inventory.csv`, `system_resource_mapping.csv`, `IPE_documentation.txt`
- **Key evidence:** 22 AWS accounts including dedicated Production (075440130607), Development (747722821363), Staging (831351477977), Sandbox, Alpha, and Logging accounts. VPCs use non-overlapping CIDR ranges.

### ESEC-151 through ESEC-156: Req 35 — Environment Segregation (per system)
- **Evidence type:** Screenshot/Config
- **Status:** ✅ Done
- **Source systems:** AWS Organizations API, AWS EC2/EKS/RDS APIs
- **Automation:** Manual collection via AWS CLI (not yet in collector)
- **Collection steps:**
  1. `aws organizations list-accounts --profile production` → lists all 22 AWS accounts
  2. Confirm account-level segregation: Dev (747722821363), Staging (831351477977), Prod (075440130607)
  3. In production account:
     - `aws eks list-clusters --region us-east-1 --profile production`
     - `aws rds describe-db-instances --region us-east-1 --profile production`
     - `aws ec2 describe-vpcs --region us-east-1 --profile production`
  4. In dev account (same commands with `--profile security-dev`)
  5. Build system-to-resource mapping from naming conventions
  6. Write CSVs: `aws_organization_accounts.csv`, `environment_resource_inventory.csv`, `system_resource_mapping.csv`
- **Output directory:** `evidence/aws/env_segregation/`
- **IPE requirements:** AWS caller identity (STS), account IDs, region coverage, pagination tokens checked
- **Lessons learned:**
  - Dev account us-west-2 denied by SCP — this is itself evidence of access control
  - Staging account exists but no SSO profile configured — listed in org accounts CSV
  - System-to-resource mapping relies on naming conventions — needs manual review
  - Uploaded to Jira tickets ESEC-151 through ESEC-156 with ADF comments

---

## Production Change Entitlements & Code Developers (ESEC-157)

### ESEC-158: Req 36 — Production Change Entitlements
- **Evidence type:** Config
- **Status:** ✅ Done
- **Source systems:** GitHub API via `gh` CLI
- **Automation:** Manual collection via `gh` CLI
- **Collection steps:**
  1. `gh api /orgs/meetearnest/members --paginate -q '.[].login'` → 160 org members
  2. `gh api /orgs/meetearnest/members?role=admin --paginate` → 7 admins
  3. `gh api /orgs/meetearnest` → confirm `default_repository_permission: none` (not write!)
  4. `gh api /orgs/meetearnest/teams --paginate` → list all teams and their repo access
  5. For each in-scope repo: `gh api /repos/meetearnest/{repo}/branches/main` → `protected: true/false`
  6. Build entitlements matrix: team → repos → permission level
- **Output directory:** `evidence/github/entitlements_and_devs/`
- **Output files:** `production_change_entitlements.csv`, `branch_protection_rules.csv`
- **Lessons learned:**
  - `gh` CLI works better than PAT — authenticated as DuuMayne with `repo` + `read:org` scopes
  - Branch protection details API returns 404 for non-admins; use branch endpoint `protected` flag instead
  - Org base permission initially assumed "write" because all teams showed 747 repos — actually `none`
  - `outside_collaborators` endpoint needs `admin:org` scope — noted in IPE as limitation

### ESEC-159: Req 37 — Code Developers List
- **Evidence type:** Population
- **Status:** ✅ Done
- **Source systems:** GitHub API via `gh` CLI
- **Collection steps:**
  1. `gh api /orgs/meetearnest/members --paginate` → 160 members with login, role, URL
  2. `gh api /orgs/meetearnest/outside_collaborators --paginate` → 13 collaborators (from PAT collection)
  3. Merge into `code_developers_list.csv`
- **Output files:** `code_developers_list.csv`

### ESEC-160: Req 38 — IPE for Code Developers List
- **Evidence type:** IPE
- **Status:** ✅ Done
- **Output files:** `IPE_documentation.txt`, `IPE_documentation.json`

---

## Patching (ESEC-161)

### ESEC-162: Req 39 — Patching Jira Tickets (Sample Months)
- **Evidence type:** Report
- **Status:** 🔄 In Progress (evidence collected, correlation built)
- **Source systems:** Jira Cloud API + AWS EKS API + GitHub API
- **Automation:** Partially automated via `collectors/jira_collector.py`
- **Collection steps:**
  1. **Jira tickets:** Query SRE project for patching tickets in sample months:
     - Oct 2025: `project = SRE AND labels = patching AND resolved >= "2025-10-01" AND resolved <= "2025-10-31"`
     - Dec 2025: same pattern
     - Jun 2026: same pattern
  2. **AWS EKS updates:** For each cluster, pull update history:
     - `aws eks list-updates --cluster-name <cluster> --region us-east-1 --profile production`
     - `aws eks describe-update --cluster-name <cluster> --update-id <id>` for each update
  3. **RDS patching config:** `aws rds describe-db-instances` → extract `AutoMinorVersionUpgrade` flag
  4. **June 2026 correlation chain:**
     - Find Jira SRE-1658 (June patching ticket)
     - Search `legoland` repo for related PRs: `gh pr list --search "eks upgrade" --state merged`
     - Match specific PRs to EKS cluster version updates
     - Build correlation: Jira SRE-1658 → 4 GitHub PRs (with peer-review approvals) → 5 AWS EKS VersionUpdate records
- **Output directory:** `evidence/patching_evidence/`
- **Output files:**
  - `jira_patching_tickets_sample_months.csv`
  - `jira_all_patching_tickets.csv`
  - `eks_cluster_updates.csv`
  - `eks_addon_versions.csv`
  - `rds_patching_config.csv`
  - `github_june_patching_prs.csv`
  - `june_2026_patching_correlation.csv`
- **IPE requirements:** Three-source correlation: Jira work ticket → GitHub PR (approval) → AWS infrastructure change
- **Lessons learned:**
  - IaC lives in `legoland` repo (Terraform/Terragrunt), not infra-live-production or nets-gitops
  - Don't bulk-dump all PRs — auditors want a specific correlation chain for each sample
  - EKS upgrades go through peer-reviewed PRs in legoland

---

## Network & Firewall (ESEC-191)

### ESEC-191: LS.12 — Network Security Configuration
- **Evidence type:** Config
- **Status:** ✅ Done (post-remediation re-pull 2026-09-04)
- **Source systems:** AWS EC2 API (Production 075440130607)
- **Collection steps:**
  1. `aws ec2 describe-security-groups --region us-east-1 --profile production` → 216 SGs
  2. `aws ec2 describe-network-acls --region us-east-1 --profile production` → 9 NACLs
  3. Parse all inbound rules (1,232 total), flag public ingress (0.0.0.0/0)
  4. Verify remediation of 8 previously-flagged orphaned SGs
- **Output directory:** `evidence/aws/network_security/`
- **Output files:** `security_groups.csv`, `security_group_rules_detail.csv`, `network_acls.csv`, `IPE_documentation.txt`
- **Key findings:**
  - 43 SGs with public ingress — all legitimate (ALB/ELB 80/443, K8s ingress, Banyan access tiers)
  - 7/8 orphaned SGs removed by infra. 1 remaining is default VPC SG (cannot be deleted)
  - All 9 NACLs have deny-all default rules (rule 32767 DENY ALL)
  - No SSH (22), RDP (3389), or database ports exposed to 0.0.0.0/0
- **Lessons learned:**
  - Always check for orphaned SGs (created by launch wizards, OpsWorks, etc.) before presenting to auditors
  - Flag remediation items early — infra team needs lead time to review and delete
  - Default VPC SG (sg-0d2f0bee1aaf60b7e) can't be deleted, but it has no custom rules

### ESEC-192: Req 92 — Network Diagram
- **Evidence type:** Diagram
- **Status:** 🔄 In Progress (raw data collected, needs visual diagram)
- **Source systems:** AWS EC2 API
- **Collection steps:**
  1. `aws ec2 describe-vpcs --region <region> --profile production`
  2. `aws ec2 describe-route-tables --region <region> --profile production`
  3. `aws ec2 describe-internet-gateways --region <region> --profile production`
  4. `aws ec2 describe-nat-gateways --region <region> --profile production`
  5. `aws ec2 describe-subnets --region <region> --profile production`
  6. Still needs: visual diagram generation from the raw data
- **Output directory:** `evidence/aws/20260901_111842/`

### ESEC-193: Req 93 — Firewall Deny-All Rules
- **Evidence type:** Config
- **Status:** ✅ Done (covered by ESEC-191 network_acls.csv showing deny-all defaults)

### ESEC-195: Req 95 — Security Group VPN-Only Access
- **Evidence type:** Config
- **Status:** ✅ Done (post-remediation)
- **Source systems:** AWS EC2 API
- **Output directory:** `evidence/aws/network_security/` (shared with ESEC-191)

---

## Security Incidents (ESEC-232)

### ESEC-233–236: Req 138–141 — Security Incidents
- **Evidence type:** Population / IPE / Samples
- **Status:** ⬜ To Do (evidence cleared — user building manually)
- **Decision:** All automated incident evidence was removed. User will build the incident population manually to:
  - Include Slack-only incidents that don't have Jira tickets
  - Exclude incidents without full PIR documentation
  - Exclude still-open incidents
  - Control auditor exposure to the incident portfolio
- **Lessons learned:**
  - Automated Jira pulls captured 178 items including alerts, bugs, and operational incidents — too broad
  - Auditors only need to see incidents with complete post-incident reviews (PIRs)
  - If "no incidents" applies, need confirmation from 2 individuals (Req 140)
  - Better to curate manually than show auditors unfinished work

---

## Backups (ESEC-263 / ESEC-265–268)

### ESEC-265: Req 212 — Server Backup Listings
- **Evidence type:** Population
- **Status:** ✅ Done
- **Source systems:** AWS RDS API, AWS Backup
- **Collection steps:**
  1. `aws rds describe-db-instances --region us-east-1 --profile production` → 25 instances
  2. Extract backup config: `BackupRetentionPeriod`, `PreferredBackupWindow`, `LatestRestorableTime`
  3. `aws backup list-backup-plans --profile production` → 3 backup plans
- **Output directory:** `evidence/aws/backup_monitoring/`
- **Output files:** `rds_backup_configs.csv`, `backup_plans.json`

### ESEC-266: Req 213 — Backup Config & Summary Samples
- **Evidence type:** Sample
- **Status:** ✅ Done (auditor selects specific servers)
- **Source systems:** AWS RDS API

### ESEC-267: Req 214 — Backup Failures List
- **Evidence type:** Population
- **Status:** ✅ Done
- **Source systems:** AWS RDS API
- **Collection steps:**
  1. `aws rds describe-events --source-type db-instance --event-categories backup --duration 20160` (14 days)
  2. Filter for failure events → none found
  3. Write `no_backup_failures.txt` confirmation + `backup_events.csv` (244 events, all success)
- **Output directory:** `evidence/aws/backup_production/`

### ESEC-268: Backup Monitoring Configuration
- **Evidence type:** Config
- **Status:** ✅ Done
- **Source systems:** AWS RDS Event Subscriptions, AWS Backup Vault Notifications
- **Collection steps:**
  1. `aws rds describe-event-subscriptions --profile production` → 11 subscriptions
  2. `aws backup list-backup-vaults --profile production` + `get-backup-vault-notifications` per vault
  3. Verify BACKUP_JOB_FAILED events route to SNS → PagerDuty/email
- **Output directory:** `evidence/aws/backup_monitoring/`
- **Output files:** `rds_event_subscriptions.csv`, `backup_vault_notifications.json`
- **Lessons learned:**
  - Security-dev account had zero monitoring — always pull from production for evidence
  - Production has comprehensive alerting: 11 RDS event subs + vault notifications
  - Always verify AWS account ID in evidence (burned once pulling from wrong account)

---

## Developer Training (ESEC-247)

### ESEC-248: Req 175 — Confluence Developer Training
- **Evidence type:** Screenshot/Catalog
- **Status:** 🔄 In Progress (evidence collected and uploaded)
- **Source systems:** Confluence Cloud REST API
- **Automation:** Manual collection via Confluence REST API
- **Collection steps:**
  1. Search Confluence using CQL across EN, ITO, SEC spaces:
     - 13 text searches: "developer training", "engineering onboarding", "best practices", "coding standards", "security training", "code review", "engineering standards", "engineering guidelines", "runbook", "development guide", "code review process", "deployment process", "new hire"
  2. Traverse page trees:
     - Engineering Home → children
     - New hire guide → Engineering Onboarding → children (Environment Setup, Standard Engineering Accounts, etc.)
     - Security Champions Program Overview → children
  3. For each relevant page, pull metadata:
     - `GET /wiki/rest/api/content/{id}?expand=version,history,space,ancestors`
     - Extract: title, space, version count, created date/by, last modified date/by, page path
  4. Categorize into: Onboarding (9), Security Training (5), Best Practices (9), Process (4)
  5. Write evidence CSV with all metadata + relevance descriptions
- **Output directory:** `evidence/confluence/developer_training/`
- **Output files:** `confluence_training_catalog.csv`, `evidence_summary.txt`, `IPE_documentation.txt`, `IPE_documentation.json`
- **Key findings:**
  - 27 training pages, 447 total versions, 8 updated in audit period
  - Security Champions Program created Jan 2026
  - Engineering Onboarding: 68 versions (since 2015)
  - Confluence API uses same credentials as Jira (Atlassian Cloud shared auth)

---

## Policy Documentation (Confluence Sweep)

### ESEC-140: SDLC & Change Management Policy
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Source systems:** Confluence Cloud REST API + PDF policy documents
- **Automation:** `collectors/replace_policy_evidence.py`
- **Collection steps:**
  1. CQL search across 6 Confluence spaces (EN, SEC, POL, IN, ITO, Enablement) with 42 search terms
  2. Page tree traversals for Engineering Home, Security@Earnest, POL space (14 trees)
  3. Pull metadata for each page: `GET /wiki/rest/api/content/{id}?expand=version,history,space,ancestors`
  4. Map pages to ESEC tickets by relevance (best-fit matching)
  5. All stale policy pages refreshed on 2026-09-03
  6. Upload evidence: policy_mapping.csv + IPE + relevant PDFs
- **Output directory:** `evidence/confluence/policy_sweep/`
- **Output files:** `policy_mapping.csv` (49 page-to-ticket mappings), `IPE_documentation.txt`
- **PDF evidence:** Earnest SDLC Policy (Navient format), Navient CISP, Docker/K8s Security, Definition of Done, JIRA Practices
- **Confluence pages:** 14 pages — SDLC Policy, SDLC Process, Change Mgmt, Release Mgmt, Infra Change Mgmt, Code Review, Peer Review, Definition of Done, Eng Release Process, Navient SDLC, JIRA Practices, Going Merry Addendum, Data Broker Change Mgmt, SDLC Refresh
- **Lessons learned:**
  - 36 of 49 original pages were stale (pre audit period) — all 24 critical ones refreshed 2026-09-03
  - Navient CISP (55pp) is the most comprehensive parent policy — maps to 6 of 7 tickets
  - Use `replace_policy_evidence.py` for future refreshes — handles delete + re-upload + comment in one pass
  - Old attachments must be deleted before re-uploading to avoid duplicates (GET attachment list, DELETE by ID)

### ESEC-165: Network Authentication Policy
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 6 pages — DLP Plan, Data Classification, Key Management, Transit Gateway VPN, AWS Security Standard, InfoSec Programs
- **PDF evidence:** Navient CISP, Navient AUP, Wireless LAN Security Standard, BYOD Policy

### ESEC-175: Access Management Policy
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 5 pages — User Access Mgmt Procedure, Access Reviews (DRAFT), Privilege Access Mgmt, SailPoint Certifications, Clean Desk Policy
- **PDF evidence:** Navient CISP, Navient AUP, IAM Policy, BYOD Policy

### ESEC-188: Database Rules Document
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 3 pages — Database Guidelines, ERD Review Process, ERD Training & Resources
- **PDF evidence:** None (Confluence pages only)

### ESEC-194: Network Traffic Settings Policy
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 5 pages — Cloudflare Runbook, WAF Rule Standardization, Docker/K8s Security, AWS Security Standard, Transit Gateway VPN
- **PDF evidence:** Navient CISP, Wireless LAN Security Standard, Docker/K8s Security

### ESEC-255: Vulnerability Management Policy
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 5 pages — Vulnerability Management (POL), Vulnerability Management (SEC), Container Image Vuln Mgmt, Patch Management SLA, Supply Chain Attacks Prevention
- **PDF evidence:** Navient CISP

### ESEC-262: IT CP & IT DRP
- **Evidence type:** Policy
- **Status:** ✅ Done
- **Confluence pages:** 11 pages — IT CP/DRP master + 5 sections + 3 appendices, BC/DR, Incident Response Plan
- **PDF evidence:** Navient CISP, Physical Security Policy, Section 3 Incident Management

---

## Secure Data Transmission (ESEC-223)

### ESEC-224: Req 132 — Secure Transmission Configurations
- **Evidence type:** Config
- **Status:** 🔄 In Progress (AWS done, needs tool-specific screenshots)
- **Source systems:** AWS ACM, ELBv2, CloudFront
- **Collection steps:**
  1. `aws acm list-certificates --certificate-statuses ISSUED --profile production` → 10 certs
  2. `aws acm describe-certificate --certificate-arn <arn>` for each → full TLS details
  3. `aws elbv2 describe-load-balancers --profile production` → 52 load balancers
  4. `aws elbv2 describe-listeners --load-balancer-arn <arn>` for each → 68 listeners (44 HTTPS/TLS)
  5. `aws cloudfront list-distributions --profile production` → 0 distributions (not used in prod account)
- **Output directory:** `evidence/aws/secure_transmission/`
- **Output files:** `acm_certificates.csv`, `alb_tls_configurations.csv`, `cloudfront_no_distributions.txt`, `IPE_documentation.txt`
- **Still needed:** Tool-specific TLS configs for Airflow, Looker, Sign Service, Files.com (stakeholder screenshots)
- **Lessons learned:**
  - CloudFront returned empty response (not error) when no distributions exist — handle gracefully
  - SSL policy names on ALB listeners (e.g., `ELBSecurityPolicy-TLS13-1-2-2021-06`) are the key evidence for TLS version enforcement

---

## Scheduled Jobs (ESEC-225)

### ESEC-226: Req 133 — Scheduled Jobs Configuration
- **Evidence type:** Config
- **Status:** 🔄 In Progress (AWS done, needs tool-specific configs)
- **Source systems:** AWS EventBridge
- **Collection steps:**
  1. `aws events list-rules --profile production` → 59 rules (47 scheduled, 12 event-driven)
  2. `aws events list-targets-by-rule --rule <name>` for each scheduled rule → target mappings
  3. `aws scheduler list-schedules --profile production` → 0 schedules (Scheduler service not used)
- **Output directory:** `evidence/aws/scheduled_jobs/`
- **Output files:** `eventbridge_rules.csv`, `eventbridge_rule_targets.csv`, `IPE_documentation.txt`
- **Still needed:** Tool-specific job configs for Airflow, Looker, Sign Service, Files.com

---

## Separation of Duties (ESEC-157)

### ESEC-157: CM.08 — Production Change Separation of Duties
- **Evidence type:** Config/Data
- **Status:** ✅ Done
- **Source systems:** GitHub API via `gh` CLI
- **Collection steps:**
  1. For each in-scope product (SLO, Servicing, CASHI, MMAX, SchoolHub):
     - Select key repos from the product mapping
     - `gh pr list --repo meetearnest/{repo} --state merged --limit 5 --json number,title,author`
     - `gh api repos/meetearnest/{repo}/pulls/{num}/reviews --jq '[.[] | {state, user: .user.login}]'`
  2. Compare PR author against reviewers — check for self-approval
  3. Export: `pr_review_separation_of_duties.csv` (75 PRs sampled)
- **Output directory:** `evidence/github/`
- **Output files:** `pr_review_separation_of_duties.csv`, `IPE_separation_of_duties.txt`
- **Key findings:** 75/75 PRs (100%) had approval from someone other than the author
- **Lessons learned:**
  - Branch protection API returns 404 for non-admin users — use PR review data instead
  - Some repos use `master` as default, others use `main` — check with `gh api repos/meetearnest/{repo} --jq '.default_branch'`
  - Org-level rulesets require `admin:org` scope — noted as limitation

---

## Change Populations via GitHub (ESEC-141/142–148)

### Change Population Collection (GitHub-based)
- **Evidence type:** Population
- **Status:** ✅ Done (6 products)
- **Source systems:** GitHub Search API via `gh` CLI
- **Decision:** Used GitHub PRs (not Jira tickets) as source of truth for code changes — gives broader coverage and limits auditor exposure to the observation window only
- **Collection steps:**
  1. Load repo-to-product mapping from "Repo List with Unit Test Coverage .xlsx"
  2. **Set the window bounds as constants first, from the observation window — never from `date`.**
     `WINDOW_START=2025-10-01; WINDOW_END=2026-08-31`
  3. For each product's repos:
     `gh search prs "repo:meetearnest/{repo}" --merged --merged-at "$WINDOW_START..$WINDOW_END" --limit 1000`
  4. Extract: repo, pr_number, title, url, author, merged_date
  5. **Assert the bounds after the pull:** `max(merged_date) <= WINDOW_END` and
     `min(merged_date) >= WINDOW_START`, per population. Fail loudly, don't warn.
  6. Write per-product CSV
- **Output directory:** `evidence/github/`
- **Output files (corrected 2026-09-14):**
  - `slo_platform_change_population.csv` — 376 PRs
  - `schoolhub_spoke_change_population.csv` — 204 PRs
  - `cashi_change_population.csv` — 140 PRs
  - `mmax_change_population.csv` — 216 PRs
  - `servicing_platform_change_population.csv` — 505 PRs
  - `file_transfer_service_change_population.csv` — 11 PRs
  - Consolidated total: **1,441** merged PRs
- **Lessons learned:**
  - ⚠️ **Bound the query on the observation window end, not the collection date.** The first pull
    used `merged:2025-10-01..2026-09-04` — 9/04 was simply the day the script ran. That put PRs
    merged September 1–4, 2026 into two populations that are scoped to end 8/31/2026: SLO 388→376
    (12 rows) and Servicing 508→505 (3 rows). Found on 9/14 *after* the populations had already
    been submitted to the auditor, so it had to be disclosed and re-uploaded rather than quietly
    fixed. The window end is a fixed constant for the whole audit; hardcode it once at the top of
    the script and assert against it after every pull.
  - When trimming a submitted population, write the removed rows to a
    `*_excluded_out_of_period.csv` sidecar and attach it alongside. A row count that silently
    drops between submissions is an IPE completeness problem; an itemized exclusion list is not.
    See `analysis_sept14/trim_change_populations.py`.
  - GitHub Search API rate limits at ~30 req/min for search — add retries with backoff
  - Some repos return 403 briefly then succeed on retry (e.g., `partner`, `lfm-integration-service`)
  - Repo names don't always match product names — mapping spreadsheet is essential
  - GitHub yields more complete change populations than Jira (376 PRs vs 107 Jira tickets for SLO)

---

## Access Rights Reviews — LS.07 (ESEC-181/182/183/184)

### ESEC-181/183: Req 73 & 75 — Entitlement Review Evidence for Sample Quarters
- **Evidence type:** Population / Report / Sample
- **Status:** ✅ Done (both sample quarters)
- **Source systems:** Entitlement Review Worksheet (.xlsx), Jira (IT, ENABLE, SEC, CH, DNA, FULL, ID projects)
- **Automation:** partial — the worksheet is manually maintained; ticket pull and packaging are scripted
- **Sample quarters:** Q4 2025 and Q2 2026 (selected by Baker Tilly)

**⚠️ Read this before touching LS.07 evidence — cycle naming.** Earnest ran access reviews
*retroactively* through the first half of the audit period: a cycle is named for the quarter whose
**entitlements** were reviewed, and the review is **performed the following quarter**. So the
**Q1 2026 cycle is the review that operated during Q2 2026** and is the Q2 2026 sample-quarter
evidence. The worksheet filename encodes it: `2026 Q1_2 Entitlement Review Worksheet` = Q1
entitlements reviewed in Q2. **Never rename that file** — the `_2` is the proof of coverage.
The convention has since changed to name a cycle for the quarter the review is performed in, so
**cycle names alone tell you nothing about timing.** Always resolve by ticket created/resolved
dates, and record the answer in a `Covers Sample Quarter` column.

| Cycle | Performed | Covers sample quarter | Cycle tickets |
|---|---|---|---|
| Q4 2025 | Jan 29 – Jul 7, 2026 | Q4 2025 | IT-20286, IT-20593 (+ remediation IT-20632, IT-20640, IT-21038) |
| Q1 2026 | May 13 – Jul 14, 2026 | **Q2 2026** | IT-21054, IT-21195 (+ remediation IT-21430) |

- **Collection steps:**
  1. Get the cycle's worksheet. Copy it byte-for-byte (`shutil.copy2`) and **verify SHA-256 against
     the source** — the worksheet is the primary artifact, so prove the copy is unmodified.
  2. Read the linked tickets out of the worksheet with `openpyxl` via
     `cell.hyperlink.target`, **not** a JQL keyword search. Cols F/I/L hold the evidence-request,
     initial-review and remediation ticket links. This is how you get the real population.
  3. Pull each ticket's full description + every comment; flatten ADF → text. No summarizing.
  4. Build the coverage summary: systems tracked, evidence collected, owner attested, exceptions.
  5. Build the remediation inventory — one row per access change, with the
     identify → owner approve → execute → confirm chain and its Jira anchors.
  6. Reconcile: remediation row count must tie to what the tickets say was executed.
- **Output directory:** `evidence/access_reviews/<cycle>/`
- **Output files:** the worksheet (original filename), `*_access_review_summary.md`,
  `*_access_review_remediation.md`, `*_access_review_ticket_exports.md`,
  `*_access_review_tickets.csv`, `it_access_review_tickets.csv`, `*_access_review_ipe.txt`
- **Scripts:** `analysis_sept14/build_q1q2_package.py`, `pull_q1q2_review_tickets.py`,
  `build_access_review_ticket_index.py`, `rebuild_ticket_exports.py`
- **IPE requirements:** which sample quarter the package covers and *why* (the naming convention);
  worksheet SHA-256; how the ticket population was derived (hyperlinks, not keyword search);
  remediation row-count reconciliation; every exception listed
- **Lessons learned:**
  - ⚠️ **Never build the ticket population from `summary ~ "access review"`.** The 9/11 version did,
    got 17 rows, and was wrong four ways: it mislabeled the three Q1 2026 tickets as Q4 2025
    "continuations," which left **the Q2 2026 sample quarter with no identified evidence at all** —
    the single most consequential error of the engagement. It also mislabeled the Q3 2025 cycle as
    Q3 2026, pulled in two provisioning requests that merely contained the word "review," and
    misgrouped IT-20632's remediation under the wrong cycle. Derive the population from the
    worksheet's own hyperlinks.
  - ⚠️ **`jira.search()` silently truncates at `maxResults`.** `project = ESEC ORDER BY key ASC`
    returned ESEC-1..100 and made a duplicate-attachment scan report *zero* duplicates. Use
    `jira.search_all()` (cursor pagination via `nextPageToken`/`isLast`) for anything where
    completeness matters — which for evidence work is everything. 100 → 277 issues.
  - **The worksheet is organized by system-of-access, not by the audit's application scope.** Four
    in-scope apps appear by name (SchoolHub/SPOKE, CASHI, MMAX, files.com); Servicing maps to the
    `Admin Internal` row; **SLO has no row of its own** — precisely the system with two 2025
    sub-exceptions. Add an explicit row per in-scope audit application to the template.
  - Reconcile the worksheet against authoritative sources yourself rather than relying only on
    owner attestation — this is what Security's verification role produces. Doing so surfaced 4
    Okta accounts (vs. the Navient Workday active-employee export) and 5 Admin Internal accounts
    (vs. Google Workspace last-sign-in) that the owners' reviews had not caught.
  - Check every attested row actually has a review ticket link. Plaid was 1 of 46 with an empty
    `Initial Review Ticket` cell — attested by worksheet record alone.
  - Watch for stale template rows. Splunk was still listed as in-scope well after the January 2026
    migration to CrowdStrike.
  - **The "Ready for Exec Review?" / "Exec Reviewer" / "Sign Off" columns are vestigial and
    intentionally unused.** Executive sign-off was deliberately discontinued — wasted resources
    for no practical assurance, since the signing executive had no knowledge of whether a given
    user's access was appropriate. **System owners own the review; Security orchestrates and
    verifies.** Never characterize the blank columns as a control gap or a missed step; explain
    the accountability model and recommend removing the columns from the template.
  - Cross-check a cycle ticket's *name* against its created date before trusting it. IT-21950 was
    titled "Q2 2026 Access Review" but was created 2026-09-11 alongside every other Q3 2026 cycle
    ticket — a misnamed Q3 review; renamed with an explanatory comment.

### ESEC-182/184: Req 73b & 75b — Remediation Samples
- **Status:** 🔄 To Do — reopened 2026-09-14, awaiting auditor sample selection
- **Why reopened:** both had been closed while the samples they ask for hadn't been selected yet.
  A request that is contingent on auditor sample selection stays open until the samples arrive —
  closing it makes the tracker read as complete when it isn't.
- **Staged evidence:** `2026_Q1_access_review_remediation.md` — 30 access changes across 6 systems
  (Env0 12, Admin Internal 5, Okta 4, Amplitude/Segment 3, Docker Hub 3, Zendesk 3 admin→agent
  downgrades), all completed, each with its Jira chain. Per-sample before/after evidence gets
  produced against these entries once BT selects.

---

## VPN & MFA (ESEC-178/179)

### ESEC-179: Req 72 — VPN & MFA Evidence
- **Evidence type:** Config/Screenshot
- **Status:** ✅ Done
- **Source systems:** Okta API + Pritunl VPN
- **Collection steps:**
  1. Okta API pulls (requires SSWS token):
     - `GET /api/v1/policies?type=OKTA_SIGN_ON` → sign-on policies
     - `GET /api/v1/policies?type=MFA_ENROLL` → MFA enrollment policies
     - `GET /api/v1/org/factors` → configured authenticators
  2. Manual screenshots:
     - VPN MFA prompt (Pritunl → Okta challenge)
     - Okta MFA enrollment settings
  3. Combine into `vpn_mfa_combined/` directory
- **Output directory:** `evidence/vpn_mfa_combined/`
- **Output files:** `okta_mfa_policies.csv`, `okta_signon_policies.csv`, `okta_authenticators.csv`, `vpn_restricted_security_groups.csv`, `IPE_documentation.txt`, screenshots
- **Lessons learned:**
  - macOS `cp` fails with special characters in screenshot filenames — use Python `shutil.copy2(glob.glob(...)[0], dest)`
  - Okta API token provided at session start by user, never stored to disk
  - VPN SGs already demonstrated in network security evidence — linked rather than duplicated

---

## Full-Device Encryption (ESEC-227)

### ESEC-228–231: CO.08 — Iru MDM / FileVault
- **Evidence type:** Population / Config / Screenshot
- **Status:** ✅ Done
- **Source systems:** Iru MDM (managed.iru.online)
- **Collection steps:**
  1. Export device population from Iru admin console → `All Devices - 2026-09-04.csv` (354 devices)
  2. Screenshot FileVault enforcement settings in Kandji profiles
  3. Screenshot device export process for IPE
- **Output directory:** `~/Downloads/Iru/`
- **Key findings:**
  - 354 total devices; 41 stale (>30 days since last check-in) — likely former employees or storage
  - FileVault enforced via Kandji MDM profiles across all managed Macs
- **Lessons learned:**
  - No Iru API available — evidence is manual exports and screenshots
  - Always note stale devices in comments to preempt auditor questions

#### Per-blueprint coverage (added 2026-09-14)

Req 136 originally held one end-user FileVault screenshot. For an MDM-enforced control that is thin:
it evidences one device out of 354. The pattern that closes it properly, and generalises to any
MDM/GPO/profile-enforced control:

1. **Pivot the population on the enforcement grouping.** `Blueprint Name` in the Req 134 export
   resolves to 6 blueprints across 354 devices. The blueprint is the unit the profile attaches to,
   so it is the unit the evidence should be organised by.
2. **Screenshot the library item's own Assignment Maps list.** This is the primary artifact — one
   screenshot naming every blueprint the profile is assigned to. Because assignment is what causes
   the profile to apply, a blueprint appearing in that list evidences enforcement on every device
   in it. This is what makes 354-device coverage provable without 354 screenshots.
3. **Confirm from the blueprint side where you can**, and open the status side panel. The best
   artifact in the CO.08 set shows `31 Success / 0 Error / 0 Other` against 31 devices — that is
   successful *application*, not just assignment, and it is the difference between "we configured
   it" and "it is on." Capture that panel by default.
4. **Reconcile blueprint headers against the population.** Iru headers count all enrolled devices;
   the population is filtered to MacBooks. One blueprint read 302 vs 289 — 13 non-Mac devices.
   Say so in the evidence, because an auditor comparing the two numbers will otherwise file it.

#### Do not scope devices out on the strength of a blueprint name

Three blueprints held 5 devices and lacked a blueprint-side screenshot. The tempting close was
"test/non-prod, out of scope" — one of them is literally named `Harry's Test blueprint - Tahoe`.

Checking the population killed that argument: all 5 are MacBook Pros assigned to named individuals,
all checked in on the export date, and one belongs to a member of Earnest IT. They are production
laptops in a blueprint someone named "test." Asserting otherwise would have handed Baker Tilly a
sample that disproves the claim, and the collateral damage is worse than the finding — a scoping
argument caught being wrong discredits every *other* scoping argument in the submission.

**The rule: a blueprint/group/OU name is an administrative label, not a scoping statement.** Before
excluding anything on the basis of what a container is called, pull the members and look at them.
And check whether you need the exclusion at all — here FileVault *was* enforced on all 5 via the
Assignment Maps list, so the honest close was stronger than the scoping argument would have been.
Disclose the difference in evidence form ("evidenced from the profile side only, screenshots
available on request") and let the control pass on its merits.

#### A filtered population needs the filter in the IPE (fixed 2026-09-14)

The Iru IPE on ESEC-229 said both `Filters applied: Model Name contains "MacBook"` and
`Completeness: ... no pagination or filtering applied`. Two adjacent lines contradicting each other,
in the one artifact type an auditor tests hardest. The second was boilerplate carried over from an
unfiltered export.

A filter *was* applied and it is the right filter — CO.08 is about laptops, so the population is the
Mac fleet, not every enrolled device. The fix was to state that affirmatively: the filter, the row
count, the six blueprints and their counts, confirmation the CSV export is not paginated, and the
reconciliation explaining why a blueprint header reads 302 against 289 MacBooks (13 non-Mac devices
in that blueprint). Re-uploaded to ESEC-229 (att 231741, superseding 231069).

**The rule: "no filtering applied" is a claim, not boilerplate — delete it unless it's true.** A
scoped population is fine and often correct; an IPE that misdescribes its own scope is not, because
it invites the auditor to distrust every other IPE in the submission. If a filter exists, name it and
justify it against the control's wording, and reconcile any count the auditor can see in the console
against the count in the file.

---

## Evidence Hygiene and Self-Correction

Procedures for the work that happens *after* evidence is submitted. Everything here came out of the
2026-09-14 review pass, which found five defects in already-submitted evidence.

### Auditing your own submitted evidence
- **Run a completeness scan across the whole ESEC project, not a sample.** Use
  `jira.search_all("project = ESEC ORDER BY key ASC", fields="summary,status,attachment")`.
  With the truncating `search()` this returned 100 of 277 issues and reported zero duplicates.
- **Find duplicate attachments by byte size**, grouped per ticket. Identical size on the same
  ticket is a near-certain duplicate; confirm with SHA-256 if the file matters.
- **Dedupe rule:** delete a duplicate only when the identical file is on the **same** ticket. If
  the same file legitimately sits on **multiple** tickets — because it's responsive to more than
  one request — **leave every copy.** Note that intent in a comment so it doesn't read as sloppiness.
  Keep the normalized snake_case copy, drop the original upload.
- **Guard every deletion.** Before deleting, re-pull the ticket live and confirm the keeper still
  exists at an identical byte size; skip the delete otherwise. See
  `analysis_sept14/dedupe_and_move.py` — pre-flight, execute, verify, in that order.
- **Comment on every change.** Any attachment removed or moved gets a dated provenance comment
  saying what was removed, its byte size, and where the surviving copy is. An attachment that
  vanishes from an audit ticket with no explanation is worse than the duplicate was.

### When submitted evidence turns out to be wrong
- **Disclose it, don't quietly amend it.** Add a dated revision block to
  `evidence_request_justification.md` listing each correction, and a dated correction section to
  the affected IPE. Self-identified and disclosed reads as a working control environment;
  discovered by the auditor after a silent edit does not.
- **Show the delta.** Old value → new value, row counts included, plus a sidecar file itemizing
  any rows removed.
- **Reopen tickets that were closed prematurely.** ESEC-182/184 were closed while still waiting on
  auditor sample selection. Requests contingent on someone else's input stay open.
- **Never leave a false statement standing in the audit record.** When correcting a prior comment,
  post the correction even if it's awkward — but keep it factual and scoped to what was wrong.

### Writing auditor-facing documents
- **No internal negotiating strategy in anything the auditor sees.** The justification doc had a
  "Pushback on this request" section arguing a request was "analogous to asking for proof that AWS
  didn't disable encryption at rest on S3." Keep the substantive technical argument, drop the
  framing — state what the evidence is, why it meets the control intent, and offer to discuss.
- **Explain a deliberate process decision as a decision, not a gap.** Discontinued controls and
  vestigial template fields need an affirmative explanation of the current accountability model.
- **Don't claim coverage you haven't traced.** Map each in-scope audit application to the specific
  artifact that covers it, and say so explicitly when the mapping is inferred rather than named.
- **Verify every vendor name against a query the auditor could run.** WHOIS, a DNS record, a console
  screenshot. Not inference from an adjacent record in the same zone. See LS.13 below.
- **Scope an unobtainability argument to the exact system whose data is gone.** "Cannot be produced"
  is a claim about a named system's retention, not about the control. Write "no Google Workspace
  customer can produce X," not "X cannot be produced" — the second version is falsified the moment
  anyone finds a second data source, and it makes every other statement in the document suspect.

### Delivering documents — format (added 2026-09-14)

Write in Markdown, ship PDF. Drive has no Markdown renderer: a `.md` previews as raw text, so every
table is pipe soup before the auditor downloads anything, and a Windows workpaper machine opens it in
Notepad. The `.md` stays the source of truth in the repo and on the Jira ticket; only what the
auditor receives changes.

`analysis_sept14/md_to_pdf.py` does the conversion. What it took to get right:

- **Renderer:** WeasyPrint, not headless Chrome. Chrome's default `--print-to-pdf` footer stamps the
  local `file:///Users/...` path into every page — path leakage on an auditor deliverable. WeasyPrint
  needs `brew install pango` and `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.
- **Page furniture:** `@page` with a running header (org name, doc title via `string-set`) and footer
  (audit period, `counter(page)` of `counter(pages)`). Page numbers exist so a workpaper can cite a
  location that still resolves next year. `thead { display: table-header-group }` repeats header rows
  across page breaks.
- **Tables need an explicit `<colgroup>`.** WeasyPrint's automatic layout allocates on *max-content*
  width, so one cell holding a 74-character filename claims most of the table and squeezes short
  columns into three-line stacks. `overflow-wrap` alone cannot rebalance it. Compute per-column
  widths from the content and pair the emitted `<colgroup>` with `table-layout: fixed`. Use
  `overflow-wrap: anywhere` on `td` but `normal` on `th`, or "Devices" renders as "Devic es".
- **Python-Markdown is not GitHub-flavoured.** It needs a blank line before a list or table, or the
  items get swallowed into the preceding paragraph and bullets come out as running prose. Normalise
  on the way in (fence-aware) rather than rewriting the source docs.
- **`Label: value` metadata runs need hard breaks**, or "Prepared by: Adam Duman" and "Last updated:
  …" merge into one line. Gate the rule on the *next* line also being a label, so a prose paragraph
  that merely opens with a bold label is left alone.
- **macOS is case-insensitive.** `keystone_swarm_channel_export.md` collided with the native Slack
  export `Keystone_Swarm_Channel_Export.pdf`. Both are real evidence — the PDF is the raw export, the
  `.md` a curated transcript with its own IPE — so rename rather than clobber. The renderer refuses
  to overwrite an existing PDF.

Traceability: the manifest and `EVIDENCE_INDEX.xlsx` carry `source_markdown` + `source_sha256` next
to each PDF's own hash. A PDF is a *rendering* of evidence, not new evidence, and the chain
Drive PDF → source `.md` → Jira attachment has to stay checkable in both directions. Note PDFs are
not byte-reproducible across runs (embedded creation timestamp), so the manifest hash is of the copy
that actually ships.

`.txt` is left alone — IPE notes, `_PENDING`, `CLOSURE_RATIONALE` are short and have no tables.
`INDEX.md` was retired for `EVIDENCE_INDEX.xlsx` (3 sheets: files / per-control totals / requests
without files). The README offers any document in Word format on request.

---

## Email Security — LS.13 (ESEC-196/197/198/199)

### Earnest's inbound mail path has TWO scanning layers
Read this before writing anything about LS.13.

1. **Cloudflare Area 1 Security** — the inbound gateway. MX records are
   `mailstream-east.mxrecord.io` and `mailstream-west.mxrecord.io`. First-line scanning for
   phishing, malware, BEC and malicious links, applied *before* Google sees the mail.
2. **Google Workspace (Gmail)** — mailbox provider, its own platform scanning plus the
   customer-configurable Gmail Safety settings.

**Valimail (`vali.email`) is NOT the gateway.** It appears in the SPF macro-include and the DMARC
`rua` destination — outbound authentication and DMARC report processing. It appears in no MX record.
The 9/8/2026 DNS evidence labeled it the gateway and was wrong for the entire year until corrected
on 9/14. Verify with:
```
whois mxrecord.io          # Registrant Organization: Area 1 Security; Registrar: Cloudflare, Inc
dig +short A mailstream-east.mxrecord.io   # 172.65.213.128
whois 172.65.213.128       # NetName: CLOUDFLARENET
```
**Any LS.13 evidence set must cover both layers.** Req 96/97/98 as filed in 2026 covered Google only.

**Procurement note:** active evaluation of **Material Security** and **Abnormal Security** to replace
Gmail + Area 1 as of 9/2026. Not complete, not in production, does not affect the 10/1/2025–9/30/2026
period. When it lands, document the migration at the time and carry retention requirements into
selection.

### Google Workspace log retention — the hard constraint
Source: `https://knowledge.workspace.google.com/admin/reports/data-retention-and-lag-times`

| Item | Retention |
|---|---|
| Gmail log events | 6 months |
| Email log search | 30 days |
| Admin log events | 6 months |
| Security reports | 6 months |
| Audit data via API | 6 months |
| Vault log events | Indefinite |

The page states verbatim: *"Administrators cannot delete log event data or change the length of time
that the data is available for."* Quote it with the URL and the page's last-updated date — it turns
"we didn't keep it" into "no customer of this platform can keep it."

- **Retention is rolling, measured backward from today.** Six months before 9/14/2026 ≈ 3/14/2026.
  Oct 2025 aged out ~Apr 2026; Dec 2025 aged out ~Jun 2026. Both were gone before the request arrived.
- **The current data ages out too.** June 2026 goes dark around Dec 2026. Say so in the document.
- **Config-continuity is not a workaround.** Admin log events are *also* 6 months, so
  "current config + audit trail showing no change" only reaches ~Mar 2026 forward. Mention this
  pre-emptively or it looks like an untried option.
- **Vault is the exception** — indefinite retention. Check what's in Vault before conceding a month.
- **Area 1 retains independently of Google.** Check it before writing any month off.

### Producing point-in-time Gmail config
There is no historical-config API for anyone. The constructible equivalent:
- **Current state:** Cloud Identity Policy API — `cloudidentity.googleapis.com/v1/policies`
  (scope `cloud-identity.policies.readonly`), returns the live Gmail Safety settings machine-readably.
- **Absence of change:** Admin SDK Reports API `applicationName=admin`
  (scope `admin.reports.audit.readonly`), showing no config-change events in the window — bounded by
  the same 6-month retention.
Both need domain-wide delegation, the same blocker as ESEC-167.

### Remediation carried forward
1. Gmail log export to BigQuery — retention under Earnest's control, not Google's.
2. Monthly snapshot of the Gmail security summary into the evidence repo.
3. Monthly snapshot of Gmail Safety config via Cloud Identity Policy API.
4. Compile the Area 1 evidence set — config, policy, admin listing, detection output.
5. Audit every in-scope system for sub-365-day retention. The 6-month default also hits Drive,
   Admin, Login, Chat and Calendar log events, not just Gmail.

---

## Backlog Snapshot (pre-collection, historical)

The lists below were the starting backlog and are **not** a current status view — most of these are
now closed. For live status, pull ESEC with `jira.search_all()` and check the Open Items Summary in
`evidence_request_justification.md`.

### Password & Authentication (ESEC-164)
- **ESEC-166:** Okta password settings → needs OKTA_DOMAIN + OKTA_API_TOKEN
- **ESEC-167:** G-Suite password settings → needs Google Admin SDK delegation
- **ESEC-168:** Files.com password settings → needs FILES_COM_API_KEY
- **ESEC-169:** ITO password settings → manual screenshot

### Access Management (ESEC-170)
- **ESEC-171:** New/modified SLO access population → Jira query for access request tickets
- **ESEC-172, 173, 174:** Access approval samples → depends on auditor selection

### Admin Listings (ESEC-204)
- **ESEC-205:** Admin listings → Okta admin users API
- **ESEC-206:** IPE for admin listings

### Files.com Accounts (ESEC-200)
- **ESEC-201:** New Files.com accounts population → Files.com API
- **ESEC-202:** IPE for Files.com accounts

### Email Security (ESEC-196)
- **ESEC-197, 198, 199:** Email security reports and config → manual or vendor API

### Asset Disposal (ESEC-207)
- **ESEC-208, 209, 210:** Asset disposal records → manual/IT process

### Stakeholder-Dependent
- **ESEC-163:** Security update PowerPoints → manual collection (sample months: Oct 2025, Dec 2025, Jun 2026)
- **ESEC-190:** Splunk/New Relic auto-update settings → Jason Kennedy screenshot
- **ESEC-217:** Splunk log edit permissions → Jason Kennedy screenshot
- **ESEC-218/219/220:** Splunk user listing + IPE → Jason Kennedy
- **ESEC-221/222:** UniFi network security settings → Tyler Yates / Gaige
- **ESEC-238:** IT Ops org chart → HR/leadership
- **ESEC-240:** Background check samples → HR
- **ESEC-241/242:** Independent contractor population + IPE → HR
- **ESEC-244:** Performance reviews → HR
- **ESEC-250:** Downtime/patching alerts → PagerDuty/status page team

### Auditor-Selection (Req 2 deadline: 9/30)
- **ESEC-149:** Change ticket samples → auditor selects from population
- **ESEC-172/173/174:** Access approval samples → auditor selects
- **ESEC-177:** Termination access removal samples → auditor selects
- **ESEC-182/184:** Access review remediation samples → auditor selects
- **ESEC-203:** Files.com account creation ticket samples → auditor selects
- **ESEC-236:** Incident response samples → user building manually
- **ESEC-266:** Backup config/summary log samples → auditor selects

### Known Gaps / Planned
- **ESEC-257/258:** Tabletop exercise → planned for before month end
- **ESEC-260:** Penetration test report → running but not remediated before month end
- **ESEC-261:** BC/DR → possible to use existing BC/DR simulation
- **ESEC-245:** Finwise MSA/OAB contract → contract document

---

## API Reference

### Jira Cloud
- **Base URL:** `https://meetearnest.atlassian.net`
- **Auth:** Basic Auth (email + API token from 1Password)
- **Search:** `GET /rest/api/3/search/jql?jql=...` (NOT the old `/search` — returns 410)
- **Pagination:** Cursor-based (`nextPageToken`/`isLast`), NOT offset-based
- ⚠️ **A single search call silently truncates at `maxResults` — no error, no flag.** It just
  returns fewer issues than match. Always use the paging wrapper (`jira.search_all()`) for
  anything where completeness matters. This produced a false "zero duplicates found" result on
  9/14 by returning ESEC-1..100 when the audit tickets live at ESEC-139..280.
- **Rename an issue:** `PUT /rest/api/3/issue/{key}` with `{"fields": {"summary": "..."}}`
- **Attachment delete:** `DELETE /rest/api/3/attachment/{id}` — returns empty body, so read it raw
- ⚠️ **Attachment ids come back as strings, not ints.** `if OLD_ID in {a[0] for a in attachments}`
  is silently False when `OLD_ID` is written as a bare int literal, so the upload-then-delete guard
  fails open: the replacement uploads, the superseded copy is never removed, and the ticket ends up
  with two versions of the same file. Coerce both sides with `str()`. Caught on ESEC-229 9/14.
- ⚠️ Comment bodies are **ADF** — a plain string is rejected. Reading requires flattening ADF back
  to text (`content[].content[].text`).
- **Rate limit:** ~100 req/60s, scripts use 90 req/60s window
- **Attachments:** `POST /rest/api/3/issue/{key}/attachments` with `X-Atlassian-Token: no-check` and `Content-Type: None` override
- **Comments:** `POST /rest/api/3/issue/{key}/comment` with ADF body
- **Transitions:** `POST /rest/api/3/issue/{key}/transitions` with `{"transition":{"id":"31"}}` (31=In Progress, 41=Done)

### Confluence Cloud
- **Base URL:** `https://meetearnest.atlassian.net/wiki`
- **Auth:** Same as Jira (Atlassian Cloud shared auth)
- **Search:** `GET /rest/api/content/search?cql=...`
- **Page metadata:** `GET /rest/api/content/{id}?expand=version,history,space,ancestors`
- **Children:** `GET /rest/api/content/{id}/child/page`

### GitHub
- **Org:** `meetearnest`
- **Auth:** `gh` CLI authenticated as DuuMayne (has `repo` + `read:org`)
- **Members:** `gh api /orgs/meetearnest/members --paginate`
- **Teams:** `gh api /orgs/meetearnest/teams --paginate`
- **Branch protection:** `gh api /repos/meetearnest/{repo}/branches/main` → check `protected` field
- **PR search:** `gh pr list --repo meetearnest/{repo} --search "QUERY" --state merged --json number,title,author,mergedAt`

### AWS
- **Auth:** AWS SSO via IAM Identity Center (d-90676c4cd0.awsapps.com/start)
- **Profiles:** `production` (075440130607), `security-dev` (747722821363)
- **CRITICAL:** Always use `AWS_PROFILE=production` for evidence. Verify with `aws sts get-caller-identity`.
- **Regions:** `us-east-1` (primary), `us-west-2` (secondary), CloudFront is global
- **Session duration:** ~24 hours — must re-auth each day
- **Organization:** 22 accounts (Production, Development, Staging, Sandbox, Alpha, Logging, etc.)
- **Key services and commands:**
  - Organizations: `aws organizations list-accounts`
  - EC2: `describe-vpcs`, `describe-security-groups`, `describe-network-acls`, `describe-subnets`
  - EKS: `list-clusters`, `describe-cluster`, `list-updates`, `describe-update`
  - RDS: `describe-db-instances`, `describe-events`, `describe-event-subscriptions`
  - ACM: `list-certificates`, `describe-certificate`
  - ELBv2: `describe-load-balancers`, `describe-listeners`
  - CloudFront: `list-distributions` (returns empty if none exist — not an error)
  - EventBridge: `list-rules`, `list-targets-by-rule`
  - Backup: `list-backup-plans`, `list-backup-vaults`, `get-backup-vault-notifications`

---

## IPE Checklist

Every evidence collection must include:

1. **Source system identification** — system name, instance URL, authentication method, account identity
2. **Query parameters** — exact API call, JQL query, CLI command with all flags
3. **Row counts** — total records returned per query
4. **Pagination completeness** — assert all pages fetched (nextToken/Marker exhausted)
5. **Timestamp** — UTC time of collection
6. **Data path** — API → transport → format → output file
7. **Accuracy controls** — auth method, TLS, no filtering/modification
8. **Reproducibility** — any user with equivalent access can re-run and get same results
9. **Limitations** — document any access restrictions, missing data, or assumptions
