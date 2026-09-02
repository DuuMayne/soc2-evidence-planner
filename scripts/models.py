from dataclasses import dataclass, field


@dataclass
class EvidenceRequest:
    request_number: int
    control_id: str
    control_family: str
    control_name: str
    control_description: str
    evidence_description: str
    evidence_type: str
    systems: list
    deadline_group: int
    owner_name: str
    owner_team: str
    priority: str = ""


@dataclass
class StorySpec:
    control_id: str
    summary: str
    description_adf: dict = field(default_factory=dict)
    labels: list = field(default_factory=list)
    tasks: list = field(default_factory=list)
    jira_key: str = None


@dataclass
class TaskSpec:
    request_number: int
    summary: str
    description_adf: dict = field(default_factory=dict)
    labels: list = field(default_factory=list)
    assignee_account_id: str = None
    due_date: str = ""
    priority: str = ""
    evidence_type: str = ""
    system: str = ""
    parent_story_control_id: str = ""
    is_blocked: bool = False
    related_request_numbers: list = field(default_factory=list)
    blocking_request_numbers: list = field(default_factory=list)
    jira_key: str = None

    @property
    def state_key(self):
        normalized = self.system.lower().replace(" ", "-").replace("/", "-")
        return f"req-{self.request_number:03d}-{normalized}"


@dataclass
class FilterSpec:
    name: str
    jql: str
    description: str = ""


@dataclass
class GadgetSpec:
    module_key: str
    title: str
    position: dict = field(default_factory=dict)
    color: str = "blue"
    properties: dict = field(default_factory=dict)


@dataclass
class DashboardSpec:
    name: str
    description: str = ""
    gadgets: list = field(default_factory=list)
