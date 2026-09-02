"""
Cross-referencing module — correlates evidence across Jira, GitHub, and AWS
for change management controls. Produces unified change population reports.
"""
import os
import sys
import csv
import re
import json
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector


class CrossReferenceCollector(EvidenceCollector):
    def __init__(self, output_root=None):
        super().__init__("cross_reference", output_root)

    def _load_csv(self, path):
        if not path or not os.path.exists(path):
            return []
        with open(path, newline="") as f:
            return list(csv.DictReader(f))

    def correlate_changes(self, jira_dir, github_dir, system_name=None):
        """
        Correlate Jira tickets with GitHub PRs by looking for ticket keys
        in PR titles/branches. Produces a unified change report showing
        which changes have both a Jira ticket and a merged PR.
        """
        jira_files = [f for f in os.listdir(jira_dir) if f.startswith("change_population_") and f.endswith(".csv")]
        jira_rows = []
        for jf in jira_files:
            jira_rows.extend(self._load_csv(os.path.join(jira_dir, jf)))

        github_pr_file = os.path.join(github_dir, "merged_prs_audit_period.csv")
        prs = self._load_csv(github_pr_file)

        jira_keys = {r["key"] for r in jira_rows if r.get("key")}
        jira_key_pattern = re.compile(r"\b([A-Z]{2,10}-\d+)\b")

        matched = []
        unmatched_prs = []
        for pr in prs:
            title = pr.get("title", "")
            found_keys = jira_key_pattern.findall(title)
            jira_match = [k for k in found_keys if k in jira_keys]
            if jira_match:
                matched.append({
                    "jira_key": "; ".join(jira_match),
                    "pr_repo": pr.get("repo", ""),
                    "pr_number": pr.get("pr_number", ""),
                    "pr_title": title,
                    "pr_author": pr.get("author", ""),
                    "pr_merged_at": pr.get("merged_at", ""),
                    "pr_merged_by": pr.get("merged_by", ""),
                    "pr_url": pr.get("html_url", ""),
                    "match_source": "title",
                })
            else:
                unmatched_prs.append(pr)

        matched_path = self.save_csv(f"change_correlation{'_' + system_name if system_name else ''}.csv", matched)
        unmatched_path = self.save_csv(f"unmatched_prs{'_' + system_name if system_name else ''}.csv", unmatched_prs)

        matched_jira_keys = set()
        for m in matched:
            matched_jira_keys.update(m["jira_key"].split("; "))
        unmatched_jira = [r for r in jira_rows if r.get("key") not in matched_jira_keys]
        unmatched_jira_path = self.save_csv(f"unmatched_jira{'_' + system_name if system_name else ''}.csv", unmatched_jira)

        self.record_ipe(
            evidence_file=matched_path,
            endpoint="(cross-reference computation)",
            params={
                "jira_source": jira_dir,
                "github_source": github_dir,
                "matching_method": "regex on PR title for Jira keys",
            },
            row_count=len(matched),
            notes=f"Correlated changes — {len(matched)} PRs matched to Jira tickets, "
                  f"{len(unmatched_prs)} PRs unmatched, {len(unmatched_jira)} Jira tickets unmatched"
        )

        summary = {
            "total_jira_changes": len(jira_rows),
            "total_github_prs": len(prs),
            "matched": len(matched),
            "unmatched_prs": len(unmatched_prs),
            "unmatched_jira_tickets": len(unmatched_jira),
            "match_rate_prs": f"{len(matched)/max(len(prs),1)*100:.1f}%",
            "match_rate_jira": f"{len(matched_jira_keys)/max(len(jira_keys),1)*100:.1f}%",
        }
        self.save_json(f"correlation_summary{'_' + system_name if system_name else ''}.json", summary)

        print(f"  Correlated: {len(matched)} matched, {len(unmatched_prs)} PRs unmatched, {len(unmatched_jira)} Jira unmatched")
        return summary

    def build_change_population_report(self, jira_dir, github_dir):
        """
        Build the complete change population report combining all sources.
        This is the main deliverable for ESEC-142 through ESEC-148.
        """
        self.correlate_changes(jira_dir, github_dir)

        jira_files = [f for f in os.listdir(jira_dir) if f.startswith("change_population_") and f.endswith(".csv")]
        system_counts = {}
        for jf in jira_files:
            system = jf.replace("change_population_", "").replace(".csv", "")
            rows = self._load_csv(os.path.join(jira_dir, jf))
            system_counts[system] = len(rows)

        github_pr_file = os.path.join(github_dir, "merged_prs_audit_period.csv")
        prs = self._load_csv(github_pr_file)
        repo_counts = {}
        for pr in prs:
            repo = pr.get("repo", "unknown")
            repo_counts[repo] = repo_counts.get(repo, 0) + 1

        report = (
            f"CHANGE MANAGEMENT POPULATION REPORT\n"
            f"Audit Period: 2025-10-01 to 2026-08-31 (population cutoff)\n"
            f"Generated: {datetime.datetime.now().isoformat()}\n"
            f"{'=' * 70}\n\n"
            f"JIRA CHANGE TICKETS BY SYSTEM:\n"
        )
        for system, count in sorted(system_counts.items()):
            report += f"  {system}: {count} tickets\n"
        report += f"  TOTAL: {sum(system_counts.values())} tickets\n\n"

        report += f"GITHUB MERGED PRs BY REPOSITORY:\n"
        for repo, count in sorted(repo_counts.items(), key=lambda x: -x[1]):
            report += f"  {repo}: {count} PRs\n"
        report += f"  TOTAL: {sum(repo_counts.values())} PRs\n\n"

        report += (
            f"CROSS-REFERENCE:\n"
            f"  See change_correlation.csv for Jira↔GitHub matches\n"
            f"  See unmatched_prs.csv for PRs without Jira tickets\n"
            f"  See unmatched_jira.csv for Jira tickets without PRs\n\n"
            f"IPE DOCUMENTATION:\n"
            f"  See IPE_documentation.json and IPE_documentation.txt\n"
        )

        self.save_text("change_population_report.txt", report)
        print(f"\n  Change population report generated")
        return report


def run_cross_reference(jira_evidence_dir, github_evidence_dir, output_root=None):
    c = CrossReferenceCollector(output_root)

    print("\n=== Cross-Reference Evidence ===\n")

    print("[1/1] Correlating Jira tickets with GitHub PRs...")
    c.build_change_population_report(jira_evidence_dir, github_evidence_dir)

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    jira_dir = sys.argv[1] if len(sys.argv) > 1 else None
    github_dir = sys.argv[2] if len(sys.argv) > 2 else None
    if not jira_dir or not github_dir:
        print("Usage: python cross_reference.py <jira_evidence_dir> <github_evidence_dir>")
        sys.exit(1)
    run_cross_reference(jira_dir, github_dir)
