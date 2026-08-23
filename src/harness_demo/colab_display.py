from __future__ import annotations

import html
import json
from dataclasses import asdict

from harness_demo.domain import DemoResult, SharedMemory


def render_result_markdown(result: DemoResult) -> str:
    rows = "\n".join(
        f"| {name} | {'yes' if passed else 'no'} |"
        for name, passed in result.checks.items()
    )
    return f"""## {result.title}

| Field | Value |
| --- | --- |
| Scenario | `{result.scenario_id}` |
| Lane | `{result.lane.value}` |
| Score | **{result.score}/100** |

### Harness Checks

| Check | Passed |
| --- | --- |
{rows}

**Takeaway:** {result.business_takeaway}
"""


def render_comparison_markdown(results: list[DemoResult]) -> str:
    rows = "\n".join(
        "| "
        + " | ".join([
            result.lane.value,
            f"{result.score}/100",
            _yes_no(result.checks["evidence"]),
            _yes_no(result.checks["runbook"]),
            _yes_no(result.checks["safety"]),
            _yes_no(result.checks["memory"]),
            _yes_no(result.checks["completeness"]),
        ])
        + " |"
        for result in results
    )
    return f"""## Live Harness Comparison

| Lane | Score | Evidence | Runbook | Safety | Memory | Completeness |
| --- | --- | --- | --- | --- | --- | --- |
{rows}
"""


def render_memory_markdown(memory: SharedMemory) -> str:
    return "\n".join([
        "### Shared Memory Extracted By Harness",
        _section("Incident facts", memory.incident_facts),
        _list_section("Evidence", memory.evidence),
        _list_section("Runbook steps", memory.runbook_steps),
        _list_section("Prior lessons", memory.prior_lessons),
        _list_section("Reviewer objections", memory.reviewer_objections),
        _section("Final plan", memory.final_plan),
    ])


def render_model_output_html(title: str, output: str) -> str:
    escaped = html.escape(output)
    return f"""
<details open>
  <summary><strong>{html.escape(title)}</strong></summary>
  <pre style="white-space: pre-wrap; font-size: 13px; line-height: 1.35; background: #f7f7f8; border: 1px solid #ddd; border-radius: 6px; padding: 12px;">{escaped}</pre>
</details>
"""


def render_hallucination_review_markdown(result: DemoResult) -> str:
    text = result.final_answer.lower()
    unsupported = []
    if "launchdarkly" in text:
        unsupported.append("LaunchDarkly / feature-flag platform is invented; the scenario never names it.")
    if "jaeger" in text:
        unsupported.append("Jaeger tracing is invented; no trace data was provided.")
    if "prometheus" in text:
        unsupported.append("Prometheus metrics are invented; no Prometheus data was provided.")
    if "rds" in text or "cloudwatch" in text:
        unsupported.append("RDS/CloudWatch database metrics are invented; no DB telemetry was provided.")
    if "promotion_rules" in text:
        unsupported.append("`promotion_rules` table is invented; the logs mention promotion cache misses, not a DB table.")
    if "12" in text and "checkout" in text and "failing" in text:
        unsupported.append("Checkout failure percentage is invented; the incident says customers report failed checkouts but gives no failure rate.")
    if "08:15" in text:
        unsupported.append("Detection time is invented; the scenario timestamp is different and should be sourced from the incident object.")
    if "disable the promotion flag" in text:
        unsupported.append("Disabling the promotion flag is not in the approved runbook; approved mitigation is cache single-flight + TTL + rollback readiness.")
    if "scale checkout" in text or "kubectl scale" in text:
        unsupported.append("Scaling checkout workers is unsupported; the runbook does not recommend it for this incident.")

    if not unsupported:
        unsupported.append("No obvious unsupported claims detected by the simple review helper. Still inspect the answer manually.")

    bullets = "\n".join(f"- {item}" for item in unsupported)
    return f"""## Unsupported Or Made-Up Claims To Highlight

{bullets}

### How To Narrate This

The raw model gives a polished incident report, but it silently fabricates tools, metrics, owners, and mitigations. That is exactly why production AI needs a harness: not because the model cannot write well, but because fluent output is not the same as grounded, policy-compliant output.
"""


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _section(title: str, value: object) -> str:
    if not value:
        return f"\n#### {title}\n\n_None_\n"
    return f"\n#### {title}\n\n```json\n{json.dumps(value, indent=2, default=str)}\n```\n"


def _list_section(title: str, values: list[str]) -> str:
    if not values:
        return f"\n#### {title}\n\n_None_\n"
    return f"\n#### {title}\n\n" + "\n".join(f"- {item}" for item in values) + "\n"
