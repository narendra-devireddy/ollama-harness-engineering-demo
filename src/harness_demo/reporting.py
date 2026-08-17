from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

from harness_demo.domain import DemoResult, Lane


def print_result(console: Console, result: DemoResult) -> None:
    console.rule(result.title)
    console.print(f"Scenario: [bold]{result.scenario_id}[/bold]")
    console.print(f"Lane: [bold]{result.lane.value}[/bold]")
    console.print(f"Score: [bold]{result.score}/100[/bold]")
    table = Table(title="Harness Checks")
    table.add_column("Check")
    table.add_column("Passed")
    for name, passed in result.checks.items():
        table.add_row(name, "yes" if passed else "no")
    console.print(table)
    console.print(f"Takeaway: {result.business_takeaway}")


def print_comparison(console: Console, results: list[DemoResult]) -> None:
    table = Table(title="Harness Engineering Spectrum")
    table.add_column("Lane")
    table.add_column("Score")
    table.add_column("Evidence")
    table.add_column("Runbook")
    table.add_column("Safety")
    table.add_column("Memory")
    table.add_column("Completeness")
    for result in results:
        table.add_row(
            result.lane.value,
            f"{result.score}/100",
            _yes_no(result.checks["evidence"]),
            _yes_no(result.checks["runbook"]),
            _yes_no(result.checks["safety"]),
            _yes_no(result.checks["memory"]),
            _yes_no(result.checks["completeness"]),
        )
    console.print(table)


def write_report(report_dir: Path, result: DemoResult) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{result.scenario_id}-{result.lane.value}.json"
    payload = asdict(result)
    payload["lane"] = result.lane.value
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
