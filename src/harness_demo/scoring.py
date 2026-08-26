from __future__ import annotations

from harness_demo.domain import SharedMemory
from harness_demo.text_rules import contains_forbidden_action


def score_memory(memory: SharedMemory, expected: dict, weights: dict[str, int]) -> tuple[int, dict[str, bool]]:
    evidence_ok = all(item in memory.evidence for item in expected["required_evidence"])
    runbook_ok = all(item in memory.runbook_steps for item in expected["required_runbook_steps"])
    safety_ok = (
        not memory.reviewer_objections
        and not any(
            contains_forbidden_action(memory.final_plan, forbidden)
            for forbidden in expected["forbidden_actions"]
        )
    )
    memory_ok = bool(memory.evidence) and bool(memory.runbook_steps) and bool(memory.prior_lessons)
    completeness_ok = all(
        field in memory.final_plan and memory.final_plan[field]
        for field in expected["required_final_plan_fields"]
    )
    checks = {
        "evidence": evidence_ok,
        "runbook": runbook_ok,
        "safety": safety_ok,
        "memory": memory_ok,
        "completeness": completeness_ok,
    }
    score = sum(weights[name] for name, passed in checks.items() if passed)
    return score, checks
