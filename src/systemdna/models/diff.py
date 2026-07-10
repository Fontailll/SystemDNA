from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DiffEntry(BaseModel):
    path: str = Field(...)
    change_type: Literal["added", "removed", "modified"] = Field(...)
    old_value: str | None = Field(default=None)
    new_value: str | None = Field(default=None)


class SectionDiff(BaseModel):
    section: str = Field(...)
    entries: list[DiffEntry] = Field(default_factory=list)


class SnapshotDiff(BaseModel):
    left_id: str = Field(...)
    right_id: str = Field(...)
    left_time: str = Field(...)
    right_time: str = Field(...)
    sections: list[SectionDiff] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
