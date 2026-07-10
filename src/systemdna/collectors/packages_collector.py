from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.packages import PackagesInfo
from systemdna.platform.linux import packages


class PackagesCollector(Collector[PackagesInfo]):
    """Collects installed package information from all detected managers."""

    name = "packages"
    description = "Collect installed packages"

    def collect(self) -> PackagesInfo:
        return packages.get_packages_info()
