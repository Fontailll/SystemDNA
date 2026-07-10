from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_doctor_engine, get_history_engine
from systemdna.models.doctor import Severity

doctor_cmd = typer.Typer(help="Analyze snapshots for recommendations")
console = Console()

_SEVERITY_STYLES: dict[Severity, str] = {
    Severity.INFO: "blue",
    Severity.WARNING: "yellow",
    Severity.ERROR: "red",
}

_SEVERITY_LABELS: dict[Severity, str] = {
    Severity.INFO: "INFO",
    Severity.WARNING: "WARNING",
    Severity.ERROR: "ERROR",
}


@doctor_cmd.command()
def run(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID to analyze (defaults to latest)",
    ),
) -> None:
    """Run doctor analysis on a snapshot."""
    history = get_history_engine()
    doctor = get_doctor_engine()

    if snapshot_id is None:
        snapshot = history.get_latest_snapshot()
        if snapshot is None:
            console.print(Panel("[yellow]No snapshots found[/]", border_style="yellow"))
            raise typer.Exit(code=1)
    else:
        snapshot = history.show_snapshot(snapshot_id)

    report = doctor.analyze(snapshot)

    if not report.recommendations:
        console.print(Panel("[green]No issues found[/]", border_style="green"))
        return

    table = Table(title="Doctor Recommendations")
    table.add_column("Severity", style="bold")
    table.add_column("Title")
    table.add_column("Description")
    table.add_column("Suggested Fix")

    for rec in report.recommendations:
        style = _SEVERITY_STYLES[rec.severity]
        label = _SEVERITY_LABELS[rec.severity]
        table.add_row(
            f"[{style}]{label}[/]",
            rec.title,
            rec.description,
            rec.suggested_fix or "-",
        )

    console.print(table)

    summary = report.summary
    parts = []
    for sev in (Severity.INFO, Severity.WARNING, Severity.ERROR):
        count = summary.get(sev.value, 0)
        if count:
            style = _SEVERITY_STYLES[sev]
            parts.append(f"[{style}]{count} {sev.value}(s)[/]")
    if parts:
        console.print(
            Panel(", ".join(parts), title="Summary", border_style="cyan")
        )
