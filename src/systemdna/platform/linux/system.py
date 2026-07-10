import locale
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from systemdna.models.system import SystemInfo


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    result: dict[str, str] = {}
    content = _read_file(path)
    if content is None:
        return result
    for line in content.splitlines():
        stripped = line.strip()
        if "=" in stripped:
            k, _, v = stripped.partition("=")
            v = v.strip('"').strip("'")
            result[k] = v
    return result


def _read_btime(path: Path = Path("/proc/stat")) -> float | None:
    content = _read_file(path)
    if content is None:
        return None
    for line in content.splitlines():
        if line.startswith("btime "):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except ValueError:
                    return None
    return None


def get_os_info() -> SystemInfo:
    os_release = _parse_os_release()
    uname = platform.uname()
    kernel = _read_file(Path("/proc/sys/kernel/version"))
    kernel = kernel or uname.release
    boot_ts = _read_btime()
    boot_time: datetime | None = None
    if boot_ts is not None:
        boot_time = datetime.fromtimestamp(boot_ts, tz=timezone.utc)
    return SystemInfo(
        os_name=os_release.get("NAME", uname.system),
        os_version=os_release.get("VERSION_ID", uname.release),
        distribution=os_release.get("ID"),
        kernel=kernel,
        architecture=uname.machine,
        hostname=get_hostname(),
        timezone=get_timezone(),
        locale=get_locale(),
        python_version=platform.python_version(),
        machine_id=get_machine_id(),
        boot_time=boot_time,
        uptime_seconds=get_uptime(),
    )


def get_boot_time() -> float | None:
    return _read_btime()


def get_uptime() -> float | None:
    content = _read_file(Path("/proc/uptime"))
    if content is None:
        return None
    parts = content.split()
    if parts:
        try:
            return float(parts[0])
        except ValueError:
            return None
    return None


def get_machine_id() -> str | None:
    for path in [Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")]:
        val = _read_file(path)
        if val:
            return val.strip()
    return None


def get_hostname() -> str:
    return platform.node()


def get_timezone() -> str:
    tz_file = _read_file(Path("/etc/timezone"))
    if tz_file:
        return tz_file.strip()
    localtime = Path("/etc/localtime")
    if localtime.exists() or localtime.is_symlink():
        try:
            target = str(localtime.readlink())
            if target.startswith("/"):
                parts = target.split("/")
                if len(parts) > 2:
                    return "/".join(parts[-2:])
                return target
        except (OSError, FileNotFoundError):
            pass
    try:
        return time.tzname[0]
    except Exception:
        return "UTC"


def get_locale() -> str:
    try:
        lang, enc = locale.getdefaultlocale()
        if lang:
            return f"{lang}.{enc}" if enc else lang
    except Exception:
        pass
    return "C"
