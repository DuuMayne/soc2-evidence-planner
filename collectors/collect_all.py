#!/usr/bin/env python3
"""
Master evidence collection runner — orchestrates all collectors,
produces per-ticket evidence mapping, and generates final IPE bundle.

Usage:
  python3 -m collectors.collect_all --systems jira,github,aws,okta,google,files_com
  python3 -m collectors.collect_all --systems jira   # run just one
  python3 -m collectors.collect_all --list            # show what each system covers

Environment variables (set only the ones you need):
  JIRA_EMAIL, JIRA_API_TOKEN          — Jira Cloud
  GITHUB_TOKEN, GITHUB_ORG            — GitHub
  AWS_PROFILE, AWS_REGIONS            — AWS CLI
  OKTA_DOMAIN, OKTA_API_TOKEN         — Okta
  GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_ADMIN_EMAIL  — Google Workspace
  FILES_COM_API_KEY                   — Files.com
"""
import argparse
import json
import os
import sys
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


EVIDENCE_OUTPUT_ROOT = os.path.expanduser("~/Downloads/2026 SOC II/evidence")

TICKET_MAP = {
    "jira": {
        "ESEC-142": {"method": "collect_change_populations", "desc": "SLO Platform change population"},
        "ESEC-143": {"method": "collect_change_populations", "desc": "SchoolHub change population"},
        "ESEC-144": {"method": "collect_change_populations", "desc": "CASHI change population"},
        "ESEC-145": {"method": "collect_change_populations", "desc": "MMAX change population"},
        "ESEC-146": {"method": "collect_change_populations", "desc": "Files.com change population"},
        "ESEC-147": {"method": "collect_change_populations", "desc": "Servicing Platform change population"},
        "ESEC-148": {"method": "collect_change_populations", "desc": "IPE for all change populations"},
        "ESEC-162": {"method": "collect_patching_tickets", "desc": "Patching JIRA tickets"},
        "ESEC-171": {"method": "collect_access_requests", "desc": "New/Modified SLO access population"},
        "ESEC-233": {"method": "collect_security_incidents", "desc": "Security incidents list"},
        "ESEC-234": {"method": "collect_security_incidents", "desc": "IPE for security incidents"},
        "ESEC-235": {"method": "collect_security_incidents", "desc": "No incidents confirmation"},
        "ESEC-254": {"method": "collect_vulnerability_tickets", "desc": "Vulnerability JIRA tickets"},
    },
    "github": {
        "ESEC-158": {"method": "collect_org_members", "desc": "Production change entitlements (org admins)"},
        "ESEC-159": {"method": "collect_org_members", "desc": "Code developers list"},
        "ESEC-160": {"method": "collect_org_members", "desc": "IPE for code developers list"},
    },
    "aws": {
        "ESEC-151": {"method": "collect_vpc_configs", "desc": "SLO Platform environment segregation"},
        "ESEC-152": {"method": "collect_vpc_configs", "desc": "SchoolHub environment segregation"},
        "ESEC-153": {"method": "collect_vpc_configs", "desc": "MMAX environment segregation"},
        "ESEC-154": {"method": "collect_vpc_configs", "desc": "CASHI environment segregation"},
        "ESEC-155": {"method": "collect_vpc_configs", "desc": "Files.com environment segregation"},
        "ESEC-156": {"method": "collect_vpc_configs", "desc": "Servicing Platform environment segregation"},
        "ESEC-192": {"method": "collect_network_topology", "desc": "Network diagram data"},
        "ESEC-193": {"method": "collect_security_groups", "desc": "Firewall deny-all rules"},
        "ESEC-264": {"method": "collect_backup_configs", "desc": "Server backup listings"},
        "ESEC-267": {"method": "collect_backup_failures", "desc": "Backup failures list"},
    },
    "okta": {
        "ESEC-166": {"method": "collect_password_policies", "desc": "Okta password settings"},
        "ESEC-205": {"method": "collect_admin_users", "desc": "Admin listings"},
        "ESEC-206": {"method": "collect_admin_users", "desc": "IPE for admin listings"},
    },
    "google": {
        "ESEC-167": {"method": "collect_password_settings", "desc": "G-Suite password settings"},
    },
    "files_com": {
        "ESEC-168": {"method": "collect_site_settings", "desc": "Files.com password settings"},
        "ESEC-201": {"method": "collect_users", "desc": "New Files.com accounts population"},
        "ESEC-202": {"method": "collect_users", "desc": "IPE for Files.com accounts"},
    },
    "cross_reference": {
        "ESEC-142": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (SLO)"},
        "ESEC-143": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (SchoolHub)"},
        "ESEC-144": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (CASHI)"},
        "ESEC-145": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (MMAX)"},
        "ESEC-146": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (Files.com)"},
        "ESEC-147": {"method": "correlate_changes", "desc": "Jira+GitHub change correlation (Servicing)"},
    },
}


def list_coverage():
    print("\nEVIDENCE COLLECTION COVERAGE BY SYSTEM\n")
    for system, tickets in sorted(TICKET_MAP.items()):
        print(f"  {system.upper()}:")
        for ticket, info in sorted(tickets.items()):
            print(f"    {ticket}: {info['desc']}")
        print()

    all_tickets = set()
    for tickets in TICKET_MAP.values():
        all_tickets.update(tickets.keys())
    print(f"  Total unique tickets covered: {len(all_tickets)}")
    print()


def run_system(system_name):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output = os.path.join(EVIDENCE_OUTPUT_ROOT, system_name, ts)

    if system_name == "jira":
        from collectors.jira_collector import run_all
        url = os.environ.get("JIRA_URL", "https://meetearnest.atlassian.net")
        email = os.environ.get("JIRA_EMAIL")
        token = os.environ.get("JIRA_API_TOKEN")
        if not email or not token:
            print(f"SKIP {system_name}: Set JIRA_EMAIL and JIRA_API_TOKEN")
            return None
        return run_all(url, email, token, output)

    elif system_name == "github":
        from collectors.github_collector import run_all
        token = os.environ.get("GITHUB_TOKEN")
        org = os.environ.get("GITHUB_ORG", "meetearnest")
        if not token:
            print(f"SKIP {system_name}: Set GITHUB_TOKEN")
            return None
        return run_all(token, org, output)

    elif system_name == "aws":
        from collectors.aws_collector import run_all
        profile = os.environ.get("AWS_PROFILE")
        regions = os.environ.get("AWS_REGIONS", "us-west-2,us-east-1").split(",")
        return run_all(profile, regions, output)

    elif system_name == "okta":
        from collectors.okta_collector import run_all
        domain = os.environ.get("OKTA_DOMAIN")
        token = os.environ.get("OKTA_API_TOKEN")
        if not domain or not token:
            print(f"SKIP {system_name}: Set OKTA_DOMAIN and OKTA_API_TOKEN")
            return None
        return run_all(domain, token, output)

    elif system_name == "google":
        from collectors.google_workspace_collector import run_all
        sa_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        admin = os.environ.get("GOOGLE_ADMIN_EMAIL")
        customer = os.environ.get("GOOGLE_CUSTOMER_ID", "my_customer")
        if not sa_file or not admin:
            print(f"SKIP {system_name}: Set GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_ADMIN_EMAIL")
            return None
        return run_all(sa_file, admin, customer, output)

    elif system_name == "files_com":
        from collectors.files_com_collector import run_all
        api_key = os.environ.get("FILES_COM_API_KEY")
        if not api_key:
            print(f"SKIP {system_name}: Set FILES_COM_API_KEY")
            return None
        return run_all(api_key, output)

    elif system_name == "cross_reference":
        from collectors.cross_reference import run_cross_reference
        jira_dir = _find_latest_evidence_dir("jira")
        github_dir = _find_latest_evidence_dir("github")
        if not jira_dir or not github_dir:
            print(f"SKIP {system_name}: Run jira and github collectors first")
            return None
        return run_cross_reference(jira_dir, github_dir, output)

    else:
        print(f"Unknown system: {system_name}")
        return None


def _find_latest_evidence_dir(system_name):
    base = os.path.join(EVIDENCE_OUTPUT_ROOT, system_name)
    if not os.path.exists(base):
        return None
    runs = sorted(os.listdir(base), reverse=True)
    return os.path.join(base, runs[0]) if runs else None


def main():
    parser = argparse.ArgumentParser(description="SOC 2 Evidence Collection")
    parser.add_argument("--systems", type=str,
                        help="Comma-separated list of systems to collect from")
    parser.add_argument("--list", action="store_true",
                        help="List all systems and their ticket coverage")
    args = parser.parse_args()

    if args.list:
        list_coverage()
        return

    if not args.systems:
        print("Specify --systems or --list. Available: jira,github,aws,okta,google,files_com,cross_reference")
        return

    systems = [s.strip() for s in args.systems.split(",")]
    results = {}

    for system in systems:
        try:
            result = run_system(system)
            results[system] = result
        except Exception as e:
            print(f"\nERROR running {system}: {e}")
            results[system] = {"error": str(e)}

    if "jira" in results and "github" in results and "cross_reference" not in systems:
        if results.get("jira") and results.get("github"):
            print("\nTIP: Run with --systems cross_reference to correlate Jira+GitHub changes")

    print("\n" + "=" * 70)
    print("EVIDENCE COLLECTION SUMMARY")
    print("=" * 70)
    for system, result in results.items():
        if result and "error" not in result:
            files = result.get("files_generated", [])
            print(f"  {system}: {len(files)} files → {result.get('output_dir', 'N/A')}")
        elif result and "error" in result:
            print(f"  {system}: ERROR — {result['error']}")
        else:
            print(f"  {system}: SKIPPED (missing credentials)")

    manifest_path = os.path.join(EVIDENCE_OUTPUT_ROOT, f"collection_manifest_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump({
            "run_timestamp": datetime.datetime.now().isoformat(),
            "systems_requested": systems,
            "results": {k: v for k, v in results.items() if v},
        }, f, indent=2, default=str)
    print(f"\n  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
