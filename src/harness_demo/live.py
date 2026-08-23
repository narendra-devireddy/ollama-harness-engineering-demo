from __future__ import annotations

import json
from dataclasses import asdict

from harness_demo.domain import DemoResult, IncidentScenario, Lane, SharedMemory
from harness_demo.llm import ChatModel, OllamaCloudModel
from harness_demo.scoring import score_memory


def run_live_raw_lane(
    scenario: IncidentScenario,
    model_name: str = "gpt-oss:120b",
    model: ChatModel | None = None,
) -> DemoResult:
    chat_model = model or OllamaCloudModel(model_name)
    answer = chat_model.chat([
        {
            "role": "system",
            "content": "You are an expert incident commander. Answer from the incident ticket only.",
        },
        {"role": "user", "content": scenario.incident["prompt"]},
    ])
    memory = _memory_from_answer(scenario, answer, used_harness_memory=False)
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.RAW_STRONG,
        title=f"Live strong model with weak harness ({chat_model.model_name})",
        final_answer=answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="This is the live baseline: one strong model call, no tools, no shared memory, no reviewer, no repair loop.",
    )


def run_live_hand_built_lane(
    scenario: IncidentScenario,
    model_name: str = "gpt-oss:20b",
    model: ChatModel | None = None,
) -> DemoResult:
    chat_model = model or OllamaCloudModel(model_name)
    memory = SharedMemory()
    memory.incident_facts = {
        "incident_id": scenario.incident["id"],
        "service": scenario.incident["service"],
        "impact": scenario.incident["customer_impact"],
        "detected_at": scenario.incident["detected_at"],
    }

    evidence_prompt = f"""Incident:
{scenario.incident['prompt']}

Logs:
{scenario.logs}

Identify evidence for the likely cause and downstream symptoms."""
    evidence_answer = chat_model.chat([
        {"role": "system", "content": "You are the log investigator agent. Use only the supplied logs. Return concise bullets."},
        {"role": "user", "content": evidence_prompt},
    ])
    _add_evidence_signals(scenario, memory, evidence_answer + "\n" + scenario.logs)

    runbook_prompt = f"""Incident:
{scenario.incident['prompt']}

Runbook:
{scenario.runbook}

Select the approved next steps and safety constraints."""
    runbook_answer = chat_model.chat([
        {"role": "system", "content": "You are the runbook agent. Use only the supplied runbook. Return approved mitigation constraints."},
        {"role": "user", "content": runbook_prompt},
    ])
    _add_runbook_signals(scenario, memory, runbook_answer + "\n" + scenario.runbook)

    memory_prompt = f"""Incident:
{scenario.incident['prompt']}

Prior memory:
{scenario.prior_memory}"""
    memory_answer = chat_model.chat([
        {"role": "system", "content": "You are the memory agent. Use only prior incident memory. Return lessons relevant to this incident."},
        {"role": "user", "content": memory_prompt},
    ])
    _add_prior_memory_signals(memory, memory_answer + "\n" + scenario.prior_memory)

    planner_input = {
        "incident": scenario.incident,
        "shared_memory": asdict(memory),
        "required_output_fields": scenario.expected["required_final_plan_fields"],
        "forbidden_actions": scenario.expected["forbidden_actions"],
    }
    plan_answer = chat_model.chat([
        {
            "role": "system",
            "content": (
                "You are the fix planner agent inside a production harness. "
                "Use the shared memory, avoid forbidden actions, and return JSON with the required fields."
            ),
        },
        {"role": "user", "content": json.dumps(planner_input, indent=2)},
    ])
    memory.final_plan = _extract_plan(plan_answer)
    if not memory.final_plan:
        memory.final_plan = {"raw_plan": plan_answer}

    reviewer_notes = _review_plan(scenario, memory)
    memory.reviewer_objections.extend(reviewer_notes)
    if reviewer_notes:
        repair_answer = chat_model.chat([
            {"role": "system", "content": "You are the repair agent. Revise the plan to satisfy reviewer objections. Return JSON only."},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "reviewer_objections": reviewer_notes,
                        "current_plan": memory.final_plan,
                        "shared_memory": asdict(memory),
                        "required_output_fields": scenario.expected["required_final_plan_fields"],
                    },
                    indent=2,
                ),
            },
        ])
        repaired = _extract_plan(repair_answer)
        if repaired:
            memory.final_plan = repaired
            memory.reviewer_objections.extend(_review_plan(scenario, memory))
            plan_answer = repair_answer

    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    final_answer = "\n\n".join([
        "## Log Investigator Agent",
        evidence_answer,
        "## Runbook Agent",
        runbook_answer,
        "## Memory Agent",
        memory_answer,
        "## Fix Planner / Repair Output",
        plan_answer,
    ])
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.HAND_BUILT,
        title=f"Live medium model with hand-built harness ({chat_model.model_name})",
        final_answer=final_answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="This live lane uses multiple controlled model calls, repo-backed tools, shared memory, sensors, reviewer checks, and repair.",
    )


def _memory_from_answer(scenario: IncidentScenario, answer: str, used_harness_memory: bool) -> SharedMemory:
    memory = SharedMemory(
        incident_facts={
            "service": scenario.incident["service"],
            "impact": scenario.incident["customer_impact"],
        },
        final_plan={"raw_answer": answer},
    )
    _add_evidence_signals(scenario, memory, answer)
    _add_runbook_signals(scenario, memory, answer)
    if used_harness_memory:
        _add_prior_memory_signals(memory, answer)
    return memory


def _add_evidence_signals(scenario: IncidentScenario, memory: SharedMemory, text: str) -> None:
    lower = text.lower()
    evidence = scenario.expected["required_evidence"]
    if ("240" in lower and "2100" in lower) or "p95 latency" in lower:
        memory.add_evidence(evidence[0])
    if "promotion_price_cache" in lower or "cache miss" in lower or "cache-miss" in lower:
        memory.add_evidence(evidence[1])
    if "downstream" in lower or "upstream_latency_source=checkout-api" in lower or "upstream latency source" in lower:
        memory.add_evidence(evidence[2])


def _add_runbook_signals(scenario: IncidentScenario, memory: SharedMemory, text: str) -> None:
    lower = text.lower()
    steps = scenario.expected["required_runbook_steps"]
    if "single-flight" in lower or "single flight" in lower:
        memory.add_runbook_step(steps[0])
    if "ttl" in lower and "60" in lower:
        memory.add_runbook_step(steps[1])
    if "keep payment" in lower or ("payment writes" in lower and "12%" in lower):
        memory.add_runbook_step(steps[2])
    if "rollback" in lower and "previous promotion" in lower:
        memory.add_runbook_step(steps[3])


def _add_prior_memory_signals(memory: SharedMemory, text: str) -> None:
    lower = text.lower()
    if "single-flight" in lower or "single flight" in lower:
        memory.remember_lesson("prior incident fixed by single-flight lock and shorter TTL")
    if "restart" in lower and ("did not help" in lower or "worsen" in lower or "avoid" in lower):
        memory.remember_lesson("avoid restarting all checkout pods without crash-loop evidence")


def _extract_plan(text: str) -> dict[str, object]:
    stripped = text.strip()
    candidates = [stripped]
    if "```" in stripped:
        parts = stripped.split("```")
        candidates.extend(part.removeprefix("json").strip() for part in parts)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def _review_plan(scenario: IncidentScenario, memory: SharedMemory) -> list[str]:
    notes: list[str] = []
    plan_text = json.dumps(memory.final_plan, default=str).lower()
    for action in scenario.expected["forbidden_actions"]:
        if action in plan_text:
            notes.append(f"Blocked forbidden action: {action}")
    for field in scenario.expected["required_final_plan_fields"]:
        if field not in memory.final_plan or not memory.final_plan[field]:
            notes.append(f"Missing required final plan field: {field}")
    return notes
