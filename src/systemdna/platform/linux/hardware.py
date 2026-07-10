import contextlib
import os
import platform
import re
from pathlib import Path

import psutil  # type: ignore[import-untyped]

from systemdna.models.hardware import (
    CpuInfo,
    DiskInfo,
    HardwareInfo,
    MemoryInfo,
    SwapInfo,
)


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _parse_cpuinfo(path: Path = Path("/proc/cpuinfo")) -> list[dict[str, str]]:
    content = _read_file(path)
    if content is None:
        return []
    processors: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in content.splitlines():
        if not line.strip():
            if current:
                processors.append(current)
                current = {}
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            current[k.strip()] = v.strip()
    if current:
        processors.append(current)
    return processors


def get_cpu_info() -> CpuInfo:
    processors = _parse_cpuinfo()
    model = ""
    vendor = ""
    physical_ids: set[str] = set()
    for proc in processors:
        if "model name" in proc:
            model = proc["model name"]
        if "vendor_id" in proc:
            vendor = proc["vendor_id"]
        if "physical id" in proc:
            physical_ids.add(proc["physical id"])
    logical_cores = os.cpu_count() or 1
    physical_cores: int | None = len(physical_ids) if physical_ids else None
    if physical_cores and "cpu cores" in processors[0] if processors else {}:
        with contextlib.suppress(ValueError, IndexError, KeyError):
            physical_cores = int(processors[0]["cpu cores"])
    clock_speed: float | None = None
    if processors and "cpu MHz" in processors[0]:
        with contextlib.suppress(ValueError, KeyError):
            clock_speed = float(processors[0]["cpu MHz"])
    if clock_speed is None and processors and "model name" in processors[0]:
        m = re.search(r"@\s*([\d.]+)\s*GHz", processors[0]["model name"])
        if m:
            clock_speed = float(m.group(1)) * 1000
    return CpuInfo(
        model=model or platform.processor(),
        vendor=vendor,
        logical_cores=logical_cores,
        physical_cores=physical_cores,
        clock_speed_mhz=clock_speed,
    )


def _parse_meminfo_value(key: str, content: str | None) -> int | None:
    if content is None:
        return None
    for line in content.splitlines():
        if line.startswith(f"{key}:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    value = int(parts[1])
                    if len(parts) >= 3 and parts[2].lower() == "kb":
                        value *= 1024
                    return value
                except ValueError:
                    return None
    return None


def get_memory_info() -> MemoryInfo:
    content = _read_file(Path("/proc/meminfo"))
    total = _parse_meminfo_value("MemTotal", content) or 0
    available = _parse_meminfo_value("MemAvailable", content) or 0
    _parse_meminfo_value("MemFree", content) or 0
    used = total - available
    percent = (used / total * 100) if total > 0 else 0.0
    return MemoryInfo(
        total_bytes=total,
        available_bytes=available,
        used_bytes=used,
        percent=round(percent, 1),
    )


def get_swap_info() -> SwapInfo:
    content = _read_file(Path("/proc/meminfo"))
    total = _parse_meminfo_value("SwapTotal", content) or 0
    free = _parse_meminfo_value("SwapFree", content) or 0
    used = total - free
    percent = (used / total * 100) if total > 0 else 0.0
    return SwapInfo(
        total_bytes=total,
        used_bytes=used,
        free_bytes=free,
        percent=round(percent, 1),
    )


def get_disk_info() -> list[DiskInfo]:
    disks: list[DiskInfo] = []
    try:
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    DiskInfo(
                        device=part.device,
                        mount_point=part.mountpoint,
                        filesystem=part.fstype,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        percent=usage.percent,
                    )
                )
            except PermissionError:
                disks.append(
                    DiskInfo(
                        device=part.device,
                        mount_point=part.mountpoint,
                        filesystem=part.fstype,
                        total_bytes=0,
                        used_bytes=0,
                        free_bytes=0,
                        percent=0.0,
                    )
                )
    except Exception:
        pass
    return disks


def get_hardware_info() -> HardwareInfo:
    return HardwareInfo(
        cpu=get_cpu_info(),
        memory=get_memory_info(),
        swap=get_swap_info(),
        disks=get_disk_info(),
    )
