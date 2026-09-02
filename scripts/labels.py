import re
from .config import get_control_family_info


def normalize_label(text):
    label = text.lower().strip()
    label = re.sub(r"[^a-z0-9\s-]", "", label)
    label = re.sub(r"\s+", "-", label)
    label = re.sub(r"-+", "-", label)
    return label.strip("-")


def compute_task_labels(task_spec, config):
    """Compute the full label set for a TaskSpec-like object."""
    audit = config.get("audit", {})
    year = audit.get("year", "")
    labels = [f"{year}-audit"]

    deadline_key = f"deadline_{task_spec.deadline_group}" if hasattr(task_spec, "deadline_group") else "deadline_1"
    dl = audit.get(deadline_key, {})
    if dl.get("label"):
        labels.append(dl["label"])

    family_info = get_control_family_info(config, task_spec.control_family)
    labels.append(f"{task_spec.control_family.lower()}-{family_info['area']}")

    labels.append(f"evidence-{task_spec.evidence_type}")

    system = task_spec.systems[0] if hasattr(task_spec, "systems") else getattr(task_spec, "system", "N/A")
    if system and system != "N/A":
        system_configs = {s["name"].lower(): s["label"] for s in config.get("systems", [])}
        sys_label = system_configs.get(system.lower(), f"system-{normalize_label(system)}")
        labels.append(sys_label)

    if task_spec.owner_team and task_spec.owner_team != "unassigned":
        teams = config.get("teams", {})
        team_data = teams.get(task_spec.owner_team, {})
        labels.append(team_data.get("label", f"owner-{task_spec.owner_team}"))

    if task_spec.evidence_type == "sample" or (hasattr(task_spec, "deadline_group") and task_spec.deadline_group == 2):
        if "blocked" not in labels:
            labels.append("blocked")

    return labels


def compute_story_labels(control_id, control_family, config):
    audit = config.get("audit", {})
    year = audit.get("year", "")
    labels = [f"{year}-audit"]

    family_info = get_control_family_info(config, control_family)
    labels.append(f"{control_family.lower()}-{family_info['area']}")

    return labels


def get_all_unique_labels(evidence_requests, config):
    """Preview all labels that would be created."""
    all_labels = set()
    seen_controls = set()

    for req in evidence_requests:
        all_labels.update(compute_task_labels(req, config))
        if req.control_id not in seen_controls:
            seen_controls.add(req.control_id)
            all_labels.update(compute_story_labels(req.control_id, req.control_family, config))

    return sorted(all_labels)
