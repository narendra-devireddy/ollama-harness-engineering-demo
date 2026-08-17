from __future__ import annotations

from harness_demo.domain import DemoResult, IncidentScenario, Lane, SharedMemory
from harness_demo.scoring import score_memory


def run_raw_strong_lane(scenario: IncidentScenario) -> DemoResult:
    memory = SharedMemory()
    memory.incident_facts = {
        "service": scenario.incident["service"],
        "impact": scenario.incident["customer_impact"],
    }
    memory.add_evidence("p95 latency increased from 240ms to 2100ms")
    memory.final_plan = {
        "likely_cause": "payment gateway instability during promotion traffic",
        "evidence": ["payment timeout errors increased"],
        "safe_next_action": "restart all checkout pods and temporarily disable payment writes",
        "customer_impact": scenario.incident["customer_impact"],
    }
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.RAW_STRONG,
        title="Strong model with weak harness",
        final_answer="Plausible incident response, but it confuses downstream payment timeouts with root cause and proposes unsafe actions.",
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="A strong model can sound confident while missing policy, memory, and safety constraints.",
    )
