# SOC 2 Evidence Collection Workflow

How we ran the 2026 SOC 2 Type II evidence collection at Earnest, what worked, what didn't, and how to replicate it.

## Architecture

```
Auditor Request List (.xlsx)
    ↓ parsed into
Jira ESEC tickets (94 tickets across ~35 controls)
    ↓ evidence collected via
Source Systems: AWS, GitHub, Okta, Confluence, Iru MDM, Jira, Google Workspace
    ↓ stored in
Local evidence directories → uploaded to Jira tickets → shared via Google Drive
```

### Key directories
- `~/Downloads/2026 SOC II/evidence/` — all collected evidence, organized by source
- `/tmp/soc2-evidence-planner/` — scripts, runbook, this doc
- Evidence shared with auditors via Google Drive (not all evidence needs to be in Jira)

### Key tools
- **Jira Cloud API v3** — ticket management, evidence upload, status tracking
- **GitHub CLI (`gh`)** — PR populations, branch protection, code review data
- **AWS CLI** — infrastructure evidence (VPCs, SGs, NACLs, ACM, ELB, RDS, Backup, EventBridge)
- **Okta API** — MFA/SSO policies, authenticators
- **Confluence REST API** — policy documentation sweep
- **Python scripts** — `scripts/jira_client.py` (rate-limited Jira client), `scripts/adf.py` (ADF comment builder)

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
4. **Okta configs** — MFA, SSO, authenticators
5. **Device management (Iru)** — manual export + screenshots

### Phase 3: Stakeholder Chase (Weeks 2-3)
For evidence that requires other teams:
1. Create Jira tickets with clear ADF comments explaining what's needed
2. Send Slack messages for urgency
3. Draft specific ask templates (not generic "please provide evidence")
4. Track who owes what — Jira dashboard "Open No Attachments" filter

### Phase 4: Gap Analysis & Remediation (Week 3)
1. Review all open tickets against the auditor request list
2. Identify known gaps (tabletop, pentest, BC/DR) — escalate or plan
3. Re-pull any evidence that was from the wrong source (e.g., wrong AWS account)
4. Update evidence for any infra remediations (e.g., orphaned SG cleanup)

### Phase 5: Closeout (Week 4)
1. Transition all completed tickets to Done
2. Prepare curated populations for auditor sample selection (9/30 deadline)
3. Share evidence via Google Drive
4. Update runbook for next year

---

## Hard-Won Lessons

### API Gotchas

| System | Gotcha | Fix |
|--------|--------|-----|
| Jira Cloud | `/rest/api/3/search` deprecated → returns 410 | Use `/rest/api/3/search/jql` endpoint |
| Jira Cloud | Pagination is cursor-based (`nextPageToken`/`isLast`), NOT `startAt` | Always use cursor pagination |
| Jira Cloud | Filter sharePermissions need `project.id` not `project.key` | Look up project ID first |
| Jira Cloud | Dashboard gadgets use Forge moduleKeys, not legacy `com.atlassian.jira.gadgets:*` | List available gadgets via API |
| Jira Cloud | Some users can't be assigned to project issues | Add comments naming the intended owner instead |
| GitHub | `gh search prs` rate limits at ~30 req/min | Retry with backoff; some 403s are transient |
| GitHub | Branch protection API returns 404 for non-admins | Use PR review data as proxy evidence |
| GitHub | `mergedAt` not in search JSON fields | Use `updatedAt` or PR detail API |
| AWS | CloudFront `list-distributions` returns empty string, not `{"DistributionList": {"Items": []}}` | Check for empty stdout before JSON parse |
| AWS | Security-dev account has different resources than production | Always verify account with `sts get-caller-identity` |
| Okta | API token is session-provided, never stored | User provides at session start |
| macOS | `cp` fails with special characters in filenames | Use Python `shutil.copy2(glob.glob(...)[0], dest)` |

### Evidence Strategy

1. **Always use production account for AWS evidence.** We burned a day pulling backup data from security-dev (2 RDS instances) when production had 25 instances and full monitoring.

2. **Limit auditor exposure.** Use observation window filters (`--merged-at`, date ranges in JQL) to scope evidence to exactly the audit period. Don't show them more than they asked for.

3. **GitHub PRs > Jira tickets for change populations.** GitHub captured 388 SLO PRs vs. 107 Jira tickets. PRs are the actual code changes; Jira tickets are work tracking.

4. **IPE is not optional.** Every evidence file needs inline IPE: query parameters, row counts, timestamps, pagination assertions. Build it into collection scripts, not after the fact.

5. **Curate incident evidence manually.** Automated pulls captured 178 items including alerts, bugs, and operational incidents. Auditors should only see incidents with complete PIRs.

6. **Pre-scan for remediation items.** We found 8 orphaned security groups with public ingress. Flagging these to infra early gave them time to clean up before audit review.

7. **Repo-to-product mapping is essential.** Without the "Repo List with Unit Test Coverage" spreadsheet, we couldn't map GitHub repos to auditor-facing product names.

8. **Screenshots are sometimes the only option.** Iru MDM has no API, G-Suite admin settings need manual capture, Okta MFA prompts need actual login screenshots.

### Jira Workflow

- **Transition IDs:** To Do = 21, In Progress = 31, Done = 41, False Positive = 42
- **ADF comments** are critical for stakeholder communication — use `scripts/adf.py` builders
- **Attachment upload** requires `X-Atlassian-Token: no-check` header and multipart/form-data
- **Rate limit:** 100 req/60s — scripts use 90 req/60s window with sliding window tracker

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

## Reusable Scripts

### `scripts/jira_client.py`
Rate-limited Jira Cloud client with retry logic. Key methods:
- `add_attachment(issue_key, filepath)` — upload file to issue
- `add_comment(issue_key, adf_body)` — add ADF-formatted comment
- `get_issue(issue_key)` — get issue details
- `search(jql)` — paginated search using new `/search/jql` endpoint

### `scripts/adf.py`
ADF builder functions: `doc`, `heading`, `paragraph`, `text`, `bold`, `italic`, `bullet_list`, `list_item`, `panel(panel_type, *blocks)`, `rule`, `table`, `link_text`, `code_block`

Note: `panel()` takes `panel_type` as first positional arg (info/note/warning/error/success), then blocks.

### `collectors/replace_policy_evidence.py`
Delete old attachments + re-upload + add comment in one pass. Useful when policy pages are refreshed.

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
