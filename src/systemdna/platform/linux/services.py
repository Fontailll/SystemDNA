from __future__ import annotations

import subprocess
from pathlib import Path

from systemdna.models.services import InitSystem, ServiceInfo, ServicesInfo


def detect_init_system() -> InitSystem | None:
    markers: list[tuple[str, str]] = [
        ("systemd", "/run/systemd/system"),
        ("runit", "/sbin/runit"),
        ("openrc", "/sbin/openrc-run"),
        ("openrc", "/sbin/openrc"),
        ("s6", "/etc/s6"),
        ("sysvinit", "/sbin/init"),
    ]
    for name, marker in markers:
        path = Path(marker)
        if path.exists() and name == "systemd":
            return InitSystem(name=name)
        if path.exists():
            return InitSystem(name=name)
    if Path("/sbin/init").exists():
        return InitSystem(name="sysvinit")
    return None


def _run_cmd(args: list[str], timeout: int = 30) -> str | None:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return None


def get_systemd_services() -> list[ServiceInfo]:
    output = _run_cmd([
        "systemctl", "list-units", "--type=service", "--all", "--no-legend",
    ])
    if output is None:
        return []
    services: list[ServiceInfo] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        name = parts[0]
        parts[1]
        active_state = parts[2]
        sub_state = parts[3]
        description = " ".join(parts[4:]) if len(parts) > 4 else None
        if name.endswith(".service"):
            name = name[:-8]
        enabled = None
        enabled_output = _run_cmd(["systemctl", "is-enabled", f"{name}.service"])
        if enabled_output:
            enabled_str = enabled_output.strip()
            if enabled_str == "enabled":
                enabled = True
            elif enabled_str == "disabled":
                enabled = False
            elif enabled_str == "static":
                enabled = None
        services.append(
            ServiceInfo(
                name=name,
                status=f"{active_state}/{sub_state}" if sub_state else active_state,
                enabled=enabled,
                startup_type=None,
                pid=None,
                description=description,
            )
        )
    return services


def get_openrc_services() -> list[ServiceInfo]:
    init_d = Path("/etc/init.d")
    services: list[ServiceInfo] = []
    if not init_d.is_dir():
        return services
    try:
        running_services: set[str] = set()
        run_dir = Path("/run/openrc")
        if run_dir.is_dir():
            for f in run_dir.iterdir():
                if f.name.startswith("openrc-"):
                    running_services.add(f.name[7:])
        for entry in sorted(init_d.iterdir()):
            if entry.is_file():
                svc_name = entry.name
                status = "running" if svc_name in running_services else "stopped"
                services.append(
                    ServiceInfo(
                        name=svc_name,
                        status=status,
                        enabled=None,
                        startup_type=None,
                        pid=None,
                        description=None,
                    )
                )
    except (PermissionError, OSError):
        pass
    return services


def get_runit_services() -> list[ServiceInfo]:
    sv_dir = Path("/etc/sv")
    services: list[ServiceInfo] = []
    if not sv_dir.is_dir():
        return services
    try:
        running_sv_dir = Path("/run/runit")
        running: set[str] = set()
        if running_sv_dir.is_dir():
            for entry in running_sv_dir.iterdir():
                if entry.is_dir():
                    running.add(entry.name)
        for entry in sorted(sv_dir.iterdir()):
            if entry.is_dir():
                svc_name = entry.name
                status = "running" if svc_name in running else "stopped"
                services.append(
                    ServiceInfo(
                        name=svc_name,
                        status=status,
                        enabled=None,
                        startup_type=None,
                        pid=None,
                        description=None,
                    )
                )
    except (PermissionError, OSError):
        pass
    return services


def get_services_info() -> ServicesInfo:
    init = detect_init_system()
    services: list[ServiceInfo] = []
    if init and init.name == "systemd":
        services = get_systemd_services()
    elif init and init.name == "openrc":
        services = get_openrc_services()
    elif init and init.name == "runit":
        services = get_runit_services()
    return ServicesInfo(init_system=init, services=services)
