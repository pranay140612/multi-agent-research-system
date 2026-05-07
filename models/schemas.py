"""
Data models for the multi-agent browser system.
Defines Plan, Step, Result, and related types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActionType(str, Enum):
    """Types of browser actions an agent can perform."""
    SEARCH_GOOGLE = "search_google"
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    READ_PAGE = "read_page"
    SCROLL = "scroll"
    OPEN_TAB = "open_tab"
    CLOSE_TAB = "close_tab"
    SWITCH_TAB = "switch_tab"
    GO_BACK = "go_back"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    EXTRACT_DATA = "extract_data"
    DONE = "done"


class StepStatus(str, Enum):
    """Status of a step in the plan."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """A single step in the execution plan."""
    id: int
    action: ActionType
    description: str
    target: str = ""           # URL, selector, or search query
    data_to_extract: str = ""  # What info to extract from page
    success_criteria: str = "" # How to verify success
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action.value,
            "description": self.description,
            "target": self.target,
            "data_to_extract": self.data_to_extract,
            "success_criteria": self.success_criteria,
            "status": self.status.value,
        }


@dataclass
class StepResult:
    """Result of executing a step."""
    step_id: int
    success: bool
    data: str = ""
    error: str = ""
    page_title: str = ""
    page_url: str = ""
    screenshot_path: str = ""


@dataclass
class Plan:
    """The execution plan containing all steps."""
    goal: str
    steps: list[Step] = field(default_factory=list)
    collected_data: list[dict] = field(default_factory=list)
    final_report: str = ""

    @property
    def completed_steps(self) -> list[Step]:
        return [s for s in self.steps if s.status in (StepStatus.SUCCESS, StepStatus.SKIPPED)]

    @property
    def pending_steps(self) -> list[Step]:
        return [s for s in self.steps if s.status == StepStatus.PENDING]

    @property
    def current_step(self) -> Optional[Step]:
        for s in self.steps:
            if s.status == StepStatus.PENDING:
                return s
        return None

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        return len(self.completed_steps) / len(self.steps) * 100

    def add_data(self, step_id: int, key: str, value: str):
        self.collected_data.append({
            "step_id": step_id,
            "key": key,
            "value": value,
        })
