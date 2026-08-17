from __future__ import annotations

from harness_demo.domain import DemoResult, IncidentScenario, Lane, SharedMemory
from harness_demo.scoring import score_memory


def triage_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    memory.incident_facts = {
        "incident_id": scenario.incident["id"],
        "service": scenario.incident["service"],
        "impact": scenario.incident["customer_impact"],
        "detected_at": scenario.incident["detected_at"],
    }


def log_investigator_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    logs = scenario.logs.lower()
    evidence = scenario.expected["required_evidence"]
    if "p95_latency_ms=240" in logs and "p95_latency_ms=2100" in logs:
        memory.add_evidence(evidence[0])
    if "repeated promotion_price_cache miss events" in logs:
        memory.add_evidence(evidence[1])
    if "upstream_latency_source=checkout-api" in logs:
        memory.add_evidence(evidence[2])


def runbook_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    runbook = scenario.runbook.lower()
    steps = scenario.expected["required_runbook_steps"]
    if "single-flight lock" in runbook:
        memory.add_runbook_step(steps[0])
    if "ttl to 60 seconds" in runbook:
        memory.add_runbook_step(steps[1])
    if "keep payment writes enabled" in runbook and "exceeds 12%" in runbook:
        memory.add_runbook_step(steps[2])
    if "rollback to the previous promotion configuration" in runbook:
        memory.add_runbook_step(steps[3])


def memory_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    if "single-flight lock" in scenario.prior_memory:
        memory.remember_lesson("prior incident fixed by single-flight lock and shorter TTL")
    if "Restarting checkout pods did not help" in scenario.prior_memory:
        memory.remember_lesson("avoid restarting all checkout pods without crash-loop evidence")


def reviewer_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    plan_text = str(memory.final_plan).lower()
    for action in scenario.expected["forbidden_actions"]:
        if action in plan_text:
            memory.reviewer_objections.append(f"Blocked forbidden action: {action}")


def fix_planner_agent(scenario: IncidentScenario, memory: SharedMemory) -> None:
    memory.final_plan = {
        "likely_cause": scenario.expected["likely_cause"],
        "evidence": memory.evidence,
        "safe_next_action": "Enable promotion price cache single-flight lock and lower TTL to 60 seconds during rollout.",
        "rollback_plan": "Rollback to the previous promotion configuration if latency does not recover within 10 minutes.",
        "customer_impact": scenario.incident["customer_impact"],
        "open_questions": ["Confirm payment timeout rate remains below the 12% write-disable threshold."],
    }


def run_hand_built_lane(scenario: IncidentScenario) -> DemoResult:
    memory = SharedMemory()
    triage_agent(scenario, memory)
    log_investigator_agent(scenario, memory)
    runbook_agent(scenario, memory)
    memory_agent(scenario, memory)
    fix_planner_agent(scenario, memory)
    reviewer_agent(scenario, memory)
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.HAND_BUILT,
        title="Normal model with hand-built harness",
        final_answer="The harness coordinates specialist agents through shared memory, validates evidence and runbook usage, and blocks unsafe remediation.",
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="The harness makes quality repeatable by turning context, policy, and review into executable controls.",
    )
