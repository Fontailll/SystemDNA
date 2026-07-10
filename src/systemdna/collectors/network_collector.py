from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.network import NetworkInfo
from systemdna.platform.linux import network


class NetworkCollector(Collector[NetworkInfo]):
    """Collects network configuration and listening ports."""

    name = "network"
    description = "Collect network information"

    def collect(self) -> NetworkInfo:
        return network.get_network_info()
