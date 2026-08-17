from __future__ import annotations

from harness_demo.domain import DemoResult, IncidentScenario, Lane, SharedMemory
from harness_demo.runners.hand_built import (
    fix_planner_agent,
    log_investigator_agent,
    memory_agent,
    reviewer_agent,
    runbook_agent,
    triage_agent,
)
from harness_demo.scoring import score_memory


def run_strands_sdk_lane(scenario: IncidentScenario) -> DemoResult:
    memory = SharedMemory()

    # Offline deterministic stand-in for the Strands runtime:
    # - agents map to Strands agents/tools
    # - reviewer_agent maps to before/after hooks and steering handlers
    # - SharedMemory maps to conversation/session memory
    for step in (
        triage_agent,
        log_investigator_agent,
        runbook_agent,
        memory_agent,
        fix_planner_agent,
        reviewer_agent,
    ):
        step(scenario, memory)

    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.STRANDS_SDK,
        title="Normal model with Strands SDK harness",
        final_answer="Same controls as the hand-built lane, expressed as SDK-level agent runtime concepts: tools, hooks, memory, sessions, and traces.",
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="Strands shows the industry trend: harness engineering is being abstracted into reusable agent infrastructure.",
    )
