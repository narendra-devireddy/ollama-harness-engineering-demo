from dataclasses import dataclass

from harness_demo.domain import DemoResult, Lane, SharedMemory
from harness_demo.rules import RuleFinding
from harness_demo.scenarios import load_incident_scenario
from harness_demo.summarizer import summarize_findings_with_ollama


@dataclass
class CapturingModel:
    model_name: str = "fake-summarizer"
    captured: str = ""

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.captured = messages[-1]["content"]
        return "## Executive Summary\n- Summary from fake model"


def test_summarizer_includes_scores_and_findings_without_api_key() -> None:
    scenario = load_incident_scenario("incident-response")
    result = DemoResult(
        scenario_id=scenario.id,
        lane=Lane.HAND_BUILT,
        title="test",
        final_answer="answer",
        memory=SharedMemory(final_plan={"likely_cause": "cache issue"}),
        score=75,
        checks={"evidence": True, "runbook": False},
        business_takeaway="takeaway",
    )
    findings = [RuleFinding(
        category="runbook",
        severity="miss",
        title="Approved runbook step missing",
        detail="enable single-flight lock",
    )]
    model = CapturingModel()
    summary = summarize_findings_with_ollama(scenario, result, findings, model=model)
    assert "Executive Summary" in summary
    assert '"score": 75' in model.captured
    assert "Approved runbook step missing" in model.captured
    assert "You are NOT the judge" in model.captured
