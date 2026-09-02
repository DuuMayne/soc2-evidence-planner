"""Re-create issues from one Jira project into another, preserving hierarchy.

Jira Cloud does not support moving issues between projects with different
types (classic → next-gen) via API. This module copies the full epic tree
into the target project, mapping issue types appropriately.
"""

import logging

log = logging.getLogger(__name__)

ISSUE_TYPE_MAP = {
    "Epic": "Workstream",
    "Task": "Task",
    "Sub-task": "Sub-task",
    "Story": "Task",
    "Bug": "Task",
}


def discover_epic_tree(client, epic_key):
    log.info(f"Discovering issue tree under {epic_key}...")

    epic = client.get_issue(epic_key, fields=[
        "summary", "status", "issuetype", "description", "labels", "assignee", "duedate",
    ])
    log.info(f"Epic: {epic_key} — {epic['fields']['summary']}")

    stories = client.get_issue_children(epic_key)
    log.info(f"Found {len(stories)} direct children of {epic_key}")

    tree = {"epic": epic, "children": []}
    for story in stories:
        story_full = client.get_issue(story["key"], fields=[
            "summary", "status", "issuetype", "description", "labels", "assignee", "duedate",
        ])
        subtasks = client.get_issue_children(story["key"])
        subtasks_full = []
        for sub in subtasks:
            sub_full = client.get_issue(sub["key"], fields=[
                "summary", "status", "issuetype", "description", "labels", "assignee", "duedate",
            ])
            subtasks_full.append(sub_full)
        tree["children"].append({
            "issue": story_full,
            "subtasks": subtasks_full,
        })

    total = 1 + len(stories) + sum(len(c["subtasks"]) for c in tree["children"])
    log.info(f"Total issues in tree: {total}")
    return tree


def preview_migration(tree, target_project, target_types):
    epic = tree["epic"]
    ef = epic["fields"]
    source_type = ef["issuetype"]["name"]
    mapped_type = target_types.get(ISSUE_TYPE_MAP.get(source_type, source_type))

    print(f"\nMigration Preview: {epic['key']} → {target_project}")
    print(f"{'=' * 70}")
    print(f"Epic: {epic['key']} ({source_type} → {ISSUE_TYPE_MAP.get(source_type, '?')})")
    print(f"  {ef['summary']}")

    for child in tree["children"]:
        issue = child["issue"]
        cf = issue["fields"]
        src_type = cf["issuetype"]["name"]
        dst_type = ISSUE_TYPE_MAP.get(src_type, src_type)
        print(f"  {issue['key']}: [{src_type} → {dst_type}] {cf['summary']}")
        for sub in child["subtasks"]:
            sf = sub["fields"]
            st = sf["issuetype"]["name"]
            dt = ISSUE_TYPE_MAP.get(st, st)
            print(f"    {sub['key']}: [{st} → {dt}] {sf['summary']}")

    total = 1 + len(tree["children"]) + sum(len(c["subtasks"]) for c in tree["children"])
    print(f"\nTotal issues to re-create: {total}")
    if mapped_type:
        print(f"Epic type mapping: {source_type} → {ISSUE_TYPE_MAP.get(source_type)} (ID: {mapped_type})")
    print()
    return total


def _get_target_type_map(client, target_project):
    """Build {type_name: type_id} for the target project."""
    types = client.get_issue_types_for_project(target_project)
    return {t["name"]: t["id"] for t in types}


def _build_create_fields(issue, target_project, target_type_id, parent_key=None):
    """Build the fields dict to create an issue in the target project."""
    f = issue["fields"]
    fields = {
        "project": {"key": target_project},
        "issuetype": {"id": target_type_id},
        "summary": f["summary"],
    }

    if f.get("description"):
        fields["description"] = f["description"]

    if f.get("labels"):
        fields["labels"] = f["labels"]

    if f.get("assignee"):
        fields["assignee"] = {"accountId": f["assignee"]["accountId"]}

    if f.get("duedate"):
        fields["duedate"] = f["duedate"]

    if parent_key:
        fields["parent"] = {"key": parent_key}

    return fields


def migrate_epic_tree(client, epic_key, target_project, state):
    tree = discover_epic_tree(client, epic_key)
    target_types = _get_target_type_map(client, target_project)

    total = preview_migration(tree, target_project, target_types)

    created = 0
    failed = 0
    key_map = {}

    # 1. Create the epic (as Workstream in ESEC)
    epic = tree["epic"]
    ef = epic["fields"]
    epic_src_type = ef["issuetype"]["name"]
    epic_dst_type_name = ISSUE_TYPE_MAP.get(epic_src_type, epic_src_type)
    epic_dst_type_id = target_types.get(epic_dst_type_name)

    if not epic_dst_type_id:
        log.error(f"No matching type '{epic_dst_type_name}' in {target_project}. Available: {list(target_types.keys())}")
        return 0, key_map

    if state.is_issue_moved(epic_key):
        new_epic_key = state._data["moved_issues"][epic_key]
        log.info(f"Epic already migrated: {epic_key} → {new_epic_key}")
        key_map[epic_key] = new_epic_key
        created += 1
    else:
        fields = _build_create_fields(epic, target_project, epic_dst_type_id)
        try:
            result = client.create_issue(fields)
            new_epic_key = result["key"]
            key_map[epic_key] = new_epic_key
            state.record_issue_moved(epic_key, new_epic_key)
            created += 1
            log.info(f"Created {epic_dst_type_name}: {epic_key} → {new_epic_key}")
        except Exception as e:
            log.error(f"Failed to create epic: {e}")
            return 0, key_map

    # 2. Create stories (as Tasks under the Workstream)
    story_dst_type_id = target_types.get("Task")
    if not story_dst_type_id:
        log.error(f"No 'Task' type in {target_project}")
        return created, key_map

    for child in tree["children"]:
        story = child["issue"]
        story_key = story["key"]

        if state.is_issue_moved(story_key):
            new_story_key = state._data["moved_issues"][story_key]
            key_map[story_key] = new_story_key
            created += 1
        else:
            fields = _build_create_fields(story, target_project, story_dst_type_id, parent_key=new_epic_key)
            try:
                result = client.create_issue(fields)
                new_story_key = result["key"]
                key_map[story_key] = new_story_key
                state.record_issue_moved(story_key, new_story_key)
                created += 1
                log.info(f"Created Task: {story_key} → {new_story_key}")
            except Exception as e:
                log.error(f"Failed to create story {story_key}: {e}")
                failed += 1
                continue

        # 3. Create subtasks
        subtask_dst_type_id = target_types.get("Sub-task")
        if not subtask_dst_type_id:
            log.warning(f"No 'Sub-task' type in {target_project}, skipping subtasks")
            continue

        for sub in child["subtasks"]:
            sub_key = sub["key"]
            if state.is_issue_moved(sub_key):
                key_map[sub_key] = state._data["moved_issues"][sub_key]
                created += 1
                continue

            fields = _build_create_fields(sub, target_project, subtask_dst_type_id, parent_key=new_story_key)
            try:
                result = client.create_issue(fields)
                new_sub_key = result["key"]
                key_map[sub_key] = new_sub_key
                state.record_issue_moved(sub_key, new_sub_key)
                created += 1
                log.info(f"Created Sub-task: {sub_key} → {new_sub_key}")
            except Exception as e:
                log.error(f"Failed to create subtask {sub_key}: {e}")
                failed += 1

    log.info(f"Migration complete: {created}/{total} issues created in {target_project} ({failed} failed)")
    return created, key_map
