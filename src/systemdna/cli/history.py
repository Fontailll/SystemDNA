from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_history_engine
from systemdna.core.exceptions import StorageError

history_cmd = typer.Typer(help="View and manage snapshot history")
console = Console()


def _confirm_action(action: str) -> bool:
    result = typer.confirm(f"Are you sure you want to {action}?")
    return result


@history_cmd.command("list")
def list_snapshots() -> None:
    """List all snapshots."""
    history = get_history_engine()
    snapshots = history.list_snapshots()

    if not snapshots:
        console.print(Panel("[yellow]No snapshots found[/]", border_style="yellow"))
        return

    table = Table(title="Snapshots")
    table.add_column("ID", style="cyan")
    table.add_column("Timestamp", style="green")
    table.add_column("Hostname")
    table.add_column("Platform")
    table.add_column("Size", justify="right")

    for s in snapshots:
        size = s.get("file_size", 0)
        if size >= 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        table.add_row(
            s.get("id", ""),
            s.get("timestamp", ""),
            s.get("hostname", ""),
            s.get("platform", ""),
            size_str,
        )

    console.print(table)


@history_cmd.command()
def show(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID to display (defaults to latest)",
    ),
) -> None:
    """Display a snapshot's contents."""
    history = get_history_engine()

    if snapshot_id is None:
        snapshot = history.get_latest_snapshot()
        if snapshot is None:
            console.print(Panel("[yellow]No snapshots found[/]", border_style="yellow"))
            raise typer.Exit(code=1)
    else:
        snapshot = history.show_snapshot(snapshot_id)

    from systemdna.cli.snapshot import _display_snapshot  # noqa: PLC0415

    _display_snapshot(snapshot)


@history_cmd.command()
def delete(
    snapshot_id: str = typer.Argument(..., help="Snapshot ID to delete"),
) -> None:
    """Delete a snapshot by ID."""
    if not _confirm_action(f"delete snapshot {snapshot_id}"):
        console.print("[yellow]Cancelled[/]")
        return

    history = get_history_engine()
    try:
        result = history.delete_snapshot(snapshot_id)
    except StorageError as exc:
        console.print(Panel(f"[red]{exc}[/]", border_style="red"))
        raise typer.Exit(code=1) from None

    if result:
        console.print(Panel(f"[green]Snapshot {snapshot_id} deleted[/]", border_style="green"))
    else:
        console.print(Panel(f"[red]Failed to delete snapshot {snapshot_id}[/]", border_style="red"))
        raise typer.Exit(code=1)


@history_cmd.command()
def clear() -> None:
    """Delete all snapshots."""
    if not _confirm_action("delete ALL snapshots"):
        console.print("[yellow]Cancelled[/]")
        return

    history = get_history_engine()
    result = history.clear_history()

    if result:
        console.print(Panel("[green]All snapshots deleted[/]", border_style="green"))
    else:
        console.print(Panel("[red]Failed to delete some snapshots[/]", border_style="red"))
        raise typer.Exit(code=1)
