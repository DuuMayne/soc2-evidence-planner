"""CLI entry point for SOC 2 Jira automation toolkit."""

import argparse
import logging
import sys

from .config import load_config, get_team_member_map
from .jira_client import JiraClient
from .state import RunState
from .csv_parser import parse_csv
from .labels import get_all_unique_labels
from .tickets import build_story_specs, build_task_specs, create_stories, create_tasks, create_issue_links
from .filters import build_filter_specs, create_filters
from .dashboard import create_dashboard_with_gadgets
from .migrate import discover_epic_tree, preview_migration, migrate_epic_tree, _get_target_type_map


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_client(config, dry_run=False):
    jira = config["jira"]
    return JiraClient(jira["url"], jira["email"], jira["api_token"], dry_run=dry_run)


def cmd_validate(args):
    """Parse CSV + config and report what would be created."""
    config = load_config(args.config, require_credentials=False)
    requests = parse_csv(args.csv, config)

    stories = build_story_specs(requests, config)
    tasks = build_task_specs(requests, config)
    labels = get_all_unique_labels(requests, config)
    teams = sorted(set(r.owner_team for r in requests if r.owner_team != "unassigned"))
    evidence_types = sorted(set(r.evidence_type for r in requests))
    filters = build_filter_specs(config, teams, evidence_types)

    print(f"\n{'=' * 50}")
    print(f"SOC 2 Evidence Collection — Validation Report")
    print(f"{'=' * 50}")
    print(f"\nCSV: {args.csv}")
    print(f"Config: {args.config}")
    print(f"\nArtifacts to create:")
    print(f"  Epic: {config['jira']['epic_key']} (existing)")
    print(f"  Stories: {len(stories)}")
    print(f"  Tasks: {len(tasks)}")
    print(f"  Unique labels: {len(labels)}")
    print(f"  Filters: {len(filters)}")
    print(f"  Dashboard: 1 (with {5} gadgets)")

    print(f"\nStories ({len(stories)}):")
    for s in stories:
        print(f"  {s.control_id} — {s.summary} ({len(s.tasks)} tasks)")

    print(f"\nPriority breakdown:")
    for p in ("P1", "P2", "P3"):
        count = sum(1 for t in tasks if t.priority == p)
        print(f"  {p}: {count} tasks")

    print(f"\nEvidence types:")
    for et in evidence_types:
        count = sum(1 for t in tasks if t.evidence_type == et)
        print(f"  {et}: {count}")

    print(f"\nTeams:")
    for team in teams:
        count = sum(1 for r in requests if r.owner_team == team)
        print(f"  {team}: {count} tasks")

    unassigned = sum(1 for r in requests if r.owner_team == "unassigned")
    if unassigned:
        print(f"  [unassigned]: {unassigned} tasks")

    unmapped_owners = set()
    member_map = get_team_member_map(config)
    for r in requests:
        if r.owner_name.lower() not in member_map and r.owner_name != "Unassigned":
            unmapped_owners.add(r.owner_name)
    if unmapped_owners:
        print(f"\n⚠ Owners not mapped to Jira accounts ({len(unmapped_owners)}):")
        for name in sorted(unmapped_owners):
            print(f"  - {name}")
        print("  These tasks will be created without an assignee.")

    print(f"\nLabels ({len(labels)}):")
    for label in labels:
        print(f"  {label}")

    print(f"\nFilters ({len(filters)}):")
    for f in filters:
        print(f"  {f.name}")

    print()


def cmd_create(args):
    """Full creation: tickets + filters + dashboard."""
    config = load_config(args.config)
    client = build_client(config, dry_run=args.dry_run)
    state = RunState(args.state_dir)
    state.load()
    state.set_config_hash(args.config)

    me = client.get_myself()
    print(f"Authenticated as: {me.get('displayName', me.get('emailAddress', 'unknown'))}")

    epic = client.get_issue(config["jira"]["epic_key"], fields=["summary"])
    print(f"Epic: {epic['key']} — {epic['fields']['summary']}\n")

    requests = parse_csv(args.csv, config)
    stories = build_story_specs(requests, config)
    task_specs = build_task_specs(requests, config)

    print(f"\nCreating {len(stories)} stories...")
    stories = create_stories(client, stories, config, state)

    print(f"Creating {len(task_specs)} tasks...")
    task_specs = create_tasks(client, task_specs, stories, config, state)

    print("Creating issue links...")
    create_issue_links(client, task_specs, state)

    teams = sorted(set(r.owner_team for r in requests if r.owner_team != "unassigned"))
    evidence_types = sorted(set(r.evidence_type for r in requests))
    filter_specs = build_filter_specs(config, teams, evidence_types)

    print(f"\nCreating {len(filter_specs)} filters...")
    create_filters(client, filter_specs, config, state)

    print("\nCreating dashboard...")
    create_dashboard_with_gadgets(client, config, state)

    summary = state.summary()
    print(f"\n{'=' * 50}")
    print(f"Creation complete!")
    print(f"  Stories: {summary['stories']}")
    print(f"  Tasks: {summary['tasks']}")
    print(f"  Links: {summary['links']}")
    print(f"  Filters: {summary['filters']}")
    print(f"  Dashboard: {'yes' if summary['dashboard'] else 'no'}")
    print(f"{'=' * 50}\n")


def cmd_tickets(args):
    """Create only stories and tasks."""
    config = load_config(args.config)
    client = build_client(config, dry_run=args.dry_run)
    state = RunState(args.state_dir)
    state.load()
    state.set_config_hash(args.config)

    me = client.get_myself()
    print(f"Authenticated as: {me.get('displayName', me.get('emailAddress', 'unknown'))}")

    requests = parse_csv(args.csv, config)
    stories = build_story_specs(requests, config)
    task_specs = build_task_specs(requests, config)

    stories = create_stories(client, stories, config, state)
    task_specs = create_tasks(client, task_specs, stories, config, state)
    create_issue_links(client, task_specs, state)

    summary = state.summary()
    print(f"\nTickets: {summary['stories']} stories, {summary['tasks']} tasks, {summary['links']} links")


def cmd_filters(args):
    """Create only filters."""
    config = load_config(args.config)
    client = build_client(config, dry_run=args.dry_run)
    state = RunState(args.state_dir)
    state.load()

    requests = parse_csv(args.csv, config)
    teams = sorted(set(r.owner_team for r in requests if r.owner_team != "unassigned"))
    evidence_types = sorted(set(r.evidence_type for r in requests))
    filter_specs = build_filter_specs(config, teams, evidence_types)

    create_filters(client, filter_specs, config, state)


def cmd_dashboard(args):
    """Create only dashboard."""
    config = load_config(args.config)
    client = build_client(config, dry_run=args.dry_run)
    state = RunState(args.state_dir)
    state.load()

    create_dashboard_with_gadgets(client, config, state)


def cmd_migrate(args):
    """Re-create an epic and all children in a different project."""
    config = load_config(args.config)
    client = build_client(config, dry_run=args.dry_run)
    state = RunState(args.state_dir)
    state.load()

    source_key = args.source_epic or config["jira"]["epic_key"]
    target_project = args.target_project

    me = client.get_myself()
    print(f"Authenticated as: {me.get('displayName', me.get('emailAddress', 'unknown'))}")

    tree = discover_epic_tree(client, source_key)
    target_types = _get_target_type_map(client, target_project)
    total = preview_migration(tree, target_project, target_types)

    if args.dry_run:
        print("[DRY RUN] No issues will be created.")
        return

    if not args.yes:
        confirm = input(f"\nRe-create {total} issues in {target_project}? [y/N] ")
        if confirm.lower() not in ("y", "yes"):
            print("Aborted.")
            return

    created, key_map = migrate_epic_tree(client, source_key, target_project, state)
    print(f"\nMigration complete: {created}/{total} issues created in {target_project}")
    if key_map:
        epic_new = key_map.get(source_key, "?")
        print(f"New epic: {epic_new}")
        print(f"View at: https://meetearnest.atlassian.net/browse/{epic_new}")


def cmd_status(args):
    """Show current run state."""
    state = RunState(args.state_dir)
    state.load()
    summary = state.summary()

    print(f"\nRun State ({args.state_dir})")
    print(f"{'=' * 40}")
    print(f"Stories created: {summary['stories']}")
    print(f"Tasks created:   {summary['tasks']}")
    print(f"Links created:   {summary['links']}")
    print(f"Filters created: {summary['filters']}")
    print(f"Dashboard:       {'yes' if summary['dashboard'] else 'no'}")
    print(f"Gadgets added:   {summary['gadgets']}")
    print(f"Issues moved:    {summary['moved']}")

    if summary['stories']:
        print(f"\nStories:")
        for cid, key in state.get_all_story_keys().items():
            print(f"  {cid} → {key}")

    if summary['filters']:
        print(f"\nFilters:")
        for name, fid in state.get_all_filter_ids().items():
            print(f"  {name} → ID {fid}")

    print()


def cmd_reset(args):
    """Clear run state."""
    state = RunState(args.state_dir)
    confirm = input("Clear all run state? This cannot be undone. [y/N] ")
    if confirm.lower() in ("y", "yes"):
        state.clear()
        print("State cleared.")
    else:
        print("Aborted.")


def main():
    parser = argparse.ArgumentParser(
        prog="soc2-jira",
        description="SOC 2 Evidence Collection — Jira Automation Toolkit",
    )
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML")
    parser.add_argument("--csv", default=None, help="Path to auditor request CSV")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making API calls")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--state-dir", default="state", help="State directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("validate", help="Validate config and CSV, report what would be created")
    subparsers.add_parser("create", help="Create all Jira artifacts")
    subparsers.add_parser("tickets", help="Create only stories and tasks")
    subparsers.add_parser("filters", help="Create only saved JQL filters")
    subparsers.add_parser("dashboard", help="Create only dashboard and gadgets")

    migrate_parser = subparsers.add_parser("migrate", help="Move epic + children to another project")
    migrate_parser.add_argument("--source-epic", help="Epic key to move (default: from config)")
    migrate_parser.add_argument("--target-project", required=True, help="Target project key")
    migrate_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")

    subparsers.add_parser("status", help="Show current run state")
    subparsers.add_parser("reset", help="Clear run state")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "validate": cmd_validate,
        "create": cmd_create,
        "tickets": cmd_tickets,
        "filters": cmd_filters,
        "dashboard": cmd_dashboard,
        "migrate": cmd_migrate,
        "status": cmd_status,
        "reset": cmd_reset,
    }

    cmd = commands.get(args.command)
    if cmd:
        try:
            cmd(args)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(1)
        except Exception as e:
            logging.getLogger(__name__).error(str(e))
            if args.verbose:
                raise
            sys.exit(1)


if __name__ == "__main__":
    main()
