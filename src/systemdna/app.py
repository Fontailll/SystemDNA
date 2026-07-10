from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.panel import Panel

from systemdna.cli.config import config_cmd
from systemdna.cli.diff import diff_cmd
from systemdna.cli.doctor import doctor_cmd
from systemdna.cli.export import export_cmd
from systemdna.cli.history import history_cmd
from systemdna.cli.info import info_cmd
from systemdna.cli.plugins import plugins_cmd
from systemdna.cli.score import score_cmd
from systemdna.cli.snapshot import snapshot_cmd
from systemdna.cli.verify import verify_cmd
from systemdna.cli.version import version_cmd
from systemdna.core.exceptions import SystemDNAError

app = typer.Typer(
    name="systemdna",
    help="Capture your system's DNA. Understand every change.",
    no_args_is_help=True,
)

app.add_typer(snapshot_cmd, name="snapshot", help="Create and manage snapshots")
app.add_typer(diff_cmd, name="diff", help="Compare snapshots and show changes")
app.add_typer(doctor_cmd, name="doctor", help="Analyze snapshots for recommendations")
app.add_typer(history_cmd, name="history", help="View and manage snapshot history")
app.add_typer(info_cmd, name="info", help="Show current system information")
app.add_typer(export_cmd, name="export", help="Export snapshots to various formats")
app.add_typer(verify_cmd, name="verify", help="Verify snapshot integrity")
app.add_typer(plugins_cmd, name="plugins", help="Manage plugins")
app.add_typer(config_cmd, name="config", help="Manage configuration")
app.add_typer(version_cmd, name="version", help="Show version information")
app.add_typer(score_cmd, name="score", help="Calculate system health score")

console = Console()


@app.callback()
def main_callback() -> None:
    pass


def main() -> None:
    try:
        app()
    except SystemDNAError as exc:
        console.print(
            Panel(
                f"[red bold]Error:[/] {exc}",
                title="SystemDNA Error",
                border_style="red",
            )
        )
        sys.exit(1)
    except Exception as exc:
        console.print(
            Panel(
                f"[red bold]Unexpected error:[/] {exc}",
                title="Unexpected Error",
                border_style="red",
            )
        )
        sys.exit(1)
