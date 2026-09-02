"""
Jira evidence collector — pulls populations, samples, and reports
for change management, access management, patching, vulnerabilities, and incidents.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collectors.base import EvidenceCollector
from scripts.jira_client import JiraClient


AUDIT_PERIOD_START = "2025-10-01"
AUDIT_PERIOD_END = "2026-09-30"
POPULATION_CUTOFF_END = "2026-08-31"

SAMPLE_MONTHS = {
    "oct_2025": ("2025-10-01", "2025-10-31"),
    "dec_2025": ("2025-12-01", "2025-12-31"),
    "jun_2026": ("2026-06-01", "2026-06-30"),
}

SAMPLE_QUARTERS = {
    "q4_2025": ("2025-10-01", "2025-12-31"),
    "q2_2026": ("2026-04-01", "2026-06-30"),
}


class JiraCollector(EvidenceCollector):
    def __init__(self, base_url, email, api_token, output_root=None):
        super().__init__("jira", output_root)
        self.client = JiraClient(base_url, email, api_token)

    def _search_and_export(self, jql, fields, filename, description):
        issues = self.client.search_issues_all(jql, fields=fields)
        rows = []
        for issue in issues:
            row = {"key": issue["key"]}
            f = issue.get("fields", {})
            for field in fields.split(","):
                field = field.strip()
                val = f.get(field)
                if isinstance(val, dict):
                    val = val.get("displayName") or val.get("name") or val.get("value") or str(val)
                elif isinstance(val, list):
                    val = "; ".join(
                        (item.get("displayName") or item.get("name") or str(item))
                        if isinstance(item, dict) else str(item)
                        for item in val
                    )
                row[field] = val
            rows.append(row)

        path = self.save_csv(filename, rows)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /rest/api/3/search/jql",
            params={"jql": jql, "fields": fields},
            row_count=len(rows),
            pagination=f"Paginated at 100/page, collected all {len(issues)} results",
            notes=description,
        )
        return rows, path

    # ── Change Management Populations (ESEC-142 to ESEC-147) ──────────

    def collect_change_populations(self, project_keys=None):
        """Pull all change/PR tickets completed during the audit period.
        Uses status in (Done, Resolved, Closed) and updated date since
        many projects don't set the resolved date field."""
        if project_keys is None:
            project_keys = ["ENG", "SIT", "PL", "LA", "LC", "LD", "SLO2", "NEW",
                            "COR", "ID", "MOB", "INF", "PLAT", "RE", "SSI",
                            "GMDEVOPS", "NUC", "CLOUDP", "ADL", "NS"]

        all_rows = []
        for pk in project_keys:
            jql = (
                f'project = "{pk}" AND issuetype in (Story, Task, Bug, "Sub-task", Spike) '
                f'AND status in (Done, Resolved, Closed) '
                f'AND updated >= "{AUDIT_PERIOD_START}" '
                f'AND updated <= "{POPULATION_CUTOFF_END}" '
                f'ORDER BY updated ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,priority,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"change_population_{pk}.csv",
                f"Change population for project {pk} — all resolved items in audit period"
            )
            all_rows.extend(rows)
            print(f"  {pk}: {len(rows)} changes found")

        combined = self.save_csv("change_population_ALL.csv", all_rows)
        if combined:
            self.record_ipe(
                evidence_file=combined,
                endpoint="(combined file)",
                params={"source_files": [f"change_population_{pk}.csv" for pk in project_keys]},
                row_count=len(all_rows),
                notes="Combined change population across all in-scope systems"
            )
        return all_rows

    # ── Patching Tickets (ESEC-162) ───────────────────────────────────

    def collect_patching_tickets(self, projects=None, label="patching"):
        """Pull patching Jira tickets for the sample months.
        Searches SEC, ESEC, and SRE projects by default."""
        if projects is None:
            projects = ["SEC", "ESEC", "SRE", "INF"]
        all_rows = []
        for period_name, (start, end) in SAMPLE_MONTHS.items():
            jql = (
                f'project in ({",".join(projects)}) AND (labels = "{label}" OR summary ~ "patch*" OR summary ~ "security update") '
                f'AND created >= "{start}" AND created <= "{end}" '
                f'ORDER BY created ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"patching_tickets_{period_name}.csv",
                f"Patching tickets for {period_name}"
            )
            all_rows.extend(rows)
            print(f"  Patching {period_name}: {len(rows)} tickets")

        jql_all = (
            f'project in ({",".join(projects)}) AND (labels = "{label}" OR summary ~ "patch*" OR summary ~ "security update") '
            f'AND created >= "{AUDIT_PERIOD_START}" AND created <= "{AUDIT_PERIOD_END}" '
            f'ORDER BY created ASC'
        )
        fields = "summary,status,issuetype,assignee,created,resolutiondate,labels"
        rows, path = self._search_and_export(
            jql_all, fields,
            "patching_tickets_full_period.csv",
            "All patching tickets in full audit period"
        )
        return all_rows

    # ── Access Request Tickets (ESEC-171 to ESEC-174) ─────────────────

    def collect_access_requests(self, project="ESEC", labels=None):
        """Pull new/modified/transfer/termination access request tickets."""
        if labels is None:
            labels = ["access-request", "access-modification", "access-termination"]

        all_rows = []
        for label in labels:
            jql = (
                f'project = "{project}" AND labels = "{label}" '
                f'AND created >= "{AUDIT_PERIOD_START}" AND created <= "{POPULATION_CUTOFF_END}" '
                f'ORDER BY created ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"access_requests_{label}.csv",
                f"Access request population — label: {label}"
            )
            all_rows.extend(rows)
            print(f"  Access {label}: {len(rows)} tickets")
        return all_rows

    # ── Vulnerability Tickets (ESEC-254) ──────────────────────────────

    def collect_vulnerability_tickets(self, project="SEC", label="vulnerability"):
        """Pull vulnerability remediation tickets for sample months."""
        all_rows = []
        for period_name, (start, end) in SAMPLE_MONTHS.items():
            jql = (
                f'project = "{project}" AND labels = "{label}" '
                f'AND created >= "{start}" AND created <= "{end}" '
                f'ORDER BY created ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,priority,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"vuln_tickets_{period_name}.csv",
                f"Vulnerability tickets for {period_name}"
            )
            all_rows.extend(rows)
            print(f"  Vuln tickets {period_name}: {len(rows)} tickets")
        return all_rows

    # ── Security Incidents (ESEC-233, ESEC-234) ──────────────────────

    def collect_security_incidents(self, projects=None):
        """Pull all security incident tickets in the audit period from ESEC and INC."""
        if projects is None:
            projects = ["ESEC", "INC", "SEC"]
        all_rows = []
        for project in projects:
            jql = (
                f'project = "{project}" AND issuetype in ("Incident", "Bug", "Alert") '
                f'AND created >= "{AUDIT_PERIOD_START}" AND created <= "{AUDIT_PERIOD_END}" '
                f'ORDER BY created ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,priority,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"security_incidents_{project}.csv",
                f"Security incidents from {project} during audit period"
            )
            all_rows.extend(rows)
            print(f"  {project} incidents: {len(rows)} found")

        if all_rows:
            self.save_csv("security_incidents_ALL.csv", all_rows)

        if len(all_rows) == 0:
            no_incidents_text = (
                f"CONFIRMATION: No security incidents were recorded in Jira projects {', '.join(projects)} "
                f"during the audit period ({AUDIT_PERIOD_START} to {AUDIT_PERIOD_END}).\n"
                f"This report was generated programmatically by querying the Jira Cloud API "
                f"for all issues of type 'Incident' in the specified date range.\n"
            )
            self.save_text("no_incidents_confirmation.txt", no_incidents_text)
            self.record_ipe(
                evidence_file="no_incidents_confirmation.txt",
                endpoint="GET /rest/api/3/search/jql",
                params={"projects": projects},
                row_count=0,
                notes="Zero incidents found — confirmation document generated"
            )
        return all_rows

    # ── Downtime/Patching Announcements (ESEC-250) ────────────────────

    def collect_downtime_announcements(self, project="ESEC", labels=None):
        """Pull quarterly downtime/maintenance announcement tickets."""
        if labels is None:
            labels = ["maintenance", "downtime", "patching-announcement"]
        for label in labels:
            jql = (
                f'project = "{project}" AND labels = "{label}" '
                f'AND created >= "{AUDIT_PERIOD_START}" AND created <= "{AUDIT_PERIOD_END}" '
                f'ORDER BY created ASC'
            )
            fields = "summary,status,issuetype,assignee,created,resolutiondate,labels"
            rows, path = self._search_and_export(
                jql, fields,
                f"downtime_announcements_{label}.csv",
                f"Downtime/maintenance announcements — label: {label}"
            )
            print(f"  Downtime {label}: {len(rows)} tickets")


def run_all(base_url, email, api_token, output_root=None):
    c = JiraCollector(base_url, email, api_token, output_root)

    print("\n=== Jira Evidence Collection ===\n")

    print("[1/5] Change populations...")
    c.collect_change_populations()

    print("[2/5] Patching tickets...")
    c.collect_patching_tickets()

    print("[3/5] Access request populations...")
    c.collect_access_requests()

    print("[4/5] Vulnerability tickets...")
    c.collect_vulnerability_tickets()

    print("[5/5] Security incidents...")
    c.collect_security_incidents()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    print(f"IPE records: {s['ipe_records']}")
    return s


if __name__ == "__main__":
    url = os.environ.get("JIRA_URL", "https://meetearnest.atlassian.net")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        print("Set JIRA_EMAIL and JIRA_API_TOKEN environment variables")
        sys.exit(1)
    run_all(url, email, token)
