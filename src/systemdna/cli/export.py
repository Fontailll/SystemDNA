from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from systemdna.cli.dependencies import get_export_engine, get_history_engine
from systemdna.models.snapshot import Snapshot

export_cmd = typer.Typer(help="Export snapshots to various formats")
console = Console()


def _resolve_snapshot(snapshot_id: str | None = None) -> Snapshot:
    history = get_history_engine()
    if snapshot_id is None:
        snapshot = history.get_latest_snapshot()
        if snapshot is None:
            console.print(Panel("[yellow]No snapshots found[/]", border_style="yellow"))
            raise typer.Exit(code=1)
        return snapshot
    return history.show_snapshot(snapshot_id)


@export_cmd.command()
def json(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID (defaults to latest)",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export snapshot as JSON."""
    snapshot = _resolve_snapshot(snapshot_id)
    engine = get_export_engine()
    content = engine.export_json(snapshot, path=output)
    if output:
        console.print(Panel(f"[green]Exported to {output}[/]", border_style="green"))
    else:
        console.print(content)


@export_cmd.command()
def markdown(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID (defaults to latest)",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export snapshot as Markdown report."""
    snapshot = _resolve_snapshot(snapshot_id)
    engine = get_export_engine()
    content = engine.export_markdown(snapshot, path=output)
    if output:
        console.print(Panel(f"[green]Exported to {output}[/]", border_style="green"))
    else:
        console.print(content)


@export_cmd.command()
def html(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID (defaults to latest)",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export snapshot as HTML report."""
    snapshot = _resolve_snapshot(snapshot_id)
    engine = get_export_engine()
    content = engine.export_html(snapshot, path=output)
    if output:
        console.print(Panel(f"[green]Exported to {output}[/]", border_style="green"))
    else:
        console.print(content)
