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

### ESEC-142: Req 27 — SLO Platform Change Population
- **Evidence type:** Population
- **Status:** ⬜ To Do (evidence collected but upload reversed pending repo mapping)
- **Source systems:** Jira Cloud API
- **Automation:** `collectors/jira_collector.py` → `collect_change_populations()`
- **Collection steps:**
  1. Query Jira: `GET /rest/api/3/search/jql` with JQL: `project = SLO2 AND status = Done AND resolved >= "2025-10-01" AND resolved <= "2026-09-30" ORDER BY resolved DESC`
  2. Paginate using `nextPageToken` (cursor-based, NOT startAt)
  3. Export fields: key, summary, status, priority, assignee, reporter, created, resolved, labels, components
  4. Write to `change_population_SLO2.csv`
- **Output files:** `change_population_SLO2.csv`
- **IPE requirements:** Query parameters, row count, timestamp, pagination completeness assertion
- **Lessons learned:**
  - SLO project key is `SLO2`, not `SLO` (which doesn't exist)
  - Must use cursor-based pagination — `startAt` silently caps at first page
  - Change population upload reversed pending confirmed repo→system mapping

### ESEC-143: Req 27 — SchoolHub Change Population
- **Evidence type:** Population
- **Status:** ⬜ To Do (same as ESEC-142)
- **Source systems:** Jira Cloud API
- **Automation:** Same as ESEC-142
- **Collection steps:** Same as ESEC-142 but with `project = ENG`
- **Lessons learned:** SchoolHub is tracked in `ENG` project (Going Merry Engineering), not a `SHUB` project

### ESEC-144: Req 27 — CASHI Change Population
- **Source systems:** Jira Cloud API
- **Collection steps:** Same as ESEC-142 but with `project = NEW` (New Products)

### ESEC-145: Req 27 — MMAX Change Population
- **Source systems:** Jira Cloud API
- **Collection steps:** Same as ESEC-142 but with `project = PL` (Personal Loans)

### ESEC-146: Req 27 — Files.com Change Population
- **Source systems:** Jira Cloud API
- **Collection steps:** Same as ESEC-142 but with `project = INF` (Infrastructure)

### ESEC-147: Req 27 — Servicing Platform Change Population
- **Source systems:** Jira Cloud API
- **Collection steps:** Same as ESEC-142 but with `project IN (SIT, NS)`

### ESEC-148: Req 28 — IPE for All Change Populations
- **Evidence type:** IPE
- **Status:** ⬜ To Do
- **Source systems:** Generated from collection metadata
- **Collection steps:**
  1. Aggregate query parameters, row counts, timestamps from all population collections
  2. Assert pagination completeness (all `nextPageToken`s exhausted, `isLast: true`)
  3. Document data path: Jira REST API → HTTPS → JSON → CSV
  4. Include authentication method and Jira account identity
- **Output files:** `IPE_documentation.txt`, `IPE_documentation.json`

### ESEC-149: Req 29 — Change Ticket Samples
- **Evidence type:** Sample
- **Status:** ⬜ To Do (depends on auditor sample selection)
- **Source systems:** Jira Cloud API + GitHub API
- **Collection steps:**
  1. Auditor selects N tickets from population
  2. For each ticket: pull full Jira issue with all fields, comments, attachments
  3. Cross-reference with GitHub PR: search `gh pr list --search "TICKET-KEY" --repo meetearnest/<repo>`
  4. Pull PR details: approval reviews, merge commit, branch protection status
  5. Build correlation: Jira ticket → GitHub PR → approval → merge
- **Lessons learned:** Use `gh` CLI (authenticated as DuuMayne) instead of PAT for GitHub — PAT rate limits at 5000/hr

---

## Environment Segregation (ESEC-150)

### ESEC-151 through ESEC-156: Req 35 — Environment Segregation (per system)
- **Evidence type:** Screenshot/Config
- **Status:** 🔄 In Progress (evidence collected and uploaded)
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
- **Status:** 🔄 In Progress
- **Source systems:** AWS EC2 API
- **Collection steps:**
  1. `aws ec2 describe-security-groups --region <region> --profile production`
  2. Parse all inbound/outbound rules
  3. Export to `security_group_rules.csv` (1,327 rules)
- **Automation:** `collectors/aws_collector.py` → `collect_security_groups()`

---

## Security Incidents (ESEC-232)

### ESEC-233: Req 138 — Security Incidents Population
- **Evidence type:** Population
- **Status:** 🔄 In Progress
- **Source systems:** Jira Cloud API
- **Automation:** `collectors/jira_collector.py` → `collect_security_incidents()`
- **Collection steps:**
  1. Query three Jira projects for incidents in audit period:
     - `project = ESEC AND issuetype IN (Alert, Incident)` → ESEC alerts/incidents
     - `project = INC` → operational incidents
     - `project = SEC AND issuetype = Bug` → security bugs
  2. Merge and deduplicate across projects
  3. Export: `security_incidents_ALL.csv` (178 total), per-project CSVs
- **Output files:** `security_incidents_ALL.csv`, `security_incidents_ESEC.csv`, `security_incidents_INC.csv`, `security_incidents_SEC.csv`

### ESEC-234: Req 139 — IPE for Security Incidents
- **Status:** 🔄 In Progress
- **Output files:** `IPE_documentation.txt`

### ESEC-235: Req 140 — No Incidents Confirmation
- **Status:** 🔄 In Progress (incidents DO exist — CSV shows 178 items)

---

## Backups (ESEC-263 / ESEC-266)

### ESEC-264: Req 212 — Server Backup Listings
- **Evidence type:** Population
- **Status:** ✅ Done
- **Source systems:** AWS RDS API
- **Automation:** `collectors/aws_collector.py` → `collect_backup_configs()`
- **Collection steps:**
  1. `aws rds describe-db-instances --region us-east-1 --profile production` → 25 instances
  2. Extract backup config: `BackupRetentionPeriod`, `PreferredBackupWindow`, `LatestRestorableTime`
  3. `aws rds describe-db-snapshots --snapshot-type automated --region us-east-1` → 230 snapshots
- **Output files:** `rds_backup_configs.csv`, `rds_automated_snapshots.csv`

### ESEC-267: Req 214 — Backup Failures List
- **Evidence type:** Population
- **Status:** 🔄 In Progress
- **Source systems:** AWS RDS API
- **Automation:** `collectors/aws_collector.py` → `collect_backup_failures()`
- **Collection steps:**
  1. `aws rds describe-events --source-type db-instance --event-categories backup --duration 20160` (14 days)
  2. Filter for failure events → none found
  3. Write `no_backup_failures.txt` confirmation + `backup_events.csv` (236 events, all success)
- **Output directory:** `evidence/aws/backup_events_fix/`

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

## Tickets Not Yet Addressed

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

### Other
- **ESEC-140:** SDLC & Change Management policy → policy document
- **ESEC-163:** Security update PowerPoints → manual collection
- **ESEC-165:** Network authentication policy → policy document
- **ESEC-175:** Access management policy → policy document
- **ESEC-194:** Network traffic settings policy → policy document
- **ESEC-195:** Security group VPN-only access → AWS VPC/SG screenshot
- **ESEC-236:** Incident response samples → depends on auditor selection
- **ESEC-244:** Performance reviews → HR process
- **ESEC-246:** Finwise MSA/OAB → contract document
- **ESEC-265:** Backup config & summary logs samples → depends on auditor selection
- **ESEC-268:** Backup failure ticket samples → depends on auditor selection

---

## API Reference

### Jira Cloud
- **Base URL:** `https://meetearnest.atlassian.net`
- **Auth:** Basic Auth (email + API token from 1Password)
- **Search:** `GET /rest/api/3/search/jql?jql=...` (NOT the old `/search` — returns 410)
- **Pagination:** Cursor-based (`nextPageToken`/`isLast`), NOT offset-based
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
- **Regions:** `us-east-1` (primary), `us-west-2` (secondary)
- **Session duration:** ~24 hours — must re-auth each day
- **Key services:** Organizations, EC2 (VPCs, SGs, subnets), EKS, RDS

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
