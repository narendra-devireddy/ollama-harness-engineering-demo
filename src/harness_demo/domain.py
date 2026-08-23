from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Lane(str, Enum):
    RAW_STRONG = "raw-strong"
    WEAK_HARNESS = "weak-harness"
    HAND_BUILT = "hand-built"
    STRANDS_SDK = "strands-sdk"
    DEEPSEEK_PROVIDER = "deepseek-provider"


@dataclass(frozen=True)
class IncidentScenario:
    id: str
    name: str
    incident: dict
    expected: dict
    score_weights: dict[str, int]
    logs: str
    runbook: str
    prior_memory: str


@dataclass
class SharedMemory:
    incident_facts: dict[str, str] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    runbook_steps: list[str] = field(default_factory=list)
    prior_lessons: list[str] = field(default_factory=list)
    reviewer_objections: list[str] = field(default_factory=list)
    final_plan: dict[str, object] = field(default_factory=dict)

    def add_evidence(self, item: str) -> None:
        if item not in self.evidence:
            self.evidence.append(item)

    def add_runbook_step(self, item: str) -> None:
        if item not in self.runbook_steps:
            self.runbook_steps.append(item)

    def remember_lesson(self, item: str) -> None:
        if item not in self.prior_lessons:
            self.prior_lessons.append(item)


@dataclass(frozen=True)
class DemoResult:
    scenario_id: str
    lane: Lane
    title: str
    final_answer: str
    memory: SharedMemory
    score: int
    checks: dict[str, bool]
    business_takeaway: str
