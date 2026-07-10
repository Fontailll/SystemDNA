from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class SnapshotMetadata(BaseModel):
    schema_version: int = Field(...)
    application_version: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
    platform: str = Field(...)
    hostname: str = Field(...)
    duration_ms: int = Field(...)
    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    notes: str | None = Field(default=None)
