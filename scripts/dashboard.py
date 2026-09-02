"""Create Jira dashboard with gadgets for SOC 2 evidence tracking."""

import logging

log = logging.getLogger(__name__)


GADGET_SPECS = [
    {
        "key": "pie-status",
        "module_key": "com.atlassian.jira.gadgets:pie-chart-gadget",
        "title": "Tasks by Status",
        "position": {"column": 0, "row": 0},
    },
    {
        "key": "bar-assignee",
        "module_key": "com.atlassian.jira.gadgets:two-dimensional-stats-gadget",
        "title": "Tasks by Assignee & Status",
        "position": {"column": 0, "row": 1},
    },
    {
        "key": "table-blocked",
        "module_key": "com.atlassian.jira.gadgets:filter-results-gadget",
        "title": "Blocked Items",
        "position": {"column": 1, "row": 0},
    },
    {
        "key": "table-due-this-week",
        "module_key": "com.atlassian.jira.gadgets:filter-results-gadget",
        "title": "Due This Week",
        "position": {"column": 1, "row": 1},
    },
    {
        "key": "activity",
        "module_key": "com.atlassian.streams.streams-jira-plugin:activitystream-gadget",
        "title": "Recent Activity",
        "position": {"column": 1, "row": 2},
    },
]


def create_dashboard_with_gadgets(client, config, state):
    audit = config.get("audit", {})
    year = audit.get("year", "")
    project_key = config["jira"]["project_key"]
    dashboard_name = f"SOC 2 {year} Evidence Tracker"

    dashboard_id = state.get_dashboard_id()
    if not dashboard_id:
        try:
            project = client.get_project(project_key)
            result = client.create_dashboard(
                dashboard_name,
                description=f"SOC 2 Type II {year} evidence collection tracking dashboard",
                share_project_id=project["id"],
            )
            dashboard_id = result["id"]
            state.record_dashboard(dashboard_id)
            log.info(f"Created dashboard: {dashboard_name} (ID: {dashboard_id})")
        except Exception as e:
            log.error(f"Failed to create dashboard: {e}")
            return None
    else:
        log.info(f"Dashboard already exists (ID: {dashboard_id})")

    for spec in GADGET_SPECS:
        if state.is_gadget_added(spec["key"]):
            continue
        try:
            client.add_dashboard_gadget(
                dashboard_id,
                spec["module_key"],
                title=spec["title"],
                position=spec["position"],
            )
            state.record_gadget(spec["key"])
            log.info(f"Added gadget: {spec['title']}")
        except Exception as e:
            log.warning(f"Failed to add gadget {spec['title']}: {e}")

    print_manual_config_instructions(config, state)
    return dashboard_id


def print_manual_config_instructions(config, state):
    audit = config.get("audit", {})
    year = audit.get("year", "")
    filter_ids = state.get_all_filter_ids()

    print("\n" + "=" * 60)
    print("DASHBOARD GADGET CONFIGURATION (manual steps)")
    print("=" * 60)
    print()
    print("The Jira API cannot configure gadget data sources.")
    print("Open the dashboard and configure each gadget:")
    print()
    print("1. Tasks by Status (pie chart):")
    print(f"   → Set saved filter to: SOC 2 {year} — My Open Tasks")
    print(f"   → Stat type: Status")
    print()
    print("2. Tasks by Assignee & Status:")
    print(f"   → Set project to: {config['jira']['project_key']}")
    print(f"   → X-axis: Assignee, Y-axis: Status")
    print()
    print("3. Blocked Items (filter results):")
    if filter_ids.get(f"SOC 2 {year} — Blocked Items"):
        print(f"   → Filter ID: {filter_ids[f'SOC 2 {year} — Blocked Items']}")
    print(f"   → Set saved filter to: SOC 2 {year} — Blocked Items")
    print()
    print("4. Due This Week (filter results):")
    print(f"   → Create a quick filter or use JQL:")
    print(f"   → project = {config['jira']['project_key']} AND duedate <= endOfWeek() AND status != Done")
    print()
    print("5. Recent Activity (activity stream):")
    print(f"   → Set project to: {config['jira']['project_key']}")
    print()
    print("Estimated time: ~5 minutes")
    print("=" * 60 + "\n")
