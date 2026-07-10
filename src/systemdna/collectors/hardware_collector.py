from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.hardware import HardwareInfo
from systemdna.platform.linux import hardware


class HardwareCollector(Collector[HardwareInfo]):
    """Collects hardware information including CPU, memory, and disks."""

    name = "hardware"
    description = "Collect hardware information"

    def collect(self) -> HardwareInfo:
        return hardware.get_hardware_info()
