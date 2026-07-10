from __future__ import annotations

import getpass
import locale as _locale
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path


def detect_platform() -> str:
    return "linux"


def get_hostname() -> str:
    return socket.gethostname()


def get_username() -> str:
    return getpass.getuser()


def get_python_version() -> str:
    return platform.python_version()


def get_architecture() -> str:
    return platform.machine()


def get_platform_identifier() -> str:
    return "linux"


def get_timezone() -> str:
    return datetime.now(timezone.utc).astimezone().tzname() or "UTC"


def get_locale() -> str:
    try:
        return _locale.getdefaultlocale()[0] or "C"
    except Exception:
        return "C"


def get_os_name() -> str:
    return platform.system()


def get_os_version() -> str:
    return platform.version()


def get_distribution() -> str | None:
    try:
        release = Path("/etc/os-release").read_text(encoding="utf-8")
        for line in release.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    except OSError:
        pass
    return None


def get_kernel() -> str | None:
    return platform.release()


def get_common_system_info() -> dict[str, object]:
    return {
        "os_name": get_os_name(),
        "os_version": get_os_version(),
        "distribution": get_distribution(),
        "kernel": get_kernel(),
        "architecture": get_architecture(),
        "hostname": get_hostname(),
        "timezone": get_timezone(),
        "locale": get_locale(),
        "python_version": get_python_version(),
    }
