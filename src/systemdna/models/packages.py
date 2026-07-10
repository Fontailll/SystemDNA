from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    name: str = Field(...)
    version: str = Field(...)
    manager: str = Field(...)
    repository: str | None = Field(default=None)


class PackageManager(BaseModel):
    name: str = Field(...)
    packages: list[PackageInfo] = Field(default_factory=list)


class PackagesInfo(BaseModel):
    managers: list[PackageManager] = Field(default_factory=list)
