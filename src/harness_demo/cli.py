from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from harness_demo.domain import Lane
from harness_demo.live import run_live_hand_built_lane, run_live_raw_lane
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
    live: Annotated[bool, typer.Option(help="Call Ollama Cloud instead of deterministic dry-run lanes.")] = False,
    model: Annotated[str | None, typer.Option(help="Model for the selected live lane.")] = None,
) -> None:
    """Run one demo lane and print its management scorecard."""
    loaded = load_incident_scenario(scenario)
    if live:
        result = _run_live_lane(loaded, lane, model)
    else:
        result = RUNNERS[lane](loaded)
    print_result(console, result)
    path = write_report(report_dir, result)
    console.print(f"Report written: [bold]{path}[/bold]")


@app.command()
def compare(
    scenario: Annotated[str, typer.Option(help="Scenario id to compare.")] = "incident-response",
    live: Annotated[bool, typer.Option(help="Compare live Ollama lanes for raw vs hand-built harness.")] = False,
    raw_model: Annotated[str, typer.Option(help="Strong model for the weak-harness live lane.")] = "gpt-oss:120b",
    harness_model: Annotated[str, typer.Option(help="Medium model for the harnessed live lane.")] = "gpt-oss:20b",
) -> None:
    """Run comparison lanes and print the spectrum scorecard."""
    loaded = load_incident_scenario(scenario)
    if live:
        results = [
            run_live_raw_lane(loaded, model_name=raw_model),
            run_live_hand_built_lane(loaded, model_name=harness_model),
        ]
        console.print("[bold]Live Ollama Cloud comparison[/bold]")
    else:
        results = [RUNNERS[lane](loaded) for lane in Lane]
        console.print("[bold]Deterministic dry-run comparison[/bold]")
    print_comparison(console, results)
    console.print("\nManagement takeaway: harness controls make quality measurable, repeatable, and less dependent on one model.")


@app.command("list-lanes")
def list_lanes() -> None:
    """List available comparison lanes."""
    for lane in Lane:
        console.print(lane.value)


def _run_live_lane(scenario, lane: Lane, model: str | None):
    if lane == Lane.RAW_STRONG:
        return run_live_raw_lane(scenario, model_name=model or "gpt-oss:120b")
    if lane == Lane.HAND_BUILT:
        return run_live_hand_built_lane(scenario, model_name=model or "gpt-oss:20b")
    raise typer.BadParameter(
        "Live mode currently supports raw-strong and hand-built. "
        "Use deterministic mode for strands-sdk/deepseek-provider until those adapters are wired."
    )
