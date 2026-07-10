from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_snapshot_engine

info_cmd = typer.Typer(help="Show current system information")
console = Console()


@info_cmd.command()
def show() -> None:
    """Show information about the current system without creating a snapshot."""
    engine = get_snapshot_engine()

    collector_names = [
        "system",
        "hardware",
        "network",
        "packages",
        "services",
        "users",
        "security",
        "configuration",
    ]
    results = engine.runner.run(engine.registry.all(), names=collector_names)

    for result in results:
        if result.success:
            data = result.data
            if data is None:
                continue

            if hasattr(data, "model_dump"):
                dump = data.model_dump(exclude_none=True)
            elif isinstance(data, dict):
                dump = data
            else:
                continue

            table = Table(title=result.name.title(), title_style="bold cyan")
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            if isinstance(dump, dict):
                for key, value in dump.items():
                    if isinstance(value, list):
                        table.add_row(key.replace("_", " ").title(), f"{len(value)} items")  # noqa: E501
                    elif isinstance(value, dict):
                        table.add_row(key.replace("_", " ").title(), "(details)")
                    else:
                        table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
        else:
            console.print(
                Panel(
                    f"[yellow]{result.name}: {result.error}[/]",
                    border_style="yellow",
                )
            )
