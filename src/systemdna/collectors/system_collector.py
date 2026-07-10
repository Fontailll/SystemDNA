from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.system import SystemInfo
from systemdna.platform.linux import system


class SystemCollector(Collector[SystemInfo]):
    """Collects operating system information."""

    name = "system"
    description = "Collect operating system information"

    def collect(self) -> SystemInfo:
        return system.get_os_info()
