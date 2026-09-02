#!/usr/bin/env python3
"""
Upload collected evidence to ESEC Jira tickets as attachments + summary comments.
Each ticket gets its relevant evidence files attached and an ADF comment
summarizing what was collected, row counts, and IPE reference.
"""
import os
import sys
import json
import csv
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.jira_client import JiraClient
from scripts.adf import doc, heading, paragraph, text, bold, bullet_list, list_item, panel, rule

EVIDENCE_ROOT = os.path.expanduser("~/Downloads/2026 SOC II/evidence")

JIRA_DIR = os.path.join(EVIDENCE_ROOT, "jira/20260901_111308")
GITHUB_DIR = os.path.join(EVIDENCE_ROOT, "github/20260901_111837")
AWS_DIR = os.path.join(EVIDENCE_ROOT, "aws/20260901_111842")
AWS_BACKUP_DIR = os.path.join(EVIDENCE_ROOT, "aws/backup_events_fix")


def row_count(filepath):
    if not os.path.exists(filepath):
        return 0
    with open(filepath) as f:
        return sum(1 for _ in f) - 1  # subtract header


def build_comment(ticket_key, description, files_attached, stats):
    """Build an ADF comment body for a ticket."""
    content = []
    content.append(heading("Evidence Collection — Automated", 3))
    content.append(paragraph(
        text(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} by soc2-evidence-planner"),
    ))
    content.append(paragraph(bold("Description: "), text(description)))

    if stats:
        stat_items = []
        for k, v in stats.items():
            stat_items.append(list_item(paragraph(bold(f"{k}: "), text(str(v)))))
        content.append(paragraph(bold("Summary:")))
        content.append(bullet_list(*stat_items))

    if files_attached:
        file_items = []
        for f in files_attached:
            file_items.append(list_item(paragraph(text(os.path.basename(f)))))
        content.append(paragraph(bold("Files attached:")))
        content.append(bullet_list(*file_items))

    content.append(paragraph(
        bold("IPE: "),
        text("Review IPE_documentation.txt for API parameters, row counts, and timestamps.")
    ))

    return doc(*content)


TICKET_EVIDENCE_MAP = {
    # ── Change Management Populations (Jira) ────────────────────────
    "ESEC-142": {
        "desc": "SLO Platform — Change Population (Jira tickets resolved in audit period)",
        "files": [
            os.path.join(JIRA_DIR, "change_population_SLO2.csv"),
        ],
        "stats_fn": lambda files: {"Resolved tickets": row_count(files[0])},
    },
    "ESEC-143": {
        "desc": "SchoolHub — Change Population",
        "files": [
            os.path.join(JIRA_DIR, "change_population_ENG.csv"),
        ],
        "stats_fn": lambda files: {"Resolved tickets": row_count(files[0]),
                                    "Note": "SchoolHub changes tracked in ENG project (Going Merry Engineering)"},
    },
    "ESEC-144": {
        "desc": "CASHI — Change Population",
        "files": [
            os.path.join(JIRA_DIR, "change_population_NEW.csv"),
        ],
        "stats_fn": lambda files: {"Resolved tickets": row_count(files[0]),
                                    "Note": "CASHI changes tracked in NEW project (New Products)"},
    },
    "ESEC-145": {
        "desc": "MMAX — Change Population",
        "files": [
            os.path.join(JIRA_DIR, "change_population_PL.csv"),
        ],
        "stats_fn": lambda files: {"Resolved tickets": row_count(files[0]),
                                    "Note": "MMAX changes tracked in PL project (Personal Loans)"},
    },
    "ESEC-146": {
        "desc": "Files.com — Change Population",
        "files": [
            os.path.join(JIRA_DIR, "change_population_INF.csv"),
        ],
        "stats_fn": lambda files: {"Resolved tickets": row_count(files[0]),
                                    "Note": "Files.com changes tracked in INF project (Infrastructure)"},
    },
    "ESEC-147": {
        "desc": "Servicing Platform — Change Population",
        "files": [
            os.path.join(JIRA_DIR, "change_population_SIT.csv"),
            os.path.join(JIRA_DIR, "change_population_NS.csv"),
        ],
        "stats_fn": lambda files: {"SIT tickets": row_count(files[0]),
                                    "NS tickets": row_count(files[1])},
    },
    "ESEC-148": {
        "desc": "IPE — All Change Populations",
        "files": [
            os.path.join(JIRA_DIR, "change_population_ALL.csv"),
            os.path.join(JIRA_DIR, "IPE_documentation.txt"),
            os.path.join(JIRA_DIR, "IPE_documentation.json"),
        ],
        "stats_fn": lambda files: {"Total changes across all projects": row_count(files[0]),
                                    "IPE records": "See attached IPE_documentation.txt"},
    },

    # ── Patching (Jira) ─────────────────────────────────────────────
    "ESEC-162": {
        "desc": "Patching JIRA Tickets — Sample Months (Oct 2025, Dec 2025, Jun 2026)",
        "files": [
            os.path.join(JIRA_DIR, "patching_tickets_oct_2025.csv"),
            os.path.join(JIRA_DIR, "patching_tickets_dec_2025.csv"),
            os.path.join(JIRA_DIR, "patching_tickets_full_period.csv"),
        ],
        "stats_fn": lambda files: {"Oct 2025 tickets": row_count(files[0]),
                                    "Dec 2025 tickets": row_count(files[1]),
                                    "Full period tickets": row_count(files[2])},
    },

    # ── Security Incidents (Jira) ────────────────────────────────────
    "ESEC-233": {
        "desc": "Security Incidents List — Full Audit Period",
        "files": [
            os.path.join(JIRA_DIR, "security_incidents_ALL.csv"),
            os.path.join(JIRA_DIR, "security_incidents_ESEC.csv"),
            os.path.join(JIRA_DIR, "security_incidents_INC.csv"),
            os.path.join(JIRA_DIR, "security_incidents_SEC.csv"),
        ],
        "stats_fn": lambda files: {"ESEC alerts/incidents": row_count(files[1]),
                                    "INC operational incidents": row_count(files[2]),
                                    "SEC incidents": row_count(files[3]),
                                    "Total": row_count(files[0])},
    },
    "ESEC-234": {
        "desc": "IPE — Security Incidents List",
        "files": [
            os.path.join(JIRA_DIR, "IPE_documentation.txt"),
        ],
        "stats_fn": lambda files: {"IPE documentation": "Attached — covers all Jira queries with parameters, row counts, timestamps"},
    },
    "ESEC-235": {
        "desc": "No Incidents Confirmation (if applicable)",
        "files": [
            os.path.join(JIRA_DIR, "security_incidents_ALL.csv"),
        ],
        "stats_fn": lambda files: {
            "Total incidents found": row_count(files[0]),
            "Note": "Incidents exist in the audit period — review attached CSV for details"
        },
    },

    # ── GitHub: Code Developers & Entitlements ───────────────────────
    "ESEC-158": {
        "desc": "Production Change Entitlements — GitHub Org Admins",
        "files": [
            os.path.join(GITHUB_DIR, "org_admins.csv"),
            os.path.join(GITHUB_DIR, "org_members.csv"),
            os.path.join(GITHUB_DIR, "IPE_documentation.txt"),
        ],
        "stats_fn": lambda files: {"Org admins (production entitlements)": row_count(files[0]),
                                    "Total org members": row_count(files[1])},
    },
    "ESEC-159": {
        "desc": "Code Developers List — GitHub Org Members",
        "files": [
            os.path.join(GITHUB_DIR, "org_members.csv"),
            os.path.join(GITHUB_DIR, "outside_collaborators.csv"),
        ],
        "stats_fn": lambda files: {"Org members": row_count(files[0]),
                                    "Outside collaborators": row_count(files[1])},
    },
    "ESEC-160": {
        "desc": "IPE — Code Developers List",
        "files": [
            os.path.join(GITHUB_DIR, "IPE_documentation.txt"),
            os.path.join(GITHUB_DIR, "IPE_documentation.json"),
        ],
        "stats_fn": lambda files: {"IPE documentation": "Attached — covers GitHub API parameters, row counts, timestamps"},
    },

    # ── AWS: Environment Segregation ─────────────────────────────────
    "ESEC-151": {
        "desc": "SLO Platform — Environment Segregation (AWS VPCs & Subnets)",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
            os.path.join(AWS_DIR, "subnets_us-east-1.csv"),
            os.path.join(AWS_DIR, "subnets_us-west-2.csv"),
        ],
        "stats_fn": lambda files: {"VPCs": row_count(files[0]),
                                    "Subnets (us-east-1)": row_count(files[1]),
                                    "Subnets (us-west-2)": row_count(files[2])},
    },
    "ESEC-152": {
        "desc": "SchoolHub — Environment Segregation",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
        ],
        "stats_fn": lambda files: {"Note": "VPC configurations shared across applications — see ESEC-151 for full data"},
    },
    "ESEC-153": {
        "desc": "MMAX — Environment Segregation",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
        ],
        "stats_fn": lambda files: {"Note": "VPC configurations shared across applications — see ESEC-151 for full data"},
    },
    "ESEC-154": {
        "desc": "CASHI — Environment Segregation",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
        ],
        "stats_fn": lambda files: {"Note": "VPC configurations shared across applications — see ESEC-151 for full data"},
    },
    "ESEC-155": {
        "desc": "Files.com — Environment Segregation",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
        ],
        "stats_fn": lambda files: {"Note": "Files.com is a SaaS platform — VPC configurations attached for cross-reference"},
    },
    "ESEC-156": {
        "desc": "Servicing Platform — Environment Segregation",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
        ],
        "stats_fn": lambda files: {"Note": "VPC configurations shared across applications — see ESEC-151 for full data"},
    },

    # ── AWS: Network & Firewall ──────────────────────────────────────
    "ESEC-192": {
        "desc": "Network Diagram — AWS Network Topology Data",
        "files": [
            os.path.join(AWS_DIR, "vpc_configurations.csv"),
            os.path.join(AWS_DIR, "route_tables_us-east-1.csv"),
            os.path.join(AWS_DIR, "route_tables_us-west-2.csv"),
            os.path.join(AWS_DIR, "internet_gateways_us-east-1.csv"),
            os.path.join(AWS_DIR, "internet_gateways_us-west-2.csv"),
            os.path.join(AWS_DIR, "nat_gateways_us-east-1.csv"),
        ],
        "stats_fn": lambda files: {"VPCs": row_count(files[0]),
                                    "Route table entries (us-east-1)": row_count(files[1]),
                                    "Internet gateways (us-east-1)": row_count(files[3]),
                                    "NAT gateways (us-east-1)": row_count(files[5]),
                                    "Note": "Raw data for network diagram generation — needs visual diagram"},
    },
    "ESEC-193": {
        "desc": "Firewall Deny-All Rules — AWS Security Groups",
        "files": [
            os.path.join(AWS_DIR, "security_group_rules.csv"),
            os.path.join(AWS_DIR, "IPE_documentation.txt"),
        ],
        "stats_fn": lambda files: {"Security group rules": row_count(files[0])},
    },

    # ── AWS: Backups ─────────────────────────────────────────────────
    "ESEC-264": {
        "desc": "Server Backup Listings — RDS Instances & Automated Snapshots",
        "files": [
            os.path.join(AWS_DIR, "rds_backup_configs.csv"),
            os.path.join(AWS_DIR, "rds_automated_snapshots.csv"),
            os.path.join(AWS_DIR, "IPE_documentation.txt"),
        ],
        "stats_fn": lambda files: {"RDS instances": row_count(files[0]),
                                    "Automated snapshots": row_count(files[1])},
    },
    "ESEC-267": {
        "desc": "Backup Failures List — RDS Events",
        "files": [
            os.path.join(AWS_BACKUP_DIR, "backup_events.csv"),
            os.path.join(AWS_BACKUP_DIR, "no_backup_failures.txt"),
            os.path.join(AWS_BACKUP_DIR, "IPE_documentation.txt"),
        ],
        "stats_fn": lambda files: {"Backup events (14 days)": row_count(files[0]),
                                    "Failures detected": "None — confirmation document attached"},
    },
}


def upload_all(base_url, email, api_token, dry_run=False, comments_only=False):
    client = JiraClient(base_url, email, api_token, dry_run=dry_run)

    results = {"success": [], "failed": [], "skipped": []}

    for ticket_key, config in sorted(TICKET_EVIDENCE_MAP.items()):
        desc = config["desc"]
        files = config["files"]
        stats_fn = config.get("stats_fn")

        existing_files = [f for f in files if os.path.exists(f)]
        if not existing_files:
            print(f"  SKIP {ticket_key}: no evidence files found")
            results["skipped"].append(ticket_key)
            continue

        stats = stats_fn(existing_files) if stats_fn else {}

        print(f"  {ticket_key}: {desc}")

        try:
            if not comments_only:
                for filepath in existing_files:
                    fname = os.path.basename(filepath)
                    print(f"    Attaching {fname}...")
                    client.add_attachment(ticket_key, filepath)

            comment_adf = build_comment(ticket_key, desc, existing_files, stats)
            client.add_comment(ticket_key, comment_adf)
            print(f"    Comment added. ({len(existing_files)} files)")

            results["success"].append(ticket_key)
        except Exception as e:
            print(f"    ERROR: {e}")
            results["failed"].append({"key": ticket_key, "error": str(e)})

    print(f"\n{'=' * 60}")
    print(f"UPLOAD SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Success: {len(results['success'])} tickets")
    print(f"  Failed:  {len(results['failed'])} tickets")
    print(f"  Skipped: {len(results['skipped'])} tickets")
    if results["failed"]:
        print(f"\n  Failed tickets:")
        for f in results["failed"]:
            print(f"    {f['key']}: {f['error'][:80]}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload evidence to ESEC Jira tickets")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--comments-only", action="store_true", help="Only post comments (files already uploaded)")
    args = parser.parse_args()

    url = os.environ.get("JIRA_URL", "https://meetearnest.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        print("Set JIRA_EMAIL and JIRA_API_TOKEN environment variables")
        sys.exit(1)

    upload_all(url, email, token, dry_run=args.dry_run, comments_only=args.comments_only)
