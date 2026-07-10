from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.configuration import ConfigurationInfo
from systemdna.platform.linux import configuration


class ConfigurationCollector(Collector[ConfigurationInfo]):
    """Collects tracked configuration file hashes and metadata."""

    name = "configuration"
    description = "Collect tracked configuration files"

    def collect(self) -> ConfigurationInfo:
        return configuration.get_configuration_info()
