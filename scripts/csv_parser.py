import csv
import re
import logging
from .models import EvidenceRequest

log = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "request_number": ["request #", "req #", "request number", "req no", "#", "item", "item #", "no"],
    "control_id": ["control id", "control", "control #", "control number", "ref", "control ref"],
    "control_name": ["control name", "control description", "control title", "control statement"],
    "evidence_description": [
        "evidence description", "request description", "evidence requested",
        "description", "request", "information requested", "evidence request",
    ],
    "evidence_type": ["evidence type", "type", "artifact type", "deliverable type"],
    "systems": ["system", "systems", "applicable system", "application", "in-scope system", "scope"],
    "deadline_group": ["deadline", "deadline group", "due", "phase", "submission phase"],
    "owner": ["owner", "assignee", "responsible", "team", "assigned to", "poc"],
}

EVIDENCE_TYPE_KEYWORDS = {
    "policy": ["policy", "procedure", "documentation", "program document"],
    "population": ["population", "listing", "all changes", "all users", "all employees", "all incidents"],
    "ipe": ["ipe", "integrity", "parameters"],
    "screenshot": ["screenshot", "evidence showing configuration", "screen capture"],
    "config": ["configuration", "settings", "config export"],
    "sample": ["for samples selected", "for the sample", "sample selected by"],
    "report": ["report", "scan results", "summary", "scan report"],
    "contract": ["contract", "agreement", "msa", "sla"],
}


def normalize_columns(headers):
    """Map CSV headers to canonical field names. Returns {canonical: csv_header}."""
    mapping = {}
    headers_lower = [h.strip().lower() for h in headers]

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            for i, header in enumerate(headers_lower):
                if alias == header or alias in header:
                    if canonical not in mapping:
                        mapping[canonical] = headers[i].strip()
                        break
            if canonical in mapping:
                break

    unmapped = [h for h in headers if h.strip() and h.strip() not in mapping.values()]
    if unmapped:
        log.info(f"Unmapped CSV columns (ignored): {unmapped}")

    missing = [k for k in ("request_number", "evidence_description") if k not in mapping]
    if missing:
        log.warning(f"Could not map required columns: {missing}")

    return mapping


def classify_evidence_type(description, explicit_type=None):
    if explicit_type and explicit_type.strip():
        normalized = explicit_type.strip().lower()
        for etype in EVIDENCE_TYPE_KEYWORDS:
            if etype in normalized:
                return etype
        return normalized

    desc_lower = description.lower()
    for etype, keywords in EVIDENCE_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return etype

    return "other"


def parse_systems(raw_value, config_systems):
    """Parse a systems cell into a list of specific system names."""
    if not raw_value or not raw_value.strip():
        return ["N/A"]

    val = raw_value.strip()
    if val.lower() in ("all", "all in-scope systems", "all systems", "all in-scope"):
        return [s["name"] for s in config_systems]

    if val.lower() in ("n/a", "na", "none", "-", ""):
        return ["N/A"]

    parts = re.split(r"[,;/]\s*", val)
    systems = []
    config_names_lower = {s["name"].lower(): s["name"] for s in config_systems}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        matched = config_names_lower.get(part.lower())
        systems.append(matched if matched else part)

    return systems if systems else ["N/A"]


def assign_priority(evidence_type, deadline_group):
    if deadline_group == 2 or evidence_type == "sample":
        return "P3"
    if evidence_type in ("population", "policy"):
        return "P1"
    return "P2"


def parse_csv(filepath, config):
    systems_config = config.get("systems", [])
    teams_config = config.get("teams", {})

    member_lookup = {}
    for team_name, team_data in teams_config.items():
        for member in team_data.get("members", []):
            member_lookup[member["name"].lower()] = team_name

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        col_map = normalize_columns(reader.fieldnames)

        def get(row, canonical, default=""):
            csv_col = col_map.get(canonical)
            if csv_col and csv_col in row:
                return row[csv_col].strip()
            return default

        requests_out = []
        for row_num, row in enumerate(reader, start=2):
            try:
                req_num = int(get(row, "request_number", "0"))
            except ValueError:
                log.warning(f"Row {row_num}: invalid request number, skipping")
                continue

            if req_num == 0:
                log.warning(f"Row {row_num}: no request number, skipping")
                continue

            evidence_desc = get(row, "evidence_description")
            if not evidence_desc:
                log.warning(f"Row {row_num}: no evidence description, skipping")
                continue

            control_id = get(row, "control_id", "UNK.00")
            control_parts = re.match(r"([A-Z]+)\.?(\d+)?", control_id)
            control_family = control_parts.group(1) if control_parts else "UNK"

            evidence_type = classify_evidence_type(
                evidence_desc, get(row, "evidence_type")
            )

            raw_systems = get(row, "systems")
            system_list = parse_systems(raw_systems, systems_config)

            try:
                deadline_group = int(get(row, "deadline_group", "1"))
            except ValueError:
                deadline_group = 2 if evidence_type == "sample" else 1

            owner_name = get(row, "owner", "Unassigned")
            owner_team = member_lookup.get(owner_name.lower(), "unassigned")

            priority = assign_priority(evidence_type, deadline_group)

            for system in system_list:
                requests_out.append(EvidenceRequest(
                    request_number=req_num,
                    control_id=control_id,
                    control_family=control_family,
                    control_name=get(row, "control_name", control_id),
                    control_description=get(row, "control_name", evidence_desc),
                    evidence_description=evidence_desc,
                    evidence_type=evidence_type,
                    systems=[system],
                    deadline_group=deadline_group,
                    owner_name=owner_name,
                    owner_team=owner_team,
                    priority=priority,
                ))

        log.info(f"Parsed {len(requests_out)} tasks from {filepath} ({row_num - 1} CSV rows)")
        return requests_out
