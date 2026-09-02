"""
Files.com evidence collector — pulls user accounts, password settings,
and new account populations.

Requires: FILES_COM_API_KEY env var.
API docs: https://developers.files.com/
"""
import os
import sys
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector

AUDIT_PERIOD_START = "2025-10-01"
POPULATION_CUTOFF_END = "2026-08-31"


class FilesComCollector(EvidenceCollector):
    def __init__(self, api_key, output_root=None):
        super().__init__("files_com", output_root)
        self.base = "https://app.files.com/api/rest/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "X-FilesAPI-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _get_paginated(self, endpoint, params=None):
        results = []
        params = params or {}
        params["per_page"] = 1000
        page = 1
        while True:
            params["page"] = page
            resp = self.session.get(f"{self.base}{endpoint}", params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            results.extend(data)
            if len(data) < 1000:
                break
            page += 1
        return results

    # ── User Accounts (ESEC-201, ESEC-202) ───────────────────────────

    def collect_users(self):
        """Export all Files.com user accounts."""
        users = self._get_paginated("/users")
        rows = []
        for u in users:
            rows.append({
                "id": u.get("id", ""),
                "username": u.get("username", ""),
                "email": u.get("email", ""),
                "name": u.get("name", ""),
                "admin_group_ids": u.get("admin_group_ids", []),
                "allowed_ips": u.get("allowed_ips", ""),
                "authenticate_until": u.get("authenticate_until", ""),
                "authentication_method": u.get("authentication_method", ""),
                "created_at": u.get("created_at", ""),
                "disabled": u.get("disabled", False),
                "last_login_at": u.get("last_login_at", ""),
                "password_set_at": u.get("password_set_at", ""),
                "require_2fa": u.get("require_2fa", ""),
                "ssl_required": u.get("ssl_required", ""),
            })

        path = self.save_csv("all_users.csv", rows)
        self.record_ipe(
            evidence_file=path,
            endpoint="GET /api/rest/v1/users",
            params={"per_page": 1000},
            row_count=len(rows),
            notes="All Files.com user accounts"
        )
        print(f"  Users: {len(rows)}")

        new_users = [r for r in rows if r.get("created_at", "") >= AUDIT_PERIOD_START and r.get("created_at", "") <= POPULATION_CUTOFF_END]
        new_path = self.save_csv("new_users_audit_period.csv", new_users)
        self.record_ipe(
            evidence_file=new_path,
            endpoint="(filtered from all_users.csv)",
            params={"filter": f"created_at between {AUDIT_PERIOD_START} and {POPULATION_CUTOFF_END}"},
            row_count=len(new_users),
            notes="New Files.com accounts during audit period (ESEC-201)"
        )
        print(f"  New users in audit period: {len(new_users)}")
        return rows

    # ── Site Settings / Password Policy (ESEC-168) ────────────────────

    def collect_site_settings(self):
        """Export Files.com site settings including password configuration."""
        resp = self.session.get(f"{self.base}/site")
        resp.raise_for_status()
        site = resp.json()

        password_settings = {
            "password_min_length": site.get("password_min_length", ""),
            "password_require_letter": site.get("password_require_letter", ""),
            "password_require_mixed": site.get("password_require_mixed", ""),
            "password_require_number": site.get("password_require_number", ""),
            "password_require_special": site.get("password_require_special", ""),
            "password_require_unbreached": site.get("password_require_unbreached", ""),
            "password_validity_days": site.get("password_validity_days", ""),
            "require_2fa": site.get("require_2fa", ""),
            "require_2fa_user_type": site.get("require_2fa_user_type", ""),
            "allowed_2fa_method_sms": site.get("allowed_2fa_method_sms", ""),
            "allowed_2fa_method_totp": site.get("allowed_2fa_method_totp", ""),
            "allowed_2fa_method_u2f": site.get("allowed_2fa_method_u2f", ""),
            "allowed_2fa_method_webauthn": site.get("allowed_2fa_method_webauthn", ""),
            "allowed_2fa_method_yubi": site.get("allowed_2fa_method_yubi", ""),
            "session_expiry": site.get("session_expiry", ""),
            "ssl_required": site.get("ssl_required", ""),
            "tls_disabled": site.get("tls_disabled", ""),
            "sftp_enabled": site.get("sftp_enabled", ""),
            "ftp_enabled": site.get("ftp_enabled", ""),
        }

        path = self.save_json("site_password_settings.json", password_settings)
        csv_rows = [{"setting": k, "value": v} for k, v in password_settings.items()]
        csv_path = self.save_csv("site_password_settings.csv", csv_rows)
        self.record_ipe(
            evidence_file=csv_path,
            endpoint="GET /api/rest/v1/site",
            params={},
            row_count=len(csv_rows),
            notes="Files.com site-level password and security settings (ESEC-168)"
        )
        print(f"  Password settings: {len(csv_rows)} settings captured")
        return password_settings


def run_all(api_key, output_root=None):
    c = FilesComCollector(api_key, output_root)

    print("\n=== Files.com Evidence Collection ===\n")

    print("[1/2] User accounts...")
    c.collect_users()

    print("[2/2] Site settings / password policy...")
    c.collect_site_settings()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    api_key = os.environ.get("FILES_COM_API_KEY")
    if not api_key:
        print("Set FILES_COM_API_KEY environment variable")
        sys.exit(1)
    run_all(api_key)
