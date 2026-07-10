from __future__ import annotations

from abc import ABC, abstractmethod

from systemdna.models.doctor import Recommendation, Severity
from systemdna.models.snapshot import Snapshot


class DoctorRule(ABC):
    name: str
    description: str
    severity: Severity

    @abstractmethod
    def check(self, snapshot: Snapshot) -> Recommendation | None: ...


class DoctorRegistry:
    def __init__(self) -> None:
        self._rules: list[DoctorRule] = []

    def register(self, rule: DoctorRule) -> None:
        self._rules.append(rule)

    def get_all(self) -> list[DoctorRule]:
        return list(self._rules)
