from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_config

plugins_cmd = typer.Typer(help="Manage plugins")
console = Console()


@plugins_cmd.command()
def list_plugins() -> None:
    """List available and registered plugins."""
    config = get_config()
    table = Table(title="Plugins")
    table.add_column("Status", style="bold")
    table.add_column("Detail")

    table.add_row(
        "[green]enabled[/]" if config.plugins_enabled else "[red]disabled[/]",
        "Plugins are "
        + ("enabled" if config.plugins_enabled else "disabled")
        + " globally",
    )

    if config.plugin_dirs:
        for pd in config.plugin_dirs:
            if pd.is_dir():
                table.add_row("[cyan]directory[/]", str(pd))
                for child in sorted(pd.iterdir()):
                    if child.suffix == ".py":
                        table.add_row("", f"  {child.name}")
            else:
                table.add_row("[yellow]missing[/]", str(pd))
    else:
        table.add_row("[dim]info[/]", "No plugin directories configured")

    console.print(table)


@plugins_cmd.command()
def info(
    plugin_name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show info about a specific plugin."""
    config = get_config()
    for pd in config.plugin_dirs:
        if not pd.is_dir():
            continue
        for child in pd.iterdir():
            if child.stem == plugin_name and child.suffix == ".py":
                console.print(
                    Panel(
                        f"[bold]Name:[/] {plugin_name}\n"
                        f"[bold]Path:[/] {child}\n"
                        f"[bold]Source:[/] {pd}",
                        title="Plugin Info",
                        border_style="cyan",
                    )
                )
                return

    console.print(
        Panel(
            f"[yellow]Plugin '{plugin_name}' not found in configured directories[/]",
            border_style="yellow",
        )
    )
    raise typer.Exit(code=1)
