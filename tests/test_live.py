from __future__ import annotations

from dataclasses import dataclass, field

from harness_demo.live import run_live_hand_built_lane, run_live_raw_lane, run_live_weak_harness_lane
from harness_demo.scenarios import load_incident_scenario


@dataclass
class FakeModel:
    model_name: str = "fake-model"
    responses: list[str] = field(default_factory=list)

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.responses:
            raise AssertionError("No fake model response left")
        return self.responses.pop(0)


def test_live_raw_scores_actual_model_text_not_static_memory() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(responses=["Payment gateway seems slow. Restart all checkout pods."])
    result = run_live_raw_lane(scenario, model=model)
    assert "Payment gateway seems slow" in result.final_answer
    assert result.score < 100
    assert not result.checks["memory"]


def test_live_hand_built_uses_agent_outputs_and_scores_shared_memory() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "p95 latency moved from 240ms to 2100ms; promotion_price_cache misses repeated; payment timeout is downstream from checkout-api.",
            "Enable single-flight lock, lower TTL to 60 seconds, keep payment writes enabled unless 12% threshold is hit, prepare rollback to previous promotion configuration.",
            "Prior lesson: single-flight lock and shorter TTL fixed this. Avoid restart because it did not help and worsened misses.",
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Enable promotion price cache single-flight lock and lower TTL to 60 seconds during rollout.",
              "rollback_plan": "Rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
        ]
    )
    result = run_live_hand_built_lane(scenario, model=model)
    assert result.score == 100
    assert all(result.checks.values())
    assert len(result.memory.evidence) == 3
    assert len(result.memory.runbook_steps) == 4


def test_live_weak_harness_scores_actual_context_bundle_output() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "Use single-flight lock, lower TTL to 60 seconds, keep payment writes enabled, rollback to previous promotion config. Evidence: p95 latency 240 to 2100, promotion_price_cache miss, downstream payment timeout. Prior memory says avoid restart."
        ]
    )
    result = run_live_weak_harness_lane(scenario, model=model)
    assert result.score > 0
    assert result.checks["evidence"]
    assert result.checks["runbook"]
    assert result.checks["memory"]
