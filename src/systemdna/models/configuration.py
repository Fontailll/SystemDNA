from pydantic import BaseModel, Field


class TrackedFile(BaseModel):
    path: str = Field(...)
    hash: str = Field(...)
    size_bytes: int = Field(...)
    modified_time: str | None = Field(default=None)
    permissions: str | None = Field(default=None)


class ConfigurationInfo(BaseModel):
    tracked_files: list[TrackedFile] = Field(default_factory=list)
