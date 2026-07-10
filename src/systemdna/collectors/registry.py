from __future__ import annotations

from typing import Any

from systemdna.collectors.base import Collector
from systemdna.collectors.configuration_collector import ConfigurationCollector
from systemdna.collectors.hardware_collector import HardwareCollector
from systemdna.collectors.network_collector import NetworkCollector
from systemdna.collectors.packages_collector import PackagesCollector
from systemdna.collectors.security_collector import SecurityCollector
from systemdna.collectors.services_collector import ServicesCollector
from systemdna.collectors.system_collector import SystemCollector
from systemdna.collectors.users_collector import UsersCollector


class CollectorRegistry:
    """Central registry for all available collectors."""

    def __init__(self) -> None:
        self._collectors: dict[str, Collector[Any]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        builtins: list[Collector[Any]] = [
            SystemCollector(),
            HardwareCollector(),
            NetworkCollector(),
            PackagesCollector(),
            ServicesCollector(),
            UsersCollector(),
            SecurityCollector(),
            ConfigurationCollector(),
        ]
        for collector in builtins:
            self._collectors[collector.name] = collector

    def register(self, collector: Collector[Any]) -> None:
        """Register a collector, overwriting any with the same name."""
        self._collectors[collector.name] = collector

    def get(self, name: str) -> Collector[Any] | None:
        """Retrieve a collector by name, or None if not found."""
        return self._collectors.get(name)

    def all(self) -> list[Collector[Any]]:
        """Return all registered collectors in insertion order."""
        return list(self._collectors.values())

    def names(self) -> list[str]:
        """Return the names of all registered collectors."""
        return list(self._collectors.keys())

    def remove(self, name: str) -> bool:
        """Remove a collector by name. Returns True if it existed."""
        if name in self._collectors:
            del self._collectors[name]
            return True
        return False

    def register_many(self, collectors: list[Collector[Any]]) -> None:
        """Register multiple collectors at once."""
        for collector in collectors:
            self.register(collector)
