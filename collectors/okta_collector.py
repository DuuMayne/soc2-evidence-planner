"""
Okta evidence collector — pulls password policies, user listings, and admin listings.

Requires: OKTA_DOMAIN (e.g., earnest.okta.com) and OKTA_API_TOKEN env vars.
"""
import os
import sys
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector


class OktaCollector(EvidenceCollector):
    def __init__(self, domain, api_token, output_root=None):
        super().__init__("okta", output_root)
        self.base = f"https://{domain}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"SSWS {api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _get_paginated(self, url, params=None):
        results = []
        params = params or {}
        next_url = url
        while next_url:
            resp = self.session.get(next_url, params=params if next_url == url else None)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("x-rate-limit-reset", time.time() + 30)) - int(time.time())
                print(f"  Rate limited, waiting {max(retry_after, 1)}s...")
                time.sleep(max(retry_after, 1))
                continue
            resp.raise_for_status()
            results.extend(resp.json())
            links = resp.links
            next_url = links.get("next", {}).get("url")
        return results

    # ── Password Policy (ESEC-166) ────────────────────────────────────

    def collect_password_policies(self):
        """Export Okta password policies with their settings."""
        policies = self._get_paginated(f"{self.base}/policies", {"type": "PASSWORD"})
        rows = []
        for p in policies:
            settings = p.get("settings", {}).get("password", {})
            complexity = settings.get("complexity", {})
            age = settings.get("age", {})
            lockout = settings.get("lockout", {})
            rows.append({
                "id": p["id"],
                "name": p.get("name", ""),
                "status": p.get("status", ""),
                "priority": p.get("priority", ""),
                "min_length": complexity.get("minLength", ""),
                "min_lowercase": complexity.get("minLowerCase", ""),
                "min_uppercase": complexity.get("minUpperCase", ""),
                "min_number": complexity.get("minNumber", ""),
                "min_symbol": complexity.get("minSymbol", ""),
                "exclude_username": complexity.get("excludeUsername", ""),
                "dictionary_lookup": complexity.get("dictionary", {}).get("common", {}).get("exclude", ""),
                "max_age_days": age.get("maxAgeDays", ""),
                "min_age_minutes": age.get("minAgeMinutes", ""),
                "history_count": age.get("historyCount", ""),
                "expire_warn_days": age.get("expireWarnDays", ""),
                "max_attempts": lockout.get("maxAttempts", ""),
                "auto_unlock_minutes": lockout.get("autoUnlockMinutes", ""),
                "show_lockout_failures": lockout.get("showLockoutFailures", ""),
            })

        path = self.save_csv("password_policies.csv", rows)
        raw_path = self.save_json("password_policies_raw.json", policies)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /api/v1/policies?type=PASSWORD",
            params={"type": "PASSWORD"},
            row_count=len(rows),
            notes="Okta password policy configuration (ESEC-166)"
        )
        print(f"  Password policies: {len(rows)}")
        return rows

    # ── MFA Policies ──────────────────────────────────────────────────

    def collect_mfa_policies(self):
        """Export MFA enrollment policies."""
        policies = self._get_paginated(f"{self.base}/policies", {"type": "MFA_ENROLL"})
        rows = []
        for p in policies:
            settings = p.get("settings", {}).get("factors", {})
            enabled = [k for k, v in settings.items() if v.get("enroll", {}).get("self") == "REQUIRED" or v.get("enroll", {}).get("self") == "OPTIONAL"]
            rows.append({
                "id": p["id"],
                "name": p.get("name", ""),
                "status": p.get("status", ""),
                "priority": p.get("priority", ""),
                "enabled_factors": "; ".join(enabled),
            })

        path = self.save_csv("mfa_policies.csv", rows)
        raw_path = self.save_json("mfa_policies_raw.json", policies)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /api/v1/policies?type=MFA_ENROLL",
            params={"type": "MFA_ENROLL"},
            row_count=len(rows),
            notes="Okta MFA enrollment policies"
        )
        print(f"  MFA policies: {len(rows)}")
        return rows

    # ── Admin Listings (ESEC-205, ESEC-206) ──────────────────────────

    def collect_admin_users(self):
        """Export users with admin roles."""
        admins = self._get_paginated(f"{self.base}/users", {"filter": 'status eq "ACTIVE"', "search": 'profile.userType eq "Admin"'})
        if not admins:
            admins = self._get_paginated(f"{self.base}/groups")
            admin_groups = [g for g in admins if "admin" in g.get("profile", {}).get("name", "").lower()]
            all_admin_users = []
            for group in admin_groups:
                members = self._get_paginated(f"{self.base}/groups/{group['id']}/users")
                for m in members:
                    all_admin_users.append({
                        "user_id": m["id"],
                        "login": m.get("profile", {}).get("login", ""),
                        "email": m.get("profile", {}).get("email", ""),
                        "first_name": m.get("profile", {}).get("firstName", ""),
                        "last_name": m.get("profile", {}).get("lastName", ""),
                        "status": m.get("status", ""),
                        "admin_group": group.get("profile", {}).get("name", ""),
                    })
            rows = all_admin_users
        else:
            rows = []
            for u in admins:
                rows.append({
                    "user_id": u["id"],
                    "login": u.get("profile", {}).get("login", ""),
                    "email": u.get("profile", {}).get("email", ""),
                    "first_name": u.get("profile", {}).get("firstName", ""),
                    "last_name": u.get("profile", {}).get("lastName", ""),
                    "status": u.get("status", ""),
                })

        path = self.save_csv("admin_users.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /api/v1/groups + /groups/{id}/users (admin groups)",
            params={"filter": "admin groups"},
            row_count=len(rows),
            notes="Admin user listing (ESEC-205, ESEC-206)"
        )
        print(f"  Admin users: {len(rows)}")
        return rows

    # ── Full User Listing ─────────────────────────────────────────────

    def collect_all_users(self):
        """Export all active users — supports access review populations."""
        users = self._get_paginated(f"{self.base}/users", {"filter": 'status eq "ACTIVE"', "limit": 200})
        rows = []
        for u in users:
            p = u.get("profile", {})
            rows.append({
                "user_id": u["id"],
                "login": p.get("login", ""),
                "email": p.get("email", ""),
                "first_name": p.get("firstName", ""),
                "last_name": p.get("lastName", ""),
                "department": p.get("department", ""),
                "title": p.get("title", ""),
                "manager": p.get("manager", ""),
                "status": u.get("status", ""),
                "created": u.get("created", ""),
                "last_login": u.get("lastLogin", ""),
            })

        path = self.save_csv("all_active_users.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /api/v1/users?filter=status eq \"ACTIVE\"",
            params={"filter": "status eq ACTIVE", "limit": 200},
            row_count=len(rows),
            pagination=f"Paginated, collected {len(rows)} users total",
            notes="Full active user listing — supports access populations and reviews"
        )
        print(f"  Active users: {len(rows)}")
        return rows


def run_all(domain, api_token, output_root=None):
    c = OktaCollector(domain, api_token, output_root)

    print("\n=== Okta Evidence Collection ===\n")

    print("[1/4] Password policies...")
    c.collect_password_policies()

    print("[2/4] MFA policies...")
    c.collect_mfa_policies()

    print("[3/4] Admin users...")
    c.collect_admin_users()

    print("[4/4] All active users...")
    c.collect_all_users()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    domain = os.environ.get("OKTA_DOMAIN")
    token = os.environ.get("OKTA_API_TOKEN")
    if not domain or not token:
        print("Set OKTA_DOMAIN and OKTA_API_TOKEN environment variables")
        sys.exit(1)
    run_all(domain, token)
