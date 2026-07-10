from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.security import SecurityInfo
from systemdna.platform.linux import security


class SecurityCollector(Collector[SecurityInfo]):
    """Collects security config: firewall, SELinux, AppArmor, SSH."""

    name = "security"
    description = "Collect security configuration"

    def collect(self) -> SecurityInfo:
        return security.get_security_info()
