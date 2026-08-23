from harness_demo.domain import DemoResult, Lane, SharedMemory
from harness_demo.rules import evaluate_rules
from harness_demo.scenarios import load_incident_scenario


def test_rule_engine_flags_ttl_contradiction_and_unsupported_tools() -> None:
    scenario = load_incident_scenario("incident-response")
    result = DemoResult(
        scenario_id=scenario.id,
        lane=Lane.HAND_BUILT,
        title="test",
        final_answer="Use Grafana, Slack, kubectl and increase TTL to 10 minutes / 600 seconds.",
        memory=SharedMemory(final_plan={"safe_next_action": "increase TTL to 10 minutes"}),
        score=0,
        checks={},
        business_takeaway="test",
    )
    findings = evaluate_rules(scenario, result)
    titles = {finding.title for finding in findings}
    assert "TTL recommendation contradicts runbook" in titles
    assert "Unsupported operational detail" in titles


def test_rule_engine_explains_missing_required_items() -> None:
    scenario = load_incident_scenario("incident-response")
    result = DemoResult(
        scenario_id=scenario.id,
        lane=Lane.RAW_STRONG,
        title="test",
        final_answer="Generic incident response.",
        memory=SharedMemory(final_plan={"raw_answer": "Generic incident response."}),
        score=0,
        checks={},
        business_takeaway="test",
    )
    findings = evaluate_rules(scenario, result)
    assert any(f.title == "Required evidence missing" for f in findings)
    assert any(f.title == "Approved runbook step missing" for f in findings)
    assert any(f.title == "Prior incident memory not used" for f in findings)
