from __future__ import annotations

import platform
import sys

import typer
from rich.console import Console
from rich.panel import Panel

from systemdna.version import get_version

version_cmd = typer.Typer(
    help="Show version information",
    no_args_is_help=False,
)
console = Console()


@version_cmd.callback(invoke_without_command=True)
def show(_ctx: typer.Context) -> None:
    """Show version, platform, and Python version."""
    ver = get_version()
    py_ver = platform.python_version()
    py_impl = platform.python_implementation()
    os_ver = f"{sys.platform} ({platform.machine()})"

    console.print(
        Panel(
            f"[bold cyan]SystemDNA[/] [white]v{ver}[/]\n\n"
            f"  [bold]Python:[/]   {py_impl} {py_ver}\n"
            f"  [bold]Platform:[/] {os_ver}\n"
            f"  [bold]System:[/]   {platform.system()} {platform.release()}\n"
            f"  [bold]Host:[/]     {platform.node()}",
            title="Version Info",
            border_style="cyan",
        )
    )
