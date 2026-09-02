import json
import os
import hashlib


class RunState:
    def __init__(self, state_dir="state"):
        self.state_dir = state_dir
        self.state_file = os.path.join(state_dir, "run_state.json")
        self._data = self._empty_state()

    def _empty_state(self):
        return {
            "config_hash": "",
            "stories_created": {},
            "tasks_created": {},
            "links_created": [],
            "filters_created": {},
            "dashboard_id": None,
            "gadgets_added": [],
            "moved_issues": {},
        }

    def load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                self._data = json.load(f)
        else:
            self._data = self._empty_state()

    def save(self):
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self._data, f, indent=2)

    def set_config_hash(self, config_path):
        with open(config_path, "rb") as f:
            self._data["config_hash"] = hashlib.sha256(f.read()).hexdigest()[:16]

    def is_story_created(self, control_id):
        return control_id in self._data["stories_created"]

    def get_story_key(self, control_id):
        return self._data["stories_created"].get(control_id)

    def record_story(self, control_id, jira_key):
        self._data["stories_created"][control_id] = jira_key
        self.save()

    def is_task_created(self, task_key):
        return task_key in self._data["tasks_created"]

    def get_task_key(self, task_key):
        return self._data["tasks_created"].get(task_key)

    def record_task(self, task_key, jira_key):
        self._data["tasks_created"][task_key] = jira_key
        self.save()

    def is_link_created(self, from_key, link_type, to_key):
        return [from_key, link_type, to_key] in self._data["links_created"]

    def record_link(self, from_key, link_type, to_key):
        self._data["links_created"].append([from_key, link_type, to_key])
        self.save()

    def is_filter_created(self, name):
        return name in self._data["filters_created"]

    def get_filter_id(self, name):
        return self._data["filters_created"].get(name)

    def record_filter(self, name, filter_id):
        self._data["filters_created"][name] = filter_id
        self.save()

    def get_dashboard_id(self):
        return self._data.get("dashboard_id")

    def record_dashboard(self, dashboard_id):
        self._data["dashboard_id"] = dashboard_id
        self.save()

    def is_gadget_added(self, gadget_key):
        return gadget_key in self._data["gadgets_added"]

    def record_gadget(self, gadget_key):
        self._data["gadgets_added"].append(gadget_key)
        self.save()

    def is_issue_moved(self, issue_key):
        return issue_key in self._data.get("moved_issues", {})

    def record_issue_moved(self, old_key, new_key):
        if "moved_issues" not in self._data:
            self._data["moved_issues"] = {}
        self._data["moved_issues"][old_key] = new_key
        self.save()

    def get_all_story_keys(self):
        return dict(self._data["stories_created"])

    def get_all_task_keys(self):
        return dict(self._data["tasks_created"])

    def get_all_filter_ids(self):
        return dict(self._data["filters_created"])

    def clear(self):
        self._data = self._empty_state()
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def summary(self):
        return {
            "stories": len(self._data["stories_created"]),
            "tasks": len(self._data["tasks_created"]),
            "links": len(self._data["links_created"]),
            "filters": len(self._data["filters_created"]),
            "dashboard": self._data["dashboard_id"] is not None,
            "gadgets": len(self._data["gadgets_added"]),
            "moved": len(self._data.get("moved_issues", {})),
        }
