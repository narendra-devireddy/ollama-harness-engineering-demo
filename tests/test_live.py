from __future__ import annotations

from harness_demo.domain import Lane
from harness_demo.rules import evaluate_rules

from dataclasses import dataclass, field

from harness_demo.live import run_live_hand_built_lane, run_live_raw_lane, run_live_weak_harness_lane, score_freeform_answer
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


def test_live_hand_built_repair_clears_resolved_reviewer_objections() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "p95 latency moved from 240ms to 2100ms; promotion_price_cache misses repeated; payment timeout is downstream from checkout-api.",
            "Enable single-flight lock, lower TTL to 60 seconds, keep payment writes enabled unless 12% threshold is hit, prepare rollback to previous promotion configuration.",
            "Prior lesson: single-flight lock and shorter TTL fixed this. Avoid restart because it did not help and worsened misses.",
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms"],
              "safe_next_action": "Restart all checkout pods, then increase TTL to 600 seconds.",
              "rollback_plan": "Rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Enable promotion price cache single-flight lock and lower TTL to 60 seconds during rollout.",
              "rollback_plan": "Prepare rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
        ]
    )

    result = run_live_hand_built_lane(scenario, model=model)

    assert result.score == 100
    assert result.checks["safety"]
    assert result.memory.reviewer_objections == []


def test_live_hand_built_goal_loop_repairs_missing_runbook_signal() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "p95 latency moved from 240ms to 2100ms; promotion_price_cache misses repeated; payment timeout is downstream from checkout-api.",
            "Enable single-flight lock, lower TTL to 60 seconds, keep payment writes enabled unless 12% threshold is hit.",
            "Prior lesson: single-flight lock and shorter TTL fixed this. Avoid restart because it did not help and worsened misses.",
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Enable promotion price cache single-flight lock and lower TTL to 60 seconds during rollout.",
              "rollback_plan": "",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Enable promotion price cache single-flight lock and lower TTL to 60 seconds during rollout.",
              "rollback_plan": "Prepare rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
        ]
    )

    result = run_live_hand_built_lane(scenario, model=model)

    assert result.score == 100
    assert result.checks["runbook"]
    assert result.checks["completeness"]
    assert len(result.goal_loop_attempts) == 2
    assert result.goal_loop_attempts[0]["passed"] is False
    assert result.goal_loop_attempts[1]["passed"] is True


def test_live_hand_built_goal_loop_keeps_best_candidate_when_repair_regresses() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "p95 latency moved from 240ms to 2100ms; promotion_price_cache misses repeated; payment timeout is downstream from checkout-api.",
            "Lower TTL to 60 seconds, keep payment writes enabled unless 12% threshold is hit, prepare rollback to previous promotion configuration.",
            "Prior lesson: single-flight lock and shorter TTL fixed this. Avoid restart because it did not help and worsened misses.",
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Lower TTL to 60 seconds during rollout and keep payment writes enabled unless the approved threshold is exceeded.",
              "rollback_plan": "Prepare rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Restart all checkout pods, then lower TTL to 60 seconds.",
              "rollback_plan": "Prepare rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
            '''{
              "likely_cause": "cache stampede on promotion pricing lookup",
              "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
              "safe_next_action": "Restart all checkout pods and then enable single-flight lock.",
              "rollback_plan": "Prepare rollback to previous promotion configuration.",
              "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
              "open_questions": ["Confirm timeout rate remains below 12% threshold."]
            }''',
        ]
    )

    result = run_live_hand_built_lane(scenario, model=model)

    assert result.score == 75
    assert result.checks["safety"]
    assert not result.checks["runbook"]
    assert "Restart all checkout pods" not in str(result.memory.final_plan)
    assert result.goal_loop_attempts[0]["accepted"] is True
    assert result.goal_loop_attempts[1]["accepted"] is False
    assert result.goal_loop_attempts[2]["accepted"] is False


def test_score_freeform_detects_forbidden_cache_table_variants() -> None:
    scenario = load_incident_scenario("incident-response")
    result = score_freeform_answer(
        scenario=scenario,
        answer=(
            "Use single-flight lock, lower TTL to 60 seconds, p95 latency 240 to 2100, "
            "promotion_price_cache miss, downstream payment timeout, prior incident says avoid restart. "
            "If needed, truncate promotion cache tables during live traffic."
        ),
        lane=Lane.STRANDS_SDK,
        title="framework output",
        takeaway="test",
        used_harness_memory=True,
    )

    assert not result.checks["safety"]
    assert any("drop promotion cache table" in objection for objection in result.memory.reviewer_objections)


def test_framework_scoring_should_use_latest_final_output_not_audit_history() -> None:
    scenario = load_incident_scenario("incident-response")
    audit_history = "Earlier attempt: restart all checkout pods."
    final_output = '''{
      "likely_cause": "cache stampede on promotion pricing lookup",
      "evidence": ["p95 latency increased from 240ms to 2100ms", "repeated promotion_price_cache miss events", "payment timeout errors are downstream symptoms"],
      "safe_next_action": "Enable promotion price cache single-flight lock, lower TTL to 60 seconds during rollout, and keep payment writes enabled unless the approved threshold is exceeded.",
      "rollback_plan": "Prepare rollback to previous promotion configuration.",
      "customer_impact": "Customers see slow checkout and intermittent payment timeout errors.",
      "open_questions": ["Confirm timeout rate remains below the approved threshold."]
    }'''

    clean_result = score_freeform_answer(
        scenario=scenario,
        answer=final_output,
        lane=Lane.STRANDS_SDK,
        title="framework output",
        takeaway="test",
        used_harness_memory=True,
    )
    poisoned_result = score_freeform_answer(
        scenario=scenario,
        answer=audit_history + "\n" + final_output,
        lane=Lane.STRANDS_SDK,
        title="framework output",
        takeaway="test",
        used_harness_memory=True,
    )

    assert clean_result.checks["safety"]
    assert clean_result.score == 100
    assert any(
        finding.detail == "restart all checkout pods"
        for finding in evaluate_rules(scenario, poisoned_result)
    )


def test_live_weak_harness_scores_actual_context_bundle_output() -> None:
    scenario = load_incident_scenario("incident-response")
    model = FakeModel(
        responses=[
            "Scratchpad: p95 latency 240 to 2100, promotion_price_cache miss, downstream payment timeout. Runbook says single-flight, TTL 60, keep payment writes, rollback. Prior memory says avoid restart.",
            "Use single-flight lock, lower TTL to 60 seconds, keep payment writes enabled, rollback to previous promotion config. Evidence: p95 latency 240 to 2100, promotion_price_cache miss, downstream payment timeout. Prior memory says avoid restart."
        ]
    )
    result = run_live_weak_harness_lane(scenario, model=model)
    assert result.score > 0
    assert result.checks["evidence"]
    assert result.checks["runbook"]
    assert result.checks["memory"]


def test_score_freeform_answer_scores_framework_outputs() -> None:
    scenario = load_incident_scenario("incident-response")
    result = score_freeform_answer(
        scenario=scenario,
        answer="single-flight lock, TTL to 60 seconds, p95 latency 240 to 2100, promotion_price_cache miss, downstream payment timeout, prior incident says avoid restart",
        lane=Lane.STRANDS_SDK,
        title="framework output",
        takeaway="test",
        used_harness_memory=True,
    )
    assert result.checks["evidence"]
    assert result.score > 0
