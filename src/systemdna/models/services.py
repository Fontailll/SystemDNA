from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    name: str = Field(...)
    status: str = Field(...)
    enabled: bool | None = Field(default=None)
    startup_type: str | None = Field(default=None)
    pid: int | None = Field(default=None)
    description: str | None = Field(default=None)


class InitSystem(BaseModel):
    name: str = Field(...)


class ServicesInfo(BaseModel):
    init_system: InitSystem | None = Field(default=None)
    services: list[ServiceInfo] = Field(default_factory=list)
