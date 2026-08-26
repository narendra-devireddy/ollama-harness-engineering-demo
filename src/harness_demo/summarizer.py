from __future__ import annotations

import json
from dataclasses import asdict

from harness_demo.domain import DemoResult, IncidentScenario
from harness_demo.llm import ChatModel, OllamaCloudModel
from harness_demo.rules import RuleFinding


def summarize_findings_with_ollama(
    scenario: IncidentScenario,
    result: DemoResult,
    findings: list[RuleFinding],
    model_name: str = "gpt-oss:20b",
    model: ChatModel | None = None,
) -> str:
    """Summarize deterministic findings without changing scores or facts."""
    chat_model = model or OllamaCloudModel(model_name)
    payload = {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "incident": scenario.incident,
        },
        "lane": result.lane.value,
        "score": result.score,
        "checks": result.checks,
        "business_takeaway": result.business_takeaway,
        "shared_memory": asdict(result.memory),
        "deterministic_findings": [asdict(finding) for finding in findings],
    }
    prompt = f"""You are a management-briefing summarizer.

You are NOT the judge. The deterministic rule engine has already judged the run.
Do not change scores, pass/fail values, or findings.
Do not add facts that are not in the payload.
Do not hide risks. If there are risks, make them clear.
Be concise and executive-friendly.

Return Markdown with exactly these sections:

## Executive Summary
3-5 bullets.

## What Improved
Bullets. If nothing improved, say so.

## Misses And Risks
Bullets grouped by groundedness, runbook, safety, memory, completeness when relevant.

## Recommended Next Step
One short paragraph.

## Management Takeaway
One sentence.

Payload:
{json.dumps(payload, indent=2, default=str)}
"""
    return chat_model.chat([
        {"role": "system", "content": "Summarize deterministic AI harness evaluation findings for senior management."},
        {"role": "user", "content": prompt},
    ])


def summarize_root_cause_for_management(
    scenario: IncidentScenario,
    result: DemoResult,
    findings: list[RuleFinding],
    model_name: str = "gpt-oss:20b",
    model: ChatModel | None = None,
) -> str:
    """Translate the incident result into management language without changing the ruling."""
    chat_model = model or OllamaCloudModel(model_name)
    payload = {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "incident": scenario.incident,
        },
        "lane": result.lane.value,
        "score": result.score,
        "checks": result.checks,
        "shared_memory": asdict(result.memory),
        "deterministic_findings": [asdict(finding) for finding in findings],
    }
    prompt = f"""You are a management-language incident translator.

You are NOT the judge. Do not change scores, pass/fail values, findings, or facts.
Use only facts in the payload.
Avoid deep technical jargon. If a technical term is necessary, explain it in plain language.
Do not overpromise timelines or certainty.
Do not hide safety, runbook, or groundedness risks.

Return Markdown with exactly these sections:

## Root Cause In Management Language
One short paragraph explaining what likely happened and why customers felt it.

## Business Impact
2-3 bullets focused on customer/business effect, not internal implementation.

## Recommended Action
2-4 bullets. Separate approved next steps from anything requiring human approval.

## Remaining Risks
2-4 bullets. Include missing fields, unsafe suggestions, or unsupported claims when present.

Payload:
{json.dumps(payload, indent=2, default=str)}
"""
    return chat_model.chat([
        {"role": "system", "content": "Translate deterministic incident findings for senior management without changing facts."},
        {"role": "user", "content": prompt},
    ])


def critique_groundedness_with_ollama(
    scenario: IncidentScenario,
    result: DemoResult,
    model_name: str = "gpt-oss:20b",
    model: ChatModel | None = None,
) -> str:
    """Use an LLM to critique unsupported claims without changing deterministic scoring."""
    chat_model = model or OllamaCloudModel(model_name)
    payload = {
        "allowed_sources": {
            "incident": scenario.incident,
            "logs": scenario.logs,
            "runbook": scenario.runbook,
            "prior_memory": scenario.prior_memory,
            "quality_contract": scenario.expected,
        },
        "lane": result.lane.value,
        "score": result.score,
        "checks": result.checks,
        "model_output": result.final_answer,
        "extracted_memory": asdict(result.memory),
    }
    prompt = f"""You are a qualitative groundedness critic for an AI harness demo.

You are NOT the numeric judge. Do not change score or pass/fail values.
Your job is to find semantic unsupported claims that deterministic string rules may miss.

Compare the model output against the allowed sources only.
Flag claims as unsupported when they introduce:
- owners, teams, tools, dashboards, platforms, databases, queues, metrics, or timelines not present in the allowed sources
- mitigations not present in the runbook
- certainty stronger than the evidence supports
- management-language risks hidden behind technical language

Do not call something unsupported merely because it is a paraphrase of an allowed source.

Return Markdown with exactly these sections:

## Qualitative Groundedness Critique
2-5 bullets with concrete unsupported or overconfident claims. If none, say none found.

## Evidence For The Critique
For each issue, quote or paraphrase the model claim briefly and name which allowed source failed to support it.

## Demo Narration
2-3 sentences explaining what this teaches about harness engineering.

Payload:
{json.dumps(payload, indent=2, default=str)}
"""
    return chat_model.chat([
        {"role": "system", "content": "Critique AI output groundedness against supplied incident sources only."},
        {"role": "user", "content": prompt},
    ])
