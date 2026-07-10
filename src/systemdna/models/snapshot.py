from pydantic import BaseModel, Field

from systemdna.models.configuration import ConfigurationInfo
from systemdna.models.hardware import HardwareInfo
from systemdna.models.metadata import SnapshotMetadata
from systemdna.models.network import NetworkInfo
from systemdna.models.packages import PackagesInfo
from systemdna.models.security import SecurityInfo
from systemdna.models.services import ServicesInfo
from systemdna.models.system import SystemInfo
from systemdna.models.users import UsersInfo


class Snapshot(BaseModel):
    metadata: SnapshotMetadata = Field(...)
    system: SystemInfo = Field(...)
    hardware: HardwareInfo | None = Field(default=None)
    network: NetworkInfo | None = Field(default=None)
    packages: PackagesInfo | None = Field(default=None)
    services: ServicesInfo | None = Field(default=None)
    users: UsersInfo | None = Field(default=None)
    security: SecurityInfo | None = Field(default=None)
    configuration: ConfigurationInfo | None = Field(default=None)
