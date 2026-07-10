from __future__ import annotations

import subprocess
from pathlib import Path

from systemdna.models.packages import PackageInfo, PackageManager, PackagesInfo


def _which(name: str) -> bool:
    try:
        result = subprocess.run(
            ["which", name],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_pkg_manager(name: str) -> bool:
    return _which(name)


def detect_package_managers() -> list[str]:
    managers = ["pacman", "dpkg", "rpm", "xbps", "apk", "flatpak", "snap", "emerge"]
    return [m for m in managers if _check_pkg_manager(m)]


def _run_cmd(args: list[str], timeout: int = 60) -> str | None:
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


def get_packages_from_dpkg() -> list[PackageInfo]:
    output = _run_cmd(["dpkg-query", "-W", "-f", "${Package}|${Version}|${Status}\n"])
    if output is None:
        return []
    packages: list[PackageInfo] = []
    for line in output.splitlines():
        parts = line.split("|")
        if len(parts) >= 3:
            name = parts[0].strip()
            version = parts[1].strip()
            status = parts[2].strip()
            if "installed" in status:
                packages.append(
                    PackageInfo(name=name, version=version, manager="dpkg", repository=None)
                )
    return packages


def get_packages_from_pacman() -> list[PackageInfo]:
    pkg_dir = Path("/var/lib/pacman/local")
    packages: list[PackageInfo] = []
    if not pkg_dir.is_dir():
        return packages
    for entry in pkg_dir.iterdir():
        if not entry.is_dir():
            continue
        desc_file = entry / "desc"
        if not desc_file.exists():
            continue
        try:
            content = desc_file.read_text(encoding="utf-8", errors="replace")
        except (PermissionError, OSError):
            continue
        name: str | None = None
        version: str | None = None
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if line == "%NAME%":
                if i + 1 < len(lines):
                    name = lines[i + 1].strip()
                i += 2
            elif line == "%VERSION%":
                if i + 1 < len(lines):
                    version = lines[i + 1].strip()
                i += 2
            else:
                i += 1
        if name and version:
            packages.append(
                PackageInfo(name=name, version=version, manager="pacman", repository=None)
            )
    return packages


def get_packages_from_rpm() -> list[PackageInfo]:
    output = _run_cmd([
        "rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}|%{VENDOR}\n"
    ])
    if output is None:
        return []
    packages: list[PackageInfo] = []
    for line in output.splitlines():
        parts = line.split("|")
        if len(parts) >= 2:
            name = parts[0].strip()
            version = parts[1].strip()
            vendor = parts[2].strip() if len(parts) >= 3 else None
            packages.append(
                PackageInfo(name=name, version=version, manager="rpm", repository=vendor)
            )
    return packages


def get_packages_from_apk() -> list[PackageInfo]:
    packages: list[PackageInfo] = []
    installed_db = Path("/lib/apk/db/installed")
    if not installed_db.exists():
        return packages
    try:
        content = installed_db.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError):
        return packages
    name: str | None = None
    version: str | None = None
    for line in content.splitlines():
        if line.startswith("P:"):
            name = line[2:].strip()
        elif line.startswith("V:"):
            version = line[2:].strip()
        elif line == "":
            if name and version:
                packages.append(
                    PackageInfo(name=name, version=version, manager="apk", repository=None)
                )
            name = None
            version = None
    if name and version:
        packages.append(
            PackageInfo(name=name, version=version, manager="apk", repository=None)
        )
    return packages


def get_packages_from_xbps() -> list[PackageInfo]:
    output = _run_cmd(["xbps-query", "-l"])
    if output is None:
        return []
    packages: list[PackageInfo] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 1)
        if len(parts) >= 2:
            pkg_str = parts[1]
            name_ver = pkg_str.rsplit("-", 2)
            if len(name_ver) >= 2:
                name = name_ver[0]
                version = f"{name_ver[1]}-{name_ver[2]}" if len(name_ver) == 3 else name_ver[1]
                packages.append(
                    PackageInfo(name=name, version=version, manager="xbps", repository=None)
                )
    return packages


def get_flatpak_packages() -> list[PackageInfo]:
    output = _run_cmd(["flatpak", "list", "--columns=application,version,origin"])
    if output is None:
        return []
    packages: list[PackageInfo] = []
    lines = output.splitlines()
    if lines and lines[0].startswith("Application"):
        lines = lines[1:]
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 1:
            name = parts[0].strip()
            version = parts[1].strip() if len(parts) >= 2 and parts[1].strip() else ""
            repository = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else None
            if name:
                packages.append(
                    PackageInfo(name=name, version=version, manager="flatpak", repository=repository)
                )
    return packages


def get_packages_info() -> PackagesInfo:
    managers = detect_package_managers()
    manager_objects: list[PackageManager] = []
    for mgr in managers:
        packages: list[PackageInfo] = []
        if mgr == "dpkg":
            packages = get_packages_from_dpkg()
        elif mgr == "pacman":
            packages = get_packages_from_pacman()
        elif mgr == "rpm":
            packages = get_packages_from_rpm()
        elif mgr == "apk":
            packages = get_packages_from_apk()
        elif mgr == "xbps":
            packages = get_packages_from_xbps()
        elif mgr == "flatpak":
            packages = get_flatpak_packages()
        elif mgr in {"snap", "emerge"}:
            packages = []
        manager_objects.append(
            PackageManager(name=mgr, packages=packages)
        )
    return PackagesInfo(managers=manager_objects)
