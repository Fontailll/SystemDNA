from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from systemdna.cli.dependencies import get_history_engine, get_snapshot_engine

snapshot_cmd = typer.Typer(help="Create and manage snapshots")
console = Console()


@snapshot_cmd.command()
def create(
    notes: str | None = typer.Option(None, "--notes", "-n", help="Notes for the snapshot"),  # noqa: E501
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Custom output path for the snapshot file",
    ),
) -> None:
    """Create a new system snapshot."""
    engine = get_snapshot_engine()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Collecting system information...", total=None)
        snapshot = engine.create_snapshot(notes=notes)

    if output is not None:
        path = engine.save_snapshot(snapshot, path=output)
    else:
        path = engine.save_snapshot(snapshot)

    m = snapshot.metadata
    console.print(
        Panel(
            f"[green]Snapshot created successfully[/]\n\n"
            f"  [bold]ID:[/]        {m.snapshot_id}\n"
            f"  [bold]Hostname:[/]  {m.hostname}\n"
            f"  [bold]Timestamp:[/] {m.created_at.isoformat()}\n"
            f"  [bold]Duration:[/]  {m.duration_ms} ms\n"
            f"  [bold]Path:[/]      {path}",
            title="Snapshot Created",
            border_style="green",
        )
    )


def _display_snapshot(snapshot: object) -> None:
    """Display a snapshot's contents using a Rich tree."""
    from systemdna.models.snapshot import Snapshot  # noqa: PLC0415

    if not isinstance(snapshot, Snapshot):
        console.print(Panel("[red]Invalid snapshot object[/]", border_style="red"))
        raise typer.Exit(code=1)

    m = snapshot.metadata
    tree = Tree(f"[bold]Snapshot {m.snapshot_id}[/]")
    tree.add(f"[cyan]Hostname:[/] {m.hostname}")
    tree.add(f"[cyan]Created:[/] {m.created_at.isoformat()}")
    tree.add(f"[cyan]Platform:[/] {m.platform}")
    tree.add(f"[cyan]Duration:[/] {m.duration_ms} ms")

    sys_branch = tree.add("[bold]System[/]")
    s = snapshot.system
    sys_info = Table.grid(padding=(0, 2))
    sys_info.add_column()
    sys_info.add_column()
    keys = (
        "os_name", "os_version", "distribution", "kernel",
        "architecture", "hostname", "timezone", "locale",
    )
    for key in keys:
        val = getattr(s, key, None)
        if val is not None:
            sys_info.add_row(f"[dim]{key.replace('_', ' ').title()}:[/]", str(val))
    sys_branch.add(sys_info)

    hw = snapshot.hardware
    if hw is not None:
        hw_branch = tree.add("[bold]Hardware[/]")
        if hw.cpu:
            hw_branch.add(f"CPU: {hw.cpu.model} ({hw.cpu.logical_cores} cores)")
        if hw.memory:
            hw_branch.add(f"Memory: {hw.memory.total_bytes} bytes total")
        if hw.disks:
            disk_node = hw_branch.add("Disks")
            for d in hw.disks:
                disk_node.add(f"{d.device} mounted at {d.mount_point} ({d.filesystem})")

    net = snapshot.network
    if net is not None:
        net_branch = tree.add("[bold]Network[/]")
        if net.interfaces:
            for iface in net.interfaces:
                ips = ", ".join(iface.ipv4) if iface.ipv4 else "N/A"
                net_branch.add(f"{iface.name}: MAC={iface.mac_address}, IPv4={ips}")

    pkgs = snapshot.packages
    if pkgs is not None and pkgs.managers:
        pkg_branch = tree.add("[bold]Packages[/]")
        for mgr in pkgs.managers:
            pkg_branch.add(f"{mgr.name}: {len(mgr.packages)} packages")

    svcs = snapshot.services
    if svcs is not None and svcs.services:
        svc_branch = tree.add("[bold]Services[/]")
        svc_branch.add(f"{len(svcs.services)} services")

    users = snapshot.users
    if users is not None and users.users:
        users_branch = tree.add("[bold]Users[/]")
        for u in users.users:
            users_branch.add(f"{u.username} (UID: {u.uid})")

    sec = snapshot.security
    if sec is not None:
        sec_branch = tree.add("[bold]Security[/]")
        fw = sec.firewall
        if fw is not None:
            fw_status = "enabled" if fw.enabled else "disabled"
            sec_branch.add(f"Firewall: {fw_status} ({fw.name})")
        if sec.ssh_password_auth is not None:
            sec_branch.add(f"SSH password auth: {sec.ssh_password_auth}")
        if sec.ssh_root_login is not None:
            sec_branch.add(f"SSH root login: {sec.ssh_root_login}")

    console.print(tree)


@snapshot_cmd.command()
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

    _display_snapshot(snapshot)
