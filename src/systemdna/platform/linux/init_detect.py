from __future__ import annotations

from pathlib import Path

from systemdna.models.services import InitSystem, ServicesInfo

from .services import (
    get_openrc_services,
    get_runit_services,
    get_systemd_services,
)


def detect_init_system() -> str | None:
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
            return name
        if path.exists():
            return name
    if Path("/sbin/init").exists():
        return "sysvinit"
    return None


def get_services_info() -> ServicesInfo:
    init_name = detect_init_system()
    init = InitSystem(name=init_name) if init_name else None
    services = []
    if init_name == "systemd":
        services = get_systemd_services()
    elif init_name == "openrc":
        services = get_openrc_services()
    elif init_name == "runit":
        services = get_runit_services()
    return ServicesInfo(init_system=init, services=services)
