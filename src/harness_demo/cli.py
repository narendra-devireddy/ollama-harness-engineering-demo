from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(help="Run harness-engineering comparison demos.")
console = Console()


@app.command()
def run(
    case: Annotated[str, typer.Option(help="Case id to run.")] = "invoice-normalization",
    lane: Annotated[str, typer.Option(help="Comparison lane to run.")] = "normal-good-harness",
    model: Annotated[str | None, typer.Option(help="Override Ollama model name.")] = None,
) -> None:
    """Placeholder runner for the first implementation pass."""
    selected_model = model or ("gpt-oss:20b" if lane == "normal-good-harness" else "gpt-oss:120b")
    console.print(f"Case: [bold]{case}[/bold]")
    console.print(f"Lane: [bold]{lane}[/bold]")
    console.print(f"Model: [bold]{selected_model}[/bold]")
    console.print("Next step: wire Ollama client, prompt assembly, sensors, and score persistence.")


@app.command()
def compare(
    case: Annotated[str, typer.Option(help="Case id to compare.")] = "invoice-normalization",
    reports_dir: Annotated[Path, typer.Option(help="Report directory.")] = Path("reports"),
) -> None:
    """Placeholder compare command for generated scorecards."""
    console.print(f"Compare case: [bold]{case}[/bold]")
    console.print(f"Reports: [bold]{reports_dir}[/bold]")
    console.print("Next step: load lane reports and render a compact scoreboard.")
