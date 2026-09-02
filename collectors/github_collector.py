"""
GitHub evidence collector — pulls org members, repo collaborators, PRs,
and branch protection configs. Cross-references with Jira for change management.
"""
import os
import sys
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector

AUDIT_PERIOD_START = "2025-10-01"
POPULATION_CUTOFF_END = "2026-08-31"


class GitHubCollector(EvidenceCollector):
    def __init__(self, token, org, output_root=None):
        super().__init__("github", output_root)
        self.org = org
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.base = "https://api.github.com"

    def _get_paginated(self, url, params=None):
        results = []
        params = params or {}
        params["per_page"] = 100
        page = 1
        while True:
            params["page"] = page
            resp = self.session.get(url, params=params)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset - time.time(), 1)
                print(f"  Rate limited, waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            results.extend(data)
            if len(data) < 100:
                break
            page += 1
        return results

    # ── Org Members (ESEC-159 Code Developers, ESEC-158 Entitlements) ──

    def collect_org_members(self):
        """Export all org members with their roles."""
        members = self._get_paginated(f"{self.base}/orgs/{self.org}/members")
        rows = []
        for m in members:
            rows.append({
                "login": m["login"],
                "id": m["id"],
                "type": m.get("type", ""),
                "site_admin": m.get("site_admin", False),
                "html_url": m.get("html_url", ""),
            })

        path = self.save_csv("org_members.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint=f"GET /orgs/{self.org}/members",
            params={"per_page": 100, "role": "all"},
            row_count=len(rows),
            pagination=f"Paginated, {len(rows)} total members",
            notes="Complete org member listing for code developer population (ESEC-159) and entitlements (ESEC-158)"
        )
        print(f"  Org members: {len(rows)}")

        admins = self._get_paginated(f"{self.base}/orgs/{self.org}/members", {"role": "admin"})
        admin_rows = [{"login": m["login"], "id": m["id"], "role": "admin"} for m in admins]
        admin_path = self.save_csv("org_admins.csv", admin_rows)
        self.record_ipe(
            evidence_file=admin_path,
            endpoint=f"GET /orgs/{self.org}/members?role=admin",
            params={"role": "admin"},
            row_count=len(admin_rows),
            notes="Org admin listing — production change entitlements (ESEC-158)"
        )
        print(f"  Org admins: {len(admin_rows)}")
        return rows, admin_rows

    # ── Repo Listing with Branch Protection ───────────────────────────

    def collect_repos_and_protection(self):
        """List all repos and their default branch protection status."""
        repos = self._get_paginated(f"{self.base}/orgs/{self.org}/repos")
        rows = []
        for r in repos:
            row = {
                "name": r["name"],
                "full_name": r["full_name"],
                "private": r["private"],
                "default_branch": r.get("default_branch", "main"),
                "archived": r.get("archived", False),
                "created_at": r.get("created_at", ""),
                "pushed_at": r.get("pushed_at", ""),
            }
            if not r.get("archived", False):
                try:
                    bp_resp = self.session.get(
                        f"{self.base}/repos/{self.org}/{r['name']}/branches/{r.get('default_branch', 'main')}/protection"
                    )
                    if bp_resp.status_code == 200:
                        bp = bp_resp.json()
                        row["branch_protection"] = True
                        row["required_reviews"] = bp.get("required_pull_request_reviews", {}).get("required_approving_review_count", 0) if bp.get("required_pull_request_reviews") else 0
                        row["status_checks"] = bool(bp.get("required_status_checks"))
                    else:
                        row["branch_protection"] = False
                        row["required_reviews"] = None
                        row["status_checks"] = None
                except Exception:
                    row["branch_protection"] = "error"
            rows.append(row)

        path = self.save_csv("repos_branch_protection.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint=f"GET /orgs/{self.org}/repos + branch protection",
            params={},
            row_count=len(rows),
            notes="Repo listing with branch protection config for change management controls"
        )
        print(f"  Repos: {len(rows)} ({sum(1 for r in rows if r.get('branch_protection') is True)} with branch protection)")
        return rows

    # ── PRs merged in audit period (cross-ref with Jira changes) ──────

    def collect_merged_prs(self, repo_names=None):
        """Pull all PRs merged during the audit period for specified repos."""
        if repo_names is None:
            all_repos = self._get_paginated(f"{self.base}/orgs/{self.org}/repos")
            repo_names = [
                r["name"] for r in all_repos
                if not r.get("archived") and r.get("pushed_at", "") >= AUDIT_PERIOD_START
            ]

        all_prs = []
        for repo in repo_names:
            prs = self._get_paginated(
                f"{self.base}/repos/{self.org}/{repo}/pulls",
                {"state": "closed", "sort": "updated", "direction": "desc"}
            )
            for pr in prs:
                if not pr.get("merged_at"):
                    continue
                merged = pr["merged_at"][:10]
                if merged < AUDIT_PERIOD_START or merged > POPULATION_CUTOFF_END:
                    continue
                all_prs.append({
                    "repo": repo,
                    "pr_number": pr["number"],
                    "title": pr["title"],
                    "author": pr["user"]["login"] if pr.get("user") else "",
                    "merged_at": pr["merged_at"],
                    "merged_by": pr.get("merged_by", {}).get("login", "") if pr.get("merged_by") else "",
                    "base_branch": pr.get("base", {}).get("ref", ""),
                    "html_url": pr.get("html_url", ""),
                    "review_comments": pr.get("review_comments", 0),
                })
            print(f"  {repo}: {sum(1 for p in all_prs if p['repo'] == repo)} merged PRs in period")

        path = self.save_csv("merged_prs_audit_period.csv", all_prs)
        self.record_ipe(
            evidence_file=path,
            endpoint=f"GET /repos/{self.org}/*/pulls?state=closed",
            params={"repos_scanned": len(repo_names), "period": f"{AUDIT_PERIOD_START} to {POPULATION_CUTOFF_END}"},
            row_count=len(all_prs),
            pagination=f"Scanned {len(repo_names)} repos",
            notes="Merged PRs in audit period — cross-reference with Jira change populations"
        )
        print(f"  Total merged PRs: {len(all_prs)}")
        return all_prs

    # ── Outside Collaborators (contractor/external access) ────────────

    def collect_outside_collaborators(self):
        """List outside collaborators for contractor population."""
        collabs = self._get_paginated(f"{self.base}/orgs/{self.org}/outside_collaborators")
        rows = [{"login": c["login"], "id": c["id"], "html_url": c.get("html_url", "")} for c in collabs]
        path = self.save_csv("outside_collaborators.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint=f"GET /orgs/{self.org}/outside_collaborators",
            params={},
            row_count=len(rows),
            notes="Outside collaborators — supplements contractor access population"
        )
        print(f"  Outside collaborators: {len(rows)}")
        return rows


def run_all(token, org, output_root=None):
    c = GitHubCollector(token, org, output_root)

    print("\n=== GitHub Evidence Collection ===\n")

    print("[1/4] Org members & admins...")
    c.collect_org_members()

    print("[2/4] Repos & branch protection...")
    c.collect_repos_and_protection()

    print("[3/4] Merged PRs in audit period...")
    c.collect_merged_prs()

    print("[4/4] Outside collaborators...")
    c.collect_outside_collaborators()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    org = os.environ.get("GITHUB_ORG", "meetearnest")
    if not token:
        print("Set GITHUB_TOKEN environment variable")
        sys.exit(1)
    run_all(token, org)
