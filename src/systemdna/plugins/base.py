from __future__ import annotations

from abc import ABC, abstractmethod

from systemdna.collectors.base import Collector
from systemdna.doctor.registry import DoctorRule


class Plugin(ABC):
    """Base class for all plugins."""

    name: str
    version: str
    description: str

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin. Called when plugin is loaded."""
        ...

    def register_collectors(self) -> list[type[Collector[object]]]:
        """Return collector classes to register. Override to add collectors."""
        return []

    def register_doctor_rules(self) -> list[type[DoctorRule]]:
        """Return doctor rule classes to register."""
        return []

    def cleanup(self) -> None:
        """Cleanup when plugin is unloaded."""
        return None
