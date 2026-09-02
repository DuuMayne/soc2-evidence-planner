"""Story and task creation with epic linking and issue linking."""

import logging
from collections import OrderedDict
from .models import StorySpec, TaskSpec
from .labels import compute_story_labels, compute_task_labels
from .templates import render_story_description, render_task_description
from .config import get_team_member_map

log = logging.getLogger(__name__)


def build_story_specs(requests, config):
    """Group evidence requests by control_id, produce one StorySpec per control."""
    grouped = OrderedDict()
    for req in requests:
        if req.control_id not in grouped:
            grouped[req.control_id] = []
        grouped[req.control_id].append(req)

    stories = []
    for control_id, reqs in grouped.items():
        first = reqs[0]
        summary = f"{control_id} - {first.control_name}"
        labels = compute_story_labels(control_id, first.control_family, config)
        description_adf = render_story_description(
            control_id, first.control_name, first.control_description, reqs, config
        )
        stories.append(StorySpec(
            control_id=control_id,
            summary=summary,
            description_adf=description_adf,
            labels=labels,
            tasks=reqs,
        ))

    return stories


def build_task_specs(requests, config):
    """Produce one TaskSpec per evidence request (already split by system)."""
    member_map = get_team_member_map(config)
    audit = config.get("audit", {})
    tasks = []

    for req in requests:
        system = req.systems[0] if req.systems else "N/A"
        summary = f"Req {req.request_number:02d} - {req.evidence_type.title()} - {system} - {req.owner_name}"

        dl = audit.get(f"deadline_{req.deadline_group}", {})
        due_date = dl.get("date", "")

        member_info = member_map.get(req.owner_name.lower(), {})
        assignee_id = member_info.get("account_id")

        labels = compute_task_labels(req, config)
        description_adf = render_task_description(req, config)

        tasks.append(TaskSpec(
            request_number=req.request_number,
            summary=summary,
            description_adf=description_adf,
            labels=labels,
            assignee_account_id=assignee_id,
            due_date=due_date,
            priority=req.priority,
            evidence_type=req.evidence_type,
            system=system,
            parent_story_control_id=req.control_id,
            is_blocked=(req.evidence_type == "sample" or req.deadline_group == 2),
        ))

    return tasks


def _detect_project_style(client, project_key):
    """Detect if project is next-gen (team-managed) or classic (company-managed)."""
    project = client.get_project(project_key)
    style = project.get("style", "classic")
    log.info(f"Project {project_key} style: {style}")
    return style


def _find_issue_type_id(client, project_key, type_name):
    """Find the issue type ID for a given name in the project."""
    issue_types = client.get_issue_types_for_project(project_key)
    for it in issue_types:
        if it["name"].lower() == type_name.lower():
            return it["id"]
    names = [it["name"] for it in issue_types]
    raise ValueError(f"Issue type '{type_name}' not found in {project_key}. Available: {names}")


def create_stories(client, stories, config, state):
    project_key = config["jira"]["project_key"]
    epic_key = config["jira"]["epic_key"]
    style = _detect_project_style(client, project_key)

    issue_type_config = config.get("issue_types", {})
    story_type_name = issue_type_config.get("story", "Story")
    story_type_id = _find_issue_type_id(client, project_key, story_type_name)

    epic_link_field = config.get("custom_fields", {}).get("epic_link")

    created = 0
    skipped = 0

    for story in stories:
        if state.is_story_created(story.control_id):
            story.jira_key = state.get_story_key(story.control_id)
            skipped += 1
            continue

        fields = {
            "project": {"key": project_key},
            "issuetype": {"id": story_type_id},
            "summary": story.summary,
            "description": story.description_adf,
            "labels": story.labels,
        }

        if style == "next-gen":
            fields["parent"] = {"key": epic_key}
        elif epic_link_field:
            fields[epic_link_field] = epic_key

        try:
            result = client.create_issue(fields)
            story.jira_key = result["key"]
            state.record_story(story.control_id, story.jira_key)
            created += 1
            log.info(f"Created story {story.jira_key}: {story.summary}")
        except Exception as e:
            log.error(f"Failed to create story {story.summary}: {e}")

    log.info(f"Stories: {created} created, {skipped} skipped (already exist)")
    return stories


def create_tasks(client, task_specs, stories, config, state):
    project_key = config["jira"]["project_key"]
    style = _detect_project_style(client, project_key)

    issue_type_config = config.get("issue_types", {})
    task_type_name = issue_type_config.get("task", "Task")

    if style == "next-gen":
        task_type_name = issue_type_config.get("task", "Task")
    else:
        task_type_name = issue_type_config.get("subtask", "Sub-task")

    task_type_id = _find_issue_type_id(client, project_key, task_type_name)

    story_key_map = {s.control_id: s.jira_key for s in stories if s.jira_key}

    created = 0
    skipped = 0
    failed = 0

    for task in task_specs:
        if state.is_task_created(task.state_key):
            task.jira_key = state.get_task_key(task.state_key)
            skipped += 1
            continue

        parent_key = story_key_map.get(task.parent_story_control_id)
        if not parent_key:
            log.error(f"No parent story for task {task.summary} (control {task.parent_story_control_id})")
            failed += 1
            continue

        fields = {
            "project": {"key": project_key},
            "issuetype": {"id": task_type_id},
            "summary": task.summary,
            "description": task.description_adf,
            "labels": task.labels,
            "parent": {"key": parent_key},
        }

        if task.assignee_account_id:
            fields["assignee"] = {"accountId": task.assignee_account_id}

        if task.due_date:
            fields["duedate"] = task.due_date

        try:
            result = client.create_issue(fields)
            task.jira_key = result["key"]
            state.record_task(task.state_key, task.jira_key)
            created += 1
            log.info(f"Created task {task.jira_key}: {task.summary}")
        except Exception as e:
            log.error(f"Failed to create task {task.summary}: {e}")
            failed += 1

    log.info(f"Tasks: {created} created, {skipped} skipped, {failed} failed")
    return task_specs


def create_issue_links(client, task_specs, state):
    """Create links between related tasks (multi-system, population→sample, IPE pairs)."""
    by_request = {}
    for t in task_specs:
        if t.jira_key:
            by_request.setdefault(t.request_number, []).append(t)

    linked = 0

    # Multi-system: link tasks from the same request number
    for req_num, tasks in by_request.items():
        if len(tasks) <= 1:
            continue
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i].jira_key, tasks[j].jira_key
                if not state.is_link_created(a, "Relates", b):
                    try:
                        client.create_issue_link("Relates", a, b)
                        state.record_link(a, "Relates", b)
                        linked += 1
                    except Exception as e:
                        log.warning(f"Failed to link {a} ↔ {b}: {e}")

    # Population → Sample: link populations to sample tasks on same control
    populations = {}
    samples = {}
    for t in task_specs:
        if not t.jira_key:
            continue
        if t.evidence_type == "population":
            populations.setdefault(t.parent_story_control_id, []).append(t)
        elif t.evidence_type == "sample":
            samples.setdefault(t.parent_story_control_id, []).append(t)

    for control_id, pops in populations.items():
        samps = samples.get(control_id, [])
        for pop in pops:
            for samp in samps:
                if not state.is_link_created(pop.jira_key, "Blocks", samp.jira_key):
                    try:
                        client.create_issue_link("Blocks", pop.jira_key, samp.jira_key)
                        state.record_link(pop.jira_key, "Blocks", samp.jira_key)
                        linked += 1
                    except Exception as e:
                        log.warning(f"Failed to link {pop.jira_key} blocks {samp.jira_key}: {e}")

    log.info(f"Issue links: {linked} created")
