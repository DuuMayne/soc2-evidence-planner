"""Create saved JQL filters in Jira."""

import logging
from .models import FilterSpec

log = logging.getLogger(__name__)


def build_filter_specs(config, team_names=None, evidence_types=None):
    audit = config.get("audit", {})
    project_key = config["jira"]["project_key"]
    year = audit.get("year", "")
    year_label = f"{year}-audit"
    dl1_label = audit.get("deadline_1", {}).get("label", "")

    filters = [
        FilterSpec(
            name=f"SOC 2 {year} — My Open Tasks",
            jql=(
                f'project = {project_key} AND assignee = currentUser() '
                f'AND status != Done AND labels = "{year_label}" '
                f'ORDER BY priority DESC, duedate ASC'
            ),
            description="Your assigned SOC 2 evidence tasks, sorted by priority and due date.",
        ),
        FilterSpec(
            name=f"SOC 2 {year} — Deadline At Risk",
            jql=(
                f'project = {project_key} AND labels IN ("{dl1_label}", "{year_label}") '
                f'AND status NOT IN ("QA Approved", "Submitted", "Done") '
                f'ORDER BY priority DESC'
            ),
            description="Tasks due at deadline 1 that are not yet approved or submitted.",
        ),
        FilterSpec(
            name=f"SOC 2 {year} — Blocked Items",
            jql=(
                f'project = {project_key} AND labels = "blocked" '
                f'AND labels = "{year_label}" AND status != Done '
                f'ORDER BY priority DESC, created ASC'
            ),
            description="Blocked evidence tasks (usually sample evidence awaiting auditor selection).",
        ),
        FilterSpec(
            name=f"SOC 2 {year} — QA Queue",
            jql=(
                f'project = {project_key} AND status = "QA Review" '
                f'AND labels = "{year_label}" '
                f'ORDER BY duedate ASC'
            ),
            description="Evidence ready for QA review before submission.",
        ),
        FilterSpec(
            name=f"SOC 2 {year} — Completed This Week",
            jql=(
                f'project = {project_key} AND status = Done '
                f'AND labels = "{year_label}" AND resolved >= startOfWeek() '
                f'ORDER BY resolved DESC'
            ),
            description="Evidence tasks completed this week.",
        ),
    ]

    if team_names:
        for team in team_names:
            team_label = f"owner-{team}"
            filters.append(FilterSpec(
                name=f"SOC 2 {year} — Team: {team.replace('-', ' ').title()}",
                jql=(
                    f'project = {project_key} AND labels = "{team_label}" '
                    f'AND labels = "{year_label}" AND status != Done '
                    f'ORDER BY duedate ASC, priority DESC'
                ),
                description=f"Open SOC 2 tasks assigned to the {team} team.",
            ))

    if evidence_types:
        for etype in evidence_types:
            filters.append(FilterSpec(
                name=f"SOC 2 {year} — Type: {etype.title()}",
                jql=(
                    f'project = {project_key} AND labels = "evidence-{etype}" '
                    f'AND labels = "{year_label}" '
                    f'ORDER BY duedate ASC'
                ),
                description=f"All SOC 2 {etype} evidence tasks.",
            ))

    return filters


def create_filters(client, filter_specs, config, state):
    project = client.get_project(config["jira"]["project_key"])
    project_id = project["id"]

    existing = {}
    try:
        my_filters = client.get_my_filters()
        existing = {f["name"]: f["id"] for f in my_filters}
    except Exception:
        log.warning("Could not fetch existing filters, will attempt to create all")

    created = 0
    skipped = 0

    for spec in filter_specs:
        if state.is_filter_created(spec.name):
            skipped += 1
            continue

        if spec.name in existing:
            state.record_filter(spec.name, existing[spec.name])
            skipped += 1
            log.info(f"Filter already exists: {spec.name}")
            continue

        try:
            result = client.create_filter(
                spec.name, spec.jql, spec.description, share_project_id=project_id,
            )
            state.record_filter(spec.name, result["id"])
            created += 1
            log.info(f"Created filter: {spec.name} (ID: {result['id']})")
        except Exception as e:
            log.error(f"Failed to create filter '{spec.name}': {e}")

    log.info(f"Filters: {created} created, {skipped} skipped")
