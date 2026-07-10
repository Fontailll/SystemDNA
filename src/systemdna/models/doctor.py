from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Recommendation(BaseModel):
    severity: Severity = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    suggested_fix: str | None = Field(default=None)
    reference: str | None = Field(default=None)


class DoctorReport(BaseModel):
    snapshot_id: str = Field(...)
    timestamp: str = Field(...)
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
