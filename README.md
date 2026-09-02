# SOC 2 Evidence Planner

Automation toolkit for SOC 2 Type II evidence collection. Built for GRC practitioners who need to collect, organize, and submit audit evidence across Jira, GitHub, AWS, Confluence, Okta, Google Workspace, and Files.com.

This started as a personal tool for managing Earnest's 2026 SOC 2 audit and is evolving into reusable building blocks for GRC engineering automation — designed to complement platforms like Vanta, not replace them.

## What This Does

1. **Parses auditor request lists** and generates a complete Jira ticket hierarchy (epic → tasks → subtasks)
2. **Collects evidence via API** from source systems with full IPE documentation
3. **Uploads evidence to Jira** as attachments with structured ADF comments
4. **Tracks collection status** with a runbook mapping every evidence request to exact steps

## Repository Structure

```
soc2-evidence-planner/
├── scripts/                    # Core Jira automation toolkit
│   ├── jira_client.py          # Jira Cloud REST API v3 client (auth, rate-limit, pagination)
│   ├── adf.py                  # Atlassian Document Format builder helpers
│   ├── cli.py                  # CLI entry point (create, validate, filters, dashboard, migrate)
│   ├── csv_parser.py           # Auditor CSV ingestion and normalization
│   ├── templates.py            # Ticket description rendering → ADF
│   ├── tickets.py              # Ticket creation, epic linking, bulk operations
│   ├── filters.py              # Saved JQL filter creation
│   ├── dashboard.py            # Dashboard + gadget creation
│   ├── labels.py               # Label computation per ticket
│   ├── migrate.py              # Cross-project issue migration
│   ├── config.py               # YAML config loading
│   ├── models.py               # Data models
│   └── state.py                # Run-state persistence for resumability
│
├── collectors/                 # Evidence collection modules
│   ├── jira_collector.py       # Change populations, patching, security incidents, access requests
│   ├── github_collector.py     # Org members, admins, repos, PRs, outside collaborators
│   ├── aws_collector.py        # VPCs, SGs, RDS backups, network topology, EKS
│   ├── okta_collector.py       # Password/MFA policies, admin users (needs credentials)
│   ├── google_workspace_collector.py  # Admin SDK (needs delegation setup)
│   ├── files_com_collector.py  # Users, site settings (needs API key)
│   ├── cross_reference.py      # Correlates Jira tickets with GitHub PRs
│   ├── upload_evidence.py      # Uploads evidence files to Jira + ADF comments
│   ├── collect_all.py          # Master runner with ticket-to-collector mapping
│   └── base.py                 # Base collector class
│
├── config/
│   └── config.example.yaml     # Documented example config (credentials via env vars)
│
├── templates/                  # Planning templates (standalone reference)
│   ├── project-plan.md         # Phased plan structure with timeline
│   ├── ticket-structure.md     # Jira ticket hierarchy and workflow
│   ├── communication-templates.md
│   ├── evidence-requirements.md
│   └── qa-checklist.md
│
├── evidence-runbook.md         # Operational playbook — every ticket, every step, every API call
├── data/sample_requests.csv
└── examples/example-output.md
```

## Quick Start

### Prerequisites

```bash
pip install requests pyyaml
```

### Environment Variables

```bash
# Jira Cloud (required for most operations)
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your-atlassian-api-token"  # from id.atlassian.com/manage-profile/security/api-tokens

# GitHub (use gh CLI auth instead of PAT when possible)
# gh auth login

# AWS (use SSO)
# aws sso login --profile production
```

### Collect Evidence

```bash
# List what each collector covers
python3 -m collectors.collect_all --list

# Run specific collectors
python3 -m collectors.collect_all --systems jira
python3 -m collectors.collect_all --systems jira,github,aws

# Upload collected evidence to Jira tickets
python3 -m collectors.upload_evidence
python3 -m collectors.upload_evidence --dry-run      # preview without uploading
python3 -m collectors.upload_evidence --comments-only  # re-post comments without re-uploading files
```

### Create Jira Tickets from Auditor CSV

```bash
python3 -m scripts.cli validate --config config/config.yaml --csv data/requests.csv
python3 -m scripts.cli create --config config/config.yaml --csv data/requests.csv
python3 -m scripts.cli create --dry-run  # preview without creating
```

## Evidence Runbook

See [`evidence-runbook.md`](evidence-runbook.md) for the operational playbook. It documents:

- Every ESEC evidence request with exact collection steps
- API calls, CLI commands, and JQL queries used
- Source systems and authentication methods
- IPE requirements per evidence type
- Lessons learned and gotchas from the 2026 collection
- Current status of each evidence request

## Key Design Decisions

**IPE-first**: Every API-based collection generates inline IPE documentation (query parameters, row counts, pagination completeness, timestamps, data path). Auditors shouldn't have to ask "how did you get this."

**Correlation chains**: For controls that span multiple systems (e.g., patching: Jira ticket → GitHub PR → AWS update), evidence is collected from all sources and cross-referenced in a single correlation file.

**Cursor-based pagination**: Jira Cloud's new search API uses `nextPageToken`/`isLast`, not `startAt`/`total`. The old pagination silently caps results. All collectors enforce cursor-based pagination.

**ADF comments**: Evidence uploads include structured Atlassian Document Format comments on each ticket with row counts, file lists, and IPE references — so auditors can review evidence without downloading attachments.

## Reusability

This toolkit is designed as building blocks for broader GRC engineering:

- **`scripts/jira_client.py`** — Generic Jira Cloud client with rate limiting, cursor pagination, attachment upload, ADF comments. Usable for any Jira automation.
- **`scripts/adf.py`** — ADF builder that works for any Confluence/Jira content generation.
- **`collectors/base.py`** — Base collector pattern (authenticate → query → paginate → export → IPE) reusable for any evidence source.
- **IPE documentation pattern** — Consistent structure for proving data integrity across any API-sourced evidence.
- **Evidence runbook format** — Repeatable playbook structure that can be templated for future audit cycles.

## Who This Is For

- **GRC practitioners** managing SOC 2 evidence collection
- **Security engineers** building compliance automation
- **Anyone** who wants to stop taking manual screenshots and start pulling evidence programmatically

## License

MIT
