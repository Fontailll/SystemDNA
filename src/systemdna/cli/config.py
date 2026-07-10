from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from systemdna.cli.dependencies import get_config
from systemdna.core.config import (
    ConfigManager,
    _default_config_dir,
    _default_storage_dir,
)

config_cmd = typer.Typer(help="Manage configuration")
console = Console()

_CONFIG_KEY_MAP: dict[str, tuple[str, type]] = {
    "storage_dir": ("storage_dir", Path),
    "snapshots_dir": ("snapshots_dir", Path),
    "plugins_enabled": ("plugins_enabled", bool),
    "plugin_dirs": ("plugin_dirs", list),
    "log_level": ("log_level", str),
    "max_snapshots": ("max_snapshots", int),
}


@config_cmd.command()
def show() -> None:
    """Show current configuration."""
    config = get_config()
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    data = config.model_dump(mode="json")
    for key, value in data.items():
        if isinstance(value, list):
            table.add_row(key, ", ".join(str(v) for v in value))
        else:
            table.add_row(key, str(value))

    console.print(table)


@config_cmd.command()
def set(
    key: str = typer.Argument(..., help="Config key (e.g. log_level, max_snapshots)"),
    value: str = typer.Argument(..., help="Config value"),
) -> None:
    """Set a configuration value."""
    if key not in _CONFIG_KEY_MAP:
        valid = ", ".join(sorted(_CONFIG_KEY_MAP))
        console.print(
            Panel(
                f"[red]Unknown config key '{key}'[/]\n\nValid keys: {valid}",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    manager = ConfigManager()
    config = get_config()
    attr, _ = _CONFIG_KEY_MAP[key]

    try:
        val: object
        if key == "plugins_enabled":
            val = value.lower() in ("true", "1", "yes")
        elif key == "max_snapshots":
            val = int(value)
        elif key == "plugin_dirs":
            val = [Path(p.strip()) for p in value.split(",")]
        elif key in ("storage_dir", "snapshots_dir"):
            val = Path(value)
        else:
            val = value
    except (ValueError, TypeError) as exc:
        console.print(
            Panel(f"[red]Invalid value for '{key}': {exc}[/]", border_style="red")
        )
        raise typer.Exit(code=1) from None

    setattr(config, attr, val)
    manager.save(config)
    console.print(
        Panel(f"[green]Set {key} = {value}[/]", border_style="green")
    )


@config_cmd.command()
def path() -> None:
    """Show configuration and storage paths."""

    config_dir = _default_config_dir()
    storage_dir = _default_storage_dir()
    manager = ConfigManager()
    config_path = manager._config_path

    table = Table(title="Paths")
    table.add_column("Purpose", style="cyan")
    table.add_column("Path")

    table.add_row("Config directory", str(config_dir))
    table.add_row("Config file", str(config_path))
    table.add_row("Storage directory", str(storage_dir))

    console.print(table)


@config_cmd.command()
def reset() -> None:
    """Reset configuration to defaults."""
    result = typer.confirm("Are you sure you want to reset configuration to defaults?")
    if not result:
        console.print("[yellow]Cancelled[/]")
        return

    manager = ConfigManager()
    manager.reset()
    console.print(Panel("[green]Configuration reset to defaults[/]", border_style="green"))  # noqa: E501
