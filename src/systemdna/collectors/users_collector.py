from __future__ import annotations

from systemdna.collectors.base import Collector
from systemdna.models.users import UsersInfo
from systemdna.platform.linux import users


class UsersCollector(Collector[UsersInfo]):
    """Collects user and group information from the system."""

    name = "users"
    description = "Collect user and group information"

    def collect(self) -> UsersInfo:
        return users.get_users_info()
