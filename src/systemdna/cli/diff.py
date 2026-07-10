from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_diff_engine, get_history_engine

diff_cmd = typer.Typer(help="Compare snapshots and show changes")
console = Console()


def _render_diff(diff_result: object) -> None:
    from systemdna.models.diff import SnapshotDiff  # noqa: PLC0415

    if not isinstance(diff_result, SnapshotDiff):
        console.print(Panel("[red]Invalid diff result[/]", border_style="red"))
        raise typer.Exit(code=1) from None

    summary = diff_result.summary
    total = summary.get("total", 0)
    added = summary.get("added", 0)
    removed = summary.get("removed", 0)
    modified = summary.get("modified", 0)

    if total == 0:
        console.print(Panel("[green]No changes detected[/]", border_style="green"))
        return

    console.print(
        Panel(
            f"[bold]Changes:[/] [green]+{added}[/] [red]-{removed}[/] "
            f"[yellow]~{modified}[/]",
            title="Diff Summary",
            border_style="cyan",
        )
    )

    for section in diff_result.sections:
        if not section.entries:
            continue
        section_panel = Table.grid(padding=(0, 1))
        section_panel.add_column(style="bold")
        section_panel.add_column()
        for entry in section.entries:
            if entry.change_type == "added":
                label = "[green]+[/]"
                text = f"[green]{entry.new_value}[/]"
            elif entry.change_type == "removed":
                label = "[red]-[/]"
                text = f"[red]{entry.old_value}[/]"
            else:
                label = "[yellow]~[/]"
                text = (
                    f"[yellow]{entry.old_value} -> {entry.new_value}[/]"
                )
            section_panel.add_row(f"{label} {entry.path}", text)
        console.print(
            Panel(
                section_panel,
                title=f"[bold]{section.section}[/]",
                border_style="cyan",
            )
        )


@diff_cmd.command()
def compare(
    left_id: str = typer.Argument(..., help="Left (older) snapshot ID"),
    right_id: str = typer.Argument(..., help="Right (newer) snapshot ID"),
) -> None:
    """Compare two snapshots by ID."""
    history = get_history_engine()
    diff_engine = get_diff_engine()

    left = history.show_snapshot(left_id)
    right = history.show_snapshot(right_id)
    result = diff_engine.compare(left, right)
    _render_diff(result)


@diff_cmd.command()
def latest(
    older_id: str | None = typer.Argument(
        None, help="Compare with a specific older snapshot (defaults to previous)",
    ),
) -> None:
    """Compare the latest snapshot with the previous one."""
    history = get_history_engine()
    diff_engine = get_diff_engine()

    all_snapshots = history.list_snapshots()
    if len(all_snapshots) < 2:
        console.print(
            Panel(
                "[yellow]Need at least 2 snapshots to compare[/]",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)

    right_id = all_snapshots[0]["id"]
    left_id = older_id if older_id is not None else all_snapshots[1]["id"]

    left = history.show_snapshot(left_id)
    right = history.show_snapshot(right_id)
    result = diff_engine.compare(left, right)
    _render_diff(result)
