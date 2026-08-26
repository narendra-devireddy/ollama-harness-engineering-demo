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
        title=f"Live strong model with no harness ({chat_model.model_name})",
        final_answer=answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="This is the live no-harness baseline: one strong model call against the incident ticket only.",
    )


def run_live_weak_harness_lane(
    scenario: IncidentScenario,
    model_name: str = "gpt-oss:120b",
    model: ChatModel | None = None,
) -> DemoResult:
    chat_model = model or OllamaCloudModel(model_name)
    triage_prompt = f"""Incident:
{scenario.incident['prompt']}

Available context:

Logs:
{scenario.logs}

Runbook:
{scenario.runbook}

Prior incident memory:
{scenario.prior_memory}

Write triage notes into the team scratchpad. Capture suspected cause, evidence, runbook guidance, prior incident lessons, and risks.
"""
    triage_notes = chat_model.chat([
        {
            "role": "system",
            "content": (
                "You are the triage agent in a multi-agent incident workflow. "
                "Write concise notes for a shared scratchpad."
            ),
        },
        {"role": "user", "content": triage_prompt},
    ])

    scratchpad = f"""# Shared scratchpad

## Triage notes
{triage_notes}
"""
    planner_prompt = f"""Incident:
{scenario.incident['prompt']}

Shared scratchpad:
{scratchpad}

Produce the final incident response plan. Include likely_cause, evidence, safe_next_action, rollback_plan, customer_impact, and open_questions.
Avoid unsafe actions.
"""
    answer = chat_model.chat([
        {
            "role": "system",
            "content": (
                "You are the planner agent in a multi-agent incident workflow. "
                "Use the shared scratchpad and produce the best final answer you can."
            ),
        },
        {"role": "user", "content": planner_prompt},
    ])

    memory = _memory_from_answer(scenario, answer, used_harness_memory=True)
    memory.final_plan["shared_scratchpad"] = scratchpad
    plan = _extract_plan(answer)
    if plan:
        memory.final_plan = plan
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.WEAK_HARNESS,
        title=f"Live strong model with weak harness ({chat_model.model_name})",
        final_answer=answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway=(
            "This is a weak multi-agent harness: agents share a scratchpad, but the memory is untyped, "
            "unprovenanced, and not checked by sensors before the final plan. There is no reviewer gate or repair loop."
        ),
    )


def run_live_hand_built_lane(
    scenario: IncidentScenario,
    model_name: str = "gpt-oss:20b",
    model: ChatModel | None = None,
    max_goal_attempts: int = 3,
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
    _add_evidence_signals(scenario, memory, evidence_answer)

    runbook_prompt = f"""Incident:
{scenario.incident['prompt']}

Runbook:
{scenario.runbook}

Select the approved next steps and safety constraints."""
    runbook_answer = chat_model.chat([
        {"role": "system", "content": "You are the runbook agent. Use only the supplied runbook. Return approved mitigation constraints."},
        {"role": "user", "content": runbook_prompt},
    ])
    _add_runbook_signals(scenario, memory, runbook_answer)

    memory_prompt = f"""Incident:
{scenario.incident['prompt']}

Prior memory:
{scenario.prior_memory}"""
    memory_answer = chat_model.chat([
        {"role": "system", "content": "You are the memory agent. Use only prior incident memory. Return lessons relevant to this incident."},
        {"role": "user", "content": memory_prompt},
    ])
    _add_prior_memory_signals(memory, memory_answer)

    planner_input = {
        "incident": scenario.incident,
        "shared_memory": asdict(memory),
        "required_output_fields": scenario.expected["required_final_plan_fields"],
        "required_evidence": scenario.expected["required_evidence"],
        "required_runbook_steps": scenario.expected["required_runbook_steps"],
        "forbidden_actions": scenario.expected["forbidden_actions"],
        "runbook_is_binding": (
            "Use the approved runbook steps as constraints. "
            "For this incident, the approved TTL action is 60 seconds during rollout. "
            "Do not substitute 10 minutes, 600 seconds, pod restarts, payment-write disablement, "
            "or cache-table drop/truncate actions."
        ),
    }
    plan_answer = chat_model.chat([
        {
            "role": "system",
            "content": (
                "You are the fix planner agent inside a production harness. "
                "Use the shared memory and approved runbook as binding constraints. "
                "Return JSON with the required fields. "
                "Every recommendation must be supported by shared memory. "
                "Do not invent tools, owners, dashboards, thresholds, or operational facts."
            ),
        },
        {"role": "user", "content": json.dumps(planner_input, indent=2)},
    ])
    goal_loop_attempts: list[dict[str, object]] = []
    plan_answer = _run_custom_goal_loop(
        scenario=scenario,
        memory=memory,
        chat_model=chat_model,
        initial_answer=plan_answer,
        max_attempts=max_goal_attempts,
        attempts=goal_loop_attempts,
    )

    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    final_answer_parts = [
        "## Log Investigator Agent",
        evidence_answer,
        "## Runbook Agent",
        runbook_answer,
        "## Memory Agent",
        memory_answer,
        "## Fix Planner / Goal Loop Output",
        plan_answer,
    ]
    if goal_loop_attempts:
        final_answer_parts.extend([
            "## Custom Goal Loop Attempts",
            json.dumps(goal_loop_attempts, indent=2),
        ])
    final_answer = "\n\n".join(final_answer_parts)
    return DemoResult(
        scenario_id=scenario.id,
        lane=Lane.HAND_BUILT,
        title=f"Live medium model with hand-built harness ({chat_model.model_name})",
        final_answer=final_answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway="This live lane uses multiple controlled model calls, repo-backed tools, shared memory, sensors, reviewer checks, and a bounded goal loop.",
        goal_loop_attempts=goal_loop_attempts,
    )


def _run_custom_goal_loop(
    scenario: IncidentScenario,
    memory: SharedMemory,
    chat_model: ChatModel,
    initial_answer: str,
    max_attempts: int,
    attempts: list[dict[str, object]],
) -> str:
    answer = initial_answer
    for attempt_number in range(1, max_attempts + 1):
        _apply_plan_answer_to_memory(scenario, memory, answer)
        reviewer_notes = _review_plan(scenario, memory)
        memory.reviewer_objections = reviewer_notes
        score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
        passed = all(checks.values()) and not reviewer_notes
        attempts.append({
            "attempt": attempt_number,
            "score": score,
            "checks": checks,
            "reviewer_objections": reviewer_notes,
            "passed": passed,
        })
        if passed or attempt_number >= max_attempts:
            return answer

        answer = chat_model.chat([
            {
                "role": "system",
                "content": (
                    "You are the repair agent in a production incident harness. "
                    "Revise the plan to satisfy every reviewer objection and failed check. Return JSON only. "
                    "Use only shared memory, approved runbook steps, and required fields. "
                    "Do not include forbidden actions, invented tools, invented owners, or unapproved thresholds."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "reviewer_objections": reviewer_notes,
                        "failed_checks": [name for name, passed_check in checks.items() if not passed_check],
                        "current_plan": memory.final_plan,
                        "shared_memory": asdict(memory),
                        "required_output_fields": scenario.expected["required_final_plan_fields"],
                        "required_runbook_steps": scenario.expected["required_runbook_steps"],
                        "required_evidence": scenario.expected["required_evidence"],
                        "forbidden_actions": scenario.expected["forbidden_actions"],
                    },
                    indent=2,
                ),
            },
        ])
    return answer


def _apply_plan_answer_to_memory(scenario: IncidentScenario, memory: SharedMemory, answer: str) -> None:
    plan = _extract_plan(answer)
    memory.final_plan = plan if plan else {"raw_plan": answer}
    _add_evidence_signals(scenario, memory, answer)
    _add_runbook_signals(scenario, memory, answer)
    _add_prior_memory_signals(memory, answer)


def score_freeform_answer(
    scenario: IncidentScenario,
    answer: str,
    lane: Lane,
    title: str,
    takeaway: str,
    used_harness_memory: bool = True,
) -> DemoResult:
    memory = _memory_from_answer(scenario, answer, used_harness_memory=used_harness_memory)
    plan = _extract_plan(answer)
    if plan:
        memory.final_plan = plan
    reviewer_notes = _review_plan(scenario, memory)
    memory.reviewer_objections.extend(reviewer_notes)
    score, checks = score_memory(memory, scenario.expected, scenario.score_weights)
    return DemoResult(
        scenario_id=scenario.id,
        lane=lane,
        title=title,
        final_answer=answer,
        memory=memory,
        score=score,
        checks=checks,
        business_takeaway=takeaway,
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
    if ("240" in lower and ("2100" in lower or "2.1" in lower or "2,100" in lower)) or "p95 latency" in lower:
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
    if ("rollback" in lower or "revert" in lower) and ("previous promotion" in lower or "previous configuration" in lower):
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
        if _contains_forbidden_action(plan_text, action):
            notes.append(f"Blocked forbidden action: {action}")
    if _mentions_ttl_contradiction(plan_text):
        notes.append("TTL recommendation contradicts runbook: use 60 seconds during rollout, not 10 minutes/600 seconds.")
    for field in scenario.expected["required_final_plan_fields"]:
        if field not in memory.final_plan or not memory.final_plan[field]:
            notes.append(f"Missing required final plan field: {field}")
    return notes


def _contains_forbidden_action(text: str, action: str) -> bool:
    if action in text:
        return True
    if action == "drop promotion cache table":
        return ("drop" in text or "truncate" in text) and "promotion" in text and "cache" in text and "table" in text
    return False


def _mentions_ttl_contradiction(text: str) -> bool:
    return "ttl" in text and ("10 minute" in text or "10-minute" in text or "600" in text)
