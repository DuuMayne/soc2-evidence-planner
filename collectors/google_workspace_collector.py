"""
Google Workspace evidence collector — pulls password policies, user listings,
and email security settings via the Admin SDK.

Requires: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
Requires: A service account with domain-wide delegation and Admin SDK API enabled.
Set GOOGLE_SERVICE_ACCOUNT_FILE to the path of the service account JSON key.
Set GOOGLE_ADMIN_EMAIL to the admin email to impersonate.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import EvidenceCollector

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.domain.readonly",
]


class GoogleWorkspaceCollector(EvidenceCollector):
    def __init__(self, service_account_file, admin_email, customer_id="my_customer", output_root=None):
        super().__init__("google_workspace", output_root)
        if not HAS_GOOGLE:
            raise ImportError("Install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        self.creds = creds.with_subject(admin_email)
        self.admin_email = admin_email
        self.customer_id = customer_id
        self.directory = build("admin", "directory_v1", credentials=self.creds)

    # ── Password Policy Settings (ESEC-167) ──────────────────────────

    def collect_password_settings(self):
        """
        Google Workspace password settings are not directly available via API.
        We document the configured settings via domain info and generate a
        template for manual screenshot capture.
        """
        try:
            domains = self.directory.domains().list(customer=self.customer_id).execute()
            domain_rows = []
            for d in domains.get("domains", []):
                domain_rows.append({
                    "domain_name": d.get("domainName", ""),
                    "verified": d.get("verified", ""),
                    "is_primary": d.get("isPrimary", ""),
                    "creation_time": d.get("creationTime", ""),
                })
            path = self.save_csv("workspace_domains.csv", domain_rows)
            self.record_ipe(
                evidence_file=path,
                endpoint="GET admin.directory.domains.list",
                params={"customer": self.customer_id},
                row_count=len(domain_rows),
                notes="Google Workspace domains — password settings must be captured via Admin Console screenshot (API does not expose password complexity rules)"
            )
            print(f"  Domains: {len(domain_rows)}")
        except Exception as e:
            print(f"  Domains: error — {e}")

        instructions = (
            "GOOGLE WORKSPACE PASSWORD SETTINGS — MANUAL CAPTURE REQUIRED\n"
            "=============================================================\n\n"
            "The Google Admin SDK does not expose password complexity settings via API.\n"
            "Navigate to: admin.google.com → Security → Authentication → Password management\n\n"
            "Capture screenshots of:\n"
            "1. Password length requirements\n"
            "2. Password strength enforcement\n"
            "3. Password expiration settings\n"
            "4. Allow password reuse setting\n\n"
            "Save screenshots in the same folder as this file.\n"
        )
        self.save_text("password_settings_instructions.txt", instructions)

    # ── All Users (supports access populations) ──────────────────────

    def collect_all_users(self):
        """Export all active Google Workspace users."""
        all_users = []
        page_token = None
        while True:
            results = self.directory.users().list(
                customer=self.customer_id,
                maxResults=500,
                orderBy="email",
                pageToken=page_token,
            ).execute()
            users = results.get("users", [])
            for u in users:
                all_users.append({
                    "user_id": u.get("id", ""),
                    "email": u.get("primaryEmail", ""),
                    "name": u.get("name", {}).get("fullName", ""),
                    "org_unit_path": u.get("orgUnitPath", ""),
                    "is_admin": u.get("isAdmin", False),
                    "is_delegated_admin": u.get("isDelegatedAdmin", False),
                    "is_suspended": u.get("suspended", False),
                    "is_archived": u.get("archived", False),
                    "creation_time": u.get("creationTime", ""),
                    "last_login_time": u.get("lastLoginTime", ""),
                    "is_2sv_enrolled": u.get("isEnrolledIn2Sv", False),
                    "is_2sv_enforced": u.get("isEnforcedIn2Sv", False),
                })
            page_token = results.get("nextPageToken")
            if not page_token:
                break

        path = self.save_csv("all_workspace_users.csv", all_users)
        self.record_ipe(
            evidence_file=path,
            endpoint="admin.directory.users.list",
            params={"customer": self.customer_id, "orderBy": "email"},
            row_count=len(all_users),
            pagination=f"Paginated at 500/page, collected {len(all_users)} total",
            notes="All Google Workspace users with admin/2FA status"
        )
        print(f"  Workspace users: {len(all_users)}")

        admins = [u for u in all_users if u["is_admin"] or u["is_delegated_admin"]]
        admin_path = self.save_csv("workspace_admins.csv", admins)
        self.record_ipe(
            evidence_file=admin_path,
            endpoint="(filtered from all_workspace_users.csv)",
            params={"filter": "is_admin=True OR is_delegated_admin=True"},
            row_count=len(admins),
            notes="Google Workspace admin users — filtered from full user export"
        )
        print(f"  Workspace admins: {len(admins)}")
        return all_users

    # ── Groups ────────────────────────────────────────────────────────

    def collect_groups(self):
        """Export all Google Groups for access review evidence."""
        all_groups = []
        page_token = None
        while True:
            results = self.directory.groups().list(
                customer=self.customer_id,
                maxResults=200,
                pageToken=page_token,
            ).execute()
            groups = results.get("groups", [])
            for g in groups:
                all_groups.append({
                    "group_id": g.get("id", ""),
                    "email": g.get("email", ""),
                    "name": g.get("name", ""),
                    "description": g.get("description", ""),
                    "direct_members_count": g.get("directMembersCount", ""),
                    "admin_created": g.get("adminCreated", ""),
                })
            page_token = results.get("nextPageToken")
            if not page_token:
                break

        path = self.save_csv("workspace_groups.csv", all_groups)
        self.record_ipe(
            evidence_file=path,
            endpoint="admin.directory.groups.list",
            params={"customer": self.customer_id},
            row_count=len(all_groups),
            notes="Google Workspace groups — access review support"
        )
        print(f"  Groups: {len(all_groups)}")
        return all_groups


def run_all(service_account_file, admin_email, customer_id="my_customer", output_root=None):
    c = GoogleWorkspaceCollector(service_account_file, admin_email, customer_id, output_root)

    print("\n=== Google Workspace Evidence Collection ===\n")

    print("[1/3] Password settings...")
    c.collect_password_settings()

    print("[2/3] All users...")
    c.collect_all_users()

    print("[3/3] Groups...")
    c.collect_groups()

    c.save_ipe()
    s = c.summary()
    print(f"\nDone. {len(s['files_generated'])} files in {s['output_dir']}")
    return s


if __name__ == "__main__":
    sa_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    admin = os.environ.get("GOOGLE_ADMIN_EMAIL")
    customer = os.environ.get("GOOGLE_CUSTOMER_ID", "my_customer")
    if not sa_file or not admin:
        print("Set GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_ADMIN_EMAIL environment variables")
        sys.exit(1)
    run_all(sa_file, admin, customer)
