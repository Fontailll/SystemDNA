from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.services import ServicesInfo
from systemdna.platform.linux import services


class ServicesCollector(Collector[ServicesInfo]):
    """Collects system service information from the active init system."""

    name = "services"
    description = "Collect system services"

    def collect(self) -> ServicesInfo:
        return services.get_services_info()
