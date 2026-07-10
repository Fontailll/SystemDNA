from enum import Enum

from pydantic import BaseModel, Field


class ScoreCategory(str, Enum):
    SECURITY = "security"
    HYGIENE = "hygiene"
    SERVICES = "services"
    CONFIGURATION = "configuration"


class ScoringFinding(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    impact: int = Field(...)
    severity: str = Field(...)


class CategoryScore(BaseModel):
    category: ScoreCategory = Field(...)
    score: int = Field(...)
    max_score: int = Field(...)
    weight: float = Field(...)
    findings: list[ScoringFinding] = Field(default_factory=list)


class HealthScore(BaseModel):
    snapshot_id: str = Field(...)
    timestamp: str = Field(...)
    overall_score: int = Field(...)
    categories: list[CategoryScore] = Field(default_factory=list)
    max_possible: int = Field(...)
    findings_count: int = Field(...)
    critical_count: int = Field(...)
    warning_count: int = Field(...)
    info_count: int = Field(...)
