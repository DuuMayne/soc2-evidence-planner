import time
import logging
import requests
from collections import deque

log = logging.getLogger(__name__)

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 90  # conservative under the 100/min limit
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3


class JiraClient:
    def __init__(self, base_url, email, api_token, dry_run=False):
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self._request_times = deque()
        self._dry_run_counter = 0

    def _rate_limit(self):
        now = time.time()
        while self._request_times and self._request_times[0] < now - RATE_LIMIT_WINDOW:
            self._request_times.popleft()
        if len(self._request_times) >= RATE_LIMIT_MAX:
            sleep_time = self._request_times[0] + RATE_LIMIT_WINDOW - now + 0.5
            log.info(f"Rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self._request_times.append(time.time())

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        for attempt in range(MAX_RETRIES):
            self._rate_limit()
            try:
                resp = self.session.request(method, url, **kwargs)
            except requests.ConnectionError as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    log.warning(f"Connection error, retrying in {wait}s: {e}")
                    time.sleep(wait)
                    continue
                raise

            if resp.status_code not in RETRY_STATUSES:
                return resp

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 ** (attempt + 2)))
                log.warning(f"429 rate limited, sleeping {retry_after}s")
                time.sleep(retry_after)
            else:
                wait = 2 ** (attempt + 1)
                log.warning(f"HTTP {resp.status_code}, retrying in {wait}s")
                time.sleep(wait)

        return resp

    def _check_response(self, resp, context=""):
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            msg = f"Jira API error {resp.status_code} ({context}): {detail}"
            log.error(msg)
            raise JiraAPIError(resp.status_code, detail, context)

    # ── Issue Operations ─────────────────────────────────────────────

    def create_issue(self, fields):
        if self.dry_run:
            self._dry_run_counter += 1
            key = f"DRY-{self._dry_run_counter}"
            log.info(f"[DRY RUN] Would create issue: {fields.get('summary', 'unknown')} → {key}")
            return {"key": key, "id": str(self._dry_run_counter)}
        resp = self._request("POST", "/rest/api/3/issue", json={"fields": fields})
        self._check_response(resp, f"create issue: {fields.get('summary', '')[:60]}")
        return resp.json()

    def bulk_create_issues(self, issues_fields):
        if self.dry_run:
            results = []
            for fields in issues_fields:
                results.append(self.create_issue(fields))
            return results
        payload = {"issueUpdates": [{"fields": f} for f in issues_fields]}
        resp = self._request("POST", "/rest/api/3/issue/bulk", json=payload)
        self._check_response(resp, "bulk create issues")
        data = resp.json()
        created = data.get("issues", [])
        errors = data.get("errors", [])
        if errors:
            log.warning(f"Bulk create had {len(errors)} errors: {errors}")
        return created, errors

    def get_issue(self, key, fields=None):
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        resp = self._request("GET", f"/rest/api/3/issue/{key}", params=params)
        self._check_response(resp, f"get issue {key}")
        return resp.json()

    def update_issue(self, key, fields):
        if self.dry_run:
            log.info(f"[DRY RUN] Would update {key}: {list(fields.keys())}")
            return
        resp = self._request("PUT", f"/rest/api/3/issue/{key}", json={"fields": fields})
        self._check_response(resp, f"update issue {key}")

    def move_issue(self, key, target_project_key):
        """Move an issue to a different project."""
        if self.dry_run:
            log.info(f"[DRY RUN] Would move {key} to project {target_project_key}")
            return {"key": f"{target_project_key}-DRY"}
        resp = self._request("PUT", f"/rest/api/3/issue/{key}", json={
            "fields": {"project": {"key": target_project_key}}
        })
        self._check_response(resp, f"move issue {key} to {target_project_key}")
        updated = self.get_issue(key, fields=["project", "summary"])
        return updated

    def search_issues(self, jql, fields=None, max_results=50):
        params = {
            "jql": jql,
            "maxResults": max_results,
        }
        if fields:
            fields_str = fields if isinstance(fields, str) else ",".join(fields)
            params["fields"] = fields_str
        resp = self._request("GET", "/rest/api/3/search/jql", params=params)
        self._check_response(resp, f"search: {jql[:80]}")
        return resp.json()

    def search_issues_all(self, jql, fields=None):
        """Paginate through all results for a JQL query.
        Supports both cursor-based (nextPageToken/isLast) and offset-based pagination."""
        all_issues = []
        page_size = 100
        fields_str = None
        if fields:
            fields_str = fields if isinstance(fields, str) else ",".join(fields)

        next_page_token = None
        while True:
            params = {
                "jql": jql,
                "maxResults": page_size,
            }
            if fields_str:
                params["fields"] = fields_str
            if next_page_token:
                params["nextPageToken"] = next_page_token

            resp = self._request("GET", "/rest/api/3/search/jql", params=params)
            self._check_response(resp, f"search all: {jql[:80]}")
            data = resp.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            if data.get("nextPageToken") and not data.get("isLast", True):
                next_page_token = data["nextPageToken"]
            elif data.get("total") is not None:
                start_at = data.get("startAt", 0)
                if start_at + len(issues) >= data["total"]:
                    break
                next_page_token = None
                params["startAt"] = start_at + page_size
            else:
                break
        return all_issues

    def get_issue_children(self, parent_key):
        """Get all child issues (subtasks or issues linked to parent via parent field)."""
        jql = f'parent = "{parent_key}" ORDER BY key ASC'
        return self.search_issues_all(jql, fields="summary,status,issuetype,subtasks,parent")

    # ── Attachments ───────────────────────────────────────────────────

    def add_attachment(self, issue_key, filepath):
        import os as _os
        if self.dry_run:
            log.info(f"[DRY RUN] Would attach {filepath} to {issue_key}")
            return {"filename": _os.path.basename(filepath)}
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"
        headers = {
            "X-Atlassian-Token": "no-check",
            "Content-Type": None,
        }
        with open(filepath, "rb") as f:
            self._rate_limit()
            resp = self.session.post(
                url,
                headers=headers,
                files={"file": (_os.path.basename(filepath), f)},
            )
        self._check_response(resp, f"attach {_os.path.basename(filepath)} to {issue_key}")
        return resp.json()

    def add_comment(self, issue_key, body_adf):
        if self.dry_run:
            log.info(f"[DRY RUN] Would comment on {issue_key}")
            return {"id": "dry-comment"}
        resp = self._request("POST", f"/rest/api/3/issue/{issue_key}/comment",
                             json={"body": body_adf})
        self._check_response(resp, f"comment on {issue_key}")
        return resp.json()

    # ── Issue Links ──────────────────────────────────────────────────

    def create_issue_link(self, link_type, inward_key, outward_key):
        if self.dry_run:
            log.info(f"[DRY RUN] Would link {inward_key} --{link_type}--> {outward_key}")
            return
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        }
        resp = self._request("POST", "/rest/api/3/issueLink", json=payload)
        self._check_response(resp, f"link {inward_key} → {outward_key}")

    # ── Filters ──────────────────────────────────────────────────────

    def create_filter(self, name, jql, description="", share_project_id=None):
        if self.dry_run:
            self._dry_run_counter += 1
            log.info(f"[DRY RUN] Would create filter: {name}")
            return {"id": str(self._dry_run_counter), "name": name}
        payload = {
            "name": name,
            "jql": jql,
            "description": description,
        }
        if share_project_id:
            payload["sharePermissions"] = [
                {"type": "project", "project": {"id": str(share_project_id)}}
            ]
        resp = self._request("POST", "/rest/api/3/filter", json=payload)
        self._check_response(resp, f"create filter: {name}")
        return resp.json()

    def get_my_filters(self):
        resp = self._request("GET", "/rest/api/3/filter/my")
        self._check_response(resp, "get my filters")
        return resp.json()

    # ── Dashboard ────────────────────────────────────────────────────

    def create_dashboard(self, name, description="", share_project_id=None):
        if self.dry_run:
            self._dry_run_counter += 1
            log.info(f"[DRY RUN] Would create dashboard: {name}")
            return {"id": str(self._dry_run_counter), "name": name}
        payload = {
            "name": name,
            "description": description,
        }
        if share_project_id:
            payload["sharePermissions"] = [
                {"type": "project", "project": {"id": str(share_project_id)}}
            ]
        resp = self._request("POST", "/rest/api/3/dashboard", json=payload)
        self._check_response(resp, f"create dashboard: {name}")
        return resp.json()

    def add_dashboard_gadget(self, dashboard_id, module_key, title="", position=None, color="blue"):
        if self.dry_run:
            log.info(f"[DRY RUN] Would add gadget {module_key} to dashboard {dashboard_id}")
            return {"id": "dry-gadget"}
        payload = {"moduleKey": module_key}
        if title:
            payload["title"] = title
        if position:
            payload["position"] = position
        if color:
            payload["color"] = color
        resp = self._request(
            "POST",
            f"/rest/api/3/dashboard/{dashboard_id}/gadget",
            json=payload,
        )
        self._check_response(resp, f"add gadget {module_key}")
        return resp.json()

    # ── Discovery ────────────────────────────────────────────────────

    def get_project(self, key):
        resp = self._request("GET", f"/rest/api/3/project/{key}")
        self._check_response(resp, f"get project {key}")
        return resp.json()

    def get_issue_types_for_project(self, project_key):
        resp = self._request("GET", f"/rest/api/3/issue/createmeta/{project_key}/issuetypes")
        self._check_response(resp, f"get issue types for {project_key}")
        return resp.json().get("issueTypes", resp.json().get("values", []))

    def get_myself(self):
        resp = self._request("GET", "/rest/api/3/myself")
        self._check_response(resp, "get myself")
        return resp.json()

    def get_fields(self):
        resp = self._request("GET", "/rest/api/3/field")
        self._check_response(resp, "get fields")
        return resp.json()


class JiraAPIError(Exception):
    def __init__(self, status_code, detail, context=""):
        self.status_code = status_code
        self.detail = detail
        self.context = context
        super().__init__(f"HTTP {status_code} ({context}): {detail}")
