from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Collector(ABC, Generic[T]):  # noqa: UP046
    """Abstract base class for all system information collectors."""

    name: str
    description: str

    @abstractmethod
    def collect(self) -> T:
        """Collect system information and return a typed model."""
        ...


@dataclass
class CollectorResult:
    """Result of a single collector execution."""

    name: str
    success: bool
    data: Any | None = None
    error: str | None = None
    duration_ms: float = field(default=0.0)
