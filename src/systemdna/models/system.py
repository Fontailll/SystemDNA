from datetime import datetime

from pydantic import BaseModel, Field


class SystemInfo(BaseModel):
    os_name: str = Field(...)
    os_version: str = Field(...)
    distribution: str | None = Field(default=None)
    kernel: str | None = Field(default=None)
    architecture: str = Field(...)
    hostname: str = Field(...)
    timezone: str = Field(...)
    locale: str = Field(...)
    python_version: str = Field(...)
    machine_id: str | None = Field(default=None)
    boot_time: datetime | None = Field(default=None)
    uptime_seconds: float | None = Field(default=None)
