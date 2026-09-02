import os
import re
import yaml


ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value, strict=True):
    if isinstance(value, str):
        def replacer(match):
            var_name = match.group(1)
            env_val = os.environ.get(var_name)
            if env_val is None:
                if strict:
                    raise ValueError(f"Environment variable ${{{var_name}}} is not set")
                return match.group(0)
            return env_val
        return ENV_VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v, strict) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item, strict) for item in value]
    return value


def load_config(path, require_credentials=True):
    with open(path) as f:
        raw = yaml.safe_load(f)

    config = _resolve_env_vars(raw, strict=require_credentials)
    errors = validate_config(config, require_credentials=require_credentials)
    if errors:
        raise ValueError("Config validation failed:\n  " + "\n  ".join(errors))

    return config


def validate_config(config, require_credentials=True):
    errors = []

    for key in ("jira", "audit"):
        if key not in config:
            errors.append(f"Missing top-level key: {key}")

    jira = config.get("jira", {})
    required_jira = ["url", "project_key", "epic_key"]
    if require_credentials:
        required_jira += ["email", "api_token"]
    for key in required_jira:
        val = jira.get(key, "")
        if not val or (isinstance(val, str) and val.startswith("${")):
            if require_credentials:
                errors.append(f"Missing jira.{key}")

    audit = config.get("audit", {})
    for key in ("year", "period_start", "period_end"):
        if not audit.get(key):
            errors.append(f"Missing audit.{key}")

    for dl_key in ("deadline_1", "deadline_2"):
        dl = audit.get(dl_key, {})
        if not dl.get("date"):
            errors.append(f"Missing audit.{dl_key}.date")
        if not dl.get("label"):
            errors.append(f"Missing audit.{dl_key}.label")

    return errors


def get_team_member_map(config):
    """Returns {lowercase name: {account_id, team}} for all configured team members."""
    member_map = {}
    for team_name, team_data in config.get("teams", {}).items():
        for member in team_data.get("members", []):
            name_lower = member["name"].lower()
            member_map[name_lower] = {
                "account_id": member.get("jira_account_id"),
                "team": team_name,
                "label": team_data.get("label", f"owner-{team_name}"),
            }
    return member_map


def get_system_labels(config):
    """Returns {system name: label} for all configured systems."""
    return {s["name"]: s["label"] for s in config.get("systems", [])}


def get_control_family_info(config, family_code):
    """Returns {area, full_name} for a control family code, or defaults."""
    families = config.get("control_families", {})
    info = families.get(family_code)
    if info:
        return info
    return {"area": family_code.lower(), "full_name": family_code}
