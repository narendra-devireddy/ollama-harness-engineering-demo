from __future__ import annotations

from harness_demo.domain import DemoResult, IncidentScenario, Lane, SharedMemory
from harness_demo.scoring import score_memory


def run_deepseek_provider_lane(scenario: IncidentScenario) -> DemoResult:
    memory = SharedMemory()
    memory.incident_facts = {
        "service": scenario.incident["service"],
        "impact": scenario.incident["customer_impact"],
    }
    for item in scenario.expected["required_evidence"]:
        memory.add_evidence(item)
    for item in scenario.expected["required_runbook_steps"]:
        memory.add_runbook_step(item)
    memory.remember_lesson("provider harness preserves reasoning/tool protocol details behind adapter")
    memory.final_plan = {
        "likely_cause": scenario.expected["likely_cause"],
        "evidence": memory.evidence,
        "safe_next_action": "Use the provider harness adapter to return a policy-checked plan for enabling single-flight cache protection.",
        "rollback_plan": "Rollback promotion configuration if cache-miss burst continues after mitigation.",
        "customer_impact": scenario.incident["customer_impact"],
        "open_questions": ["Verify the exact DeepSeek harness package before live demo."],
    }
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.DEEPSEEK_PROVIDER,
        title="Provider-specific DeepSeek harness adapter",
        final_answer="Provider-specific harness controls are hidden behind an adapter boundary so the application consumes a plug-and-play incident response contract.",
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="The plug-and-play future is provider controls plus application-level governance, not raw model calls.",
    )
