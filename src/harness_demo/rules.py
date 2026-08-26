from __future__ import annotations

import json
from dataclasses import dataclass

from harness_demo.domain import DemoResult, IncidentScenario
from harness_demo.text_rules import contains_forbidden_action, mentions_ttl_contradiction


@dataclass(frozen=True)
class RuleFinding:
    category: str
    severity: str
    title: str
    detail: str
    evidence: str = ""
    recommendation: str = ""


def evaluate_rules(scenario: IncidentScenario, result: DemoResult) -> list[RuleFinding]:
    text = _result_text(result)
    findings: list[RuleFinding] = []
    findings.extend(_required_evidence_rules(scenario, result))
    findings.extend(_required_runbook_rules(scenario, result))
    findings.extend(_memory_rules(result))
    findings.extend(_safety_rules(scenario, result, text))
    findings.extend(_contradiction_rules(text))
    findings.extend(_unsupported_claim_rules(text))
    findings.extend(_completeness_rules(scenario, result))
    if not findings:
        findings.append(RuleFinding(
            category="summary",
            severity="info",
            title="No deterministic misses found",
            detail="The rule engine did not find missing required items or known unsupported claims.",
        ))
    return findings


def _required_evidence_rules(scenario: IncidentScenario, result: DemoResult) -> list[RuleFinding]:
    findings = []
    for item in scenario.expected["required_evidence"]:
        if item in result.memory.evidence:
            findings.append(RuleFinding(
                category="evidence",
                severity="good",
                title="Required evidence recovered",
                detail=item,
            ))
        else:
            findings.append(RuleFinding(
                category="evidence",
                severity="miss",
                title="Required evidence missing",
                detail=item,
                recommendation="Ground the answer in the supplied logs and extract this fact explicitly.",
            ))
    return findings


def _required_runbook_rules(scenario: IncidentScenario, result: DemoResult) -> list[RuleFinding]:
    findings = []
    for item in scenario.expected["required_runbook_steps"]:
        if item in result.memory.runbook_steps:
            findings.append(RuleFinding(
                category="runbook",
                severity="good",
                title="Approved runbook step included",
                detail=item,
            ))
        else:
            findings.append(RuleFinding(
                category="runbook",
                severity="miss",
                title="Approved runbook step missing",
                detail=item,
                recommendation="Use the approved runbook rather than inventing an operational action.",
            ))
    return findings


def _memory_rules(result: DemoResult) -> list[RuleFinding]:
    if result.memory.prior_lessons:
        return [RuleFinding(
            category="memory",
            severity="good",
            title="Prior incident memory used",
            detail=lesson,
        ) for lesson in result.memory.prior_lessons]
    return [RuleFinding(
        category="memory",
        severity="miss",
        title="Prior incident memory not used",
        detail="No prior lesson was extracted into shared memory.",
        recommendation="Use prior incident memory to avoid repeating known ineffective actions.",
    )]


def _safety_rules(scenario: IncidentScenario, result: DemoResult, text: str) -> list[RuleFinding]:
    findings = []
    for action in scenario.expected["forbidden_actions"]:
        if contains_forbidden_action(text, action):
            findings.append(RuleFinding(
                category="safety",
                severity="risk",
                title="Forbidden action appears in output",
                detail=action,
                recommendation="Reviewer should block or require explicit runbook threshold before this action is considered.",
            ))
    for objection in result.memory.reviewer_objections:
        findings.append(RuleFinding(
            category="safety",
            severity="risk",
            title="Reviewer objection raised",
            detail=objection,
            recommendation="Run repair loop or send to human review before presenting as final plan.",
        ))
    if not findings:
        findings.append(RuleFinding(
            category="safety",
            severity="good",
            title="No deterministic safety violation found",
            detail="No forbidden action or reviewer objection was detected.",
        ))
    return findings


def _contradiction_rules(text: str) -> list[RuleFinding]:
    findings = []
    if mentions_ttl_contradiction(text):
        findings.append(RuleFinding(
            category="contradiction",
            severity="risk",
            title="TTL recommendation contradicts runbook",
            detail="Output recommends a 10-minute/600-second TTL while the runbook requires lowering TTL to 60 seconds during rollout.",
            recommendation="Repair plan to follow the runbook TTL of 60 seconds unless a human approves deviation.",
        ))
    if contains_forbidden_action(text, "disable payment writes"):
        findings.append(RuleFinding(
            category="contradiction",
            severity="risk",
            title="Payment writes recommendation violates runbook threshold",
            detail="Output mentions disabling payment writes without proving timeout rate exceeded the approved threshold.",
            recommendation="Keep payment writes enabled unless threshold is explicitly met.",
        ))
    if contains_forbidden_action(text, "restart all checkout pods"):
        findings.append(RuleFinding(
            category="contradiction",
            severity="risk",
            title="Pod restart recommendation contradicts prior memory/runbook",
            detail="Prior incident memory says restarting checkout pods did not help and worsened cache misses.",
            recommendation="Avoid pod restart unless crash-loop or memory-pressure evidence is present.",
        ))
    return findings


def _unsupported_claim_rules(text: str) -> list[RuleFinding]:
    unsupported_patterns = {
        "LaunchDarkly / feature flag platform": ["launchdarkly"],
        "Jaeger tracing": ["jaeger"],
        "Prometheus metrics": ["prometheus"],
        "RDS or CloudWatch database telemetry": ["rds", "cloudwatch"],
        "Grafana dashboard": ["grafana"],
        "Slack or Teams channel": ["slack", "teams"],
        "ConfigMap or Kubernetes execution detail": ["configmap", "kubectl", "kubernetes"],
        "promotion_rules database table": ["promotion_rules"],
    }
    findings = []
    for label, needles in unsupported_patterns.items():
        if any(needle in text for needle in needles):
            findings.append(RuleFinding(
                category="groundedness",
                severity="risk",
                title="Unsupported operational detail",
                detail=label,
                recommendation="Only include operational systems/tools that are present in the scenario or approved runbook.",
            ))
    return findings


def _completeness_rules(scenario: IncidentScenario, result: DemoResult) -> list[RuleFinding]:
    findings = []
    for field in scenario.expected["required_final_plan_fields"]:
        if field in result.memory.final_plan and result.memory.final_plan[field]:
            findings.append(RuleFinding(
                category="completeness",
                severity="good",
                title="Required final-plan field present",
                detail=field,
            ))
        else:
            findings.append(RuleFinding(
                category="completeness",
                severity="miss",
                title="Required final-plan field missing",
                detail=field,
                recommendation="Return structured JSON with the required final-plan field.",
            ))
    return findings


def _result_text(result: DemoResult) -> str:
    return (result.final_answer + "\n" + json.dumps(result.memory.final_plan, default=str)).lower()
