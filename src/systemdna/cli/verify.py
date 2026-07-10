from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from systemdna.cli.dependencies import (
    get_history_engine,
    get_snapshot_engine,
    get_storage_manager,
)
from systemdna.core.exceptions import SnapshotError, StorageError

verify_cmd = typer.Typer(help="Verify snapshot integrity")
console = Console()


@verify_cmd.command()
def check(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID to verify (defaults to latest)",
    ),
) -> None:
    """Verify snapshot integrity."""
    history = get_history_engine()

    try:
        if snapshot_id is None:
            path = history.get_latest_path()
            if path is None:
                console.print(
                    Panel("[yellow]No snapshots found[/]", border_style="yellow")
                )
                raise typer.Exit(code=1)
        else:
            storage = get_storage_manager()
            path = storage.get_snapshot_path(snapshot_id)

        snapshot = get_snapshot_engine().load_snapshot(path)
        m = snapshot.metadata

        if m.schema_version != 1:
            console.print(
                Panel(
                    f"[red]Schema version mismatch: expected 1, got {m.schema_version}[/]",  # noqa: E501
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)

        if not m.snapshot_id:
            console.print(
                Panel("[red]Snapshot is missing snapshot ID[/]", border_style="red")
            )
            raise typer.Exit(code=1)

        if not m.created_at:
            console.print(
                Panel(
                    "[red]Snapshot is missing creation timestamp[/]",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)

        console.print(
            Panel(
                f"[green]Snapshot is valid[/]\n\n"
                f"  [bold]ID:[/]      {m.snapshot_id}\n"
                f"  [bold]Hostname:[/] {m.hostname}\n"
                f"  [bold]Schema:[/]  v{m.schema_version}\n"
                f"  [bold]Created:[/] {m.created_at.isoformat()}\n"
                f"  [bold]Path:[/]    {path}",
                title="Verification Result",
                border_style="green",
            )
        )

    except SnapshotError as exc:
        console.print(
            Panel(f"[red]Snapshot corrupted: {exc}[/]", border_style="red")
        )
        raise typer.Exit(code=1) from None
    except StorageError as exc:
        console.print(
            Panel(f"[red]{exc}[/]", border_style="red")
        )
        raise typer.Exit(code=1) from None
