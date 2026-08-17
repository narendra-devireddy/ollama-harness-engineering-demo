from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from harness_demo.domain import Lane
from harness_demo.reporting import print_comparison, print_result, write_report
from harness_demo.runners import RUNNERS
from harness_demo.scenarios import load_incident_scenario

app = typer.Typer(help="Run harness-engineering management demos.")
console = Console()


@app.command()
def run(
    scenario: Annotated[str, typer.Option(help="Scenario id to run.")] = "incident-response",
    lane: Annotated[Lane, typer.Option(help="Demo lane to run.")] = Lane.HAND_BUILT,
    report_dir: Annotated[Path, typer.Option(help="Where JSON reports are written.")] = Path("reports"),
) -> None:
    """Run one demo lane and print its management scorecard."""
    loaded = load_incident_scenario(scenario)
    result = RUNNERS[lane](loaded)
    print_result(console, result)
    path = write_report(report_dir, result)
    console.print(f"Report written: [bold]{path}[/bold]")


@app.command()
def compare(
    scenario: Annotated[str, typer.Option(help="Scenario id to compare.")] = "incident-response",
) -> None:
    """Run every lane and print the spectrum scorecard."""
    loaded = load_incident_scenario(scenario)
    results = [RUNNERS[lane](loaded) for lane in Lane]
    print_comparison(console, results)
    console.print("\nManagement takeaway: harness controls make quality measurable, repeatable, and less dependent on one model.")


@app.command("list-lanes")
def list_lanes() -> None:
    """List available comparison lanes."""
    for lane in Lane:
        console.print(lane.value)
