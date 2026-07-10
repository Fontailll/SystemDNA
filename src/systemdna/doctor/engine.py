from __future__ import annotations

from datetime import datetime

from systemdna.doctor.registry import DoctorRegistry
from systemdna.doctor.rules import (
    FirewallDisabledRule,
    LowDiskSpaceRule,
    ManyPackagesRule,
    MultiplePackageManagersRule,
    NoDnsRule,
    NoInitDetectedRule,
    OldKernelPackagesRule,
    SSHPasswordAuthRule,
    SSHRootLoginRule,
    SwapDisabledRule,
)
from systemdna.models.doctor import DoctorReport
from systemdna.models.snapshot import Snapshot


class DoctorEngine:

    def __init__(self) -> None:
        self.registry = DoctorRegistry()
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        rules = [
            FirewallDisabledRule(),
            SSHPasswordAuthRule(),
            SSHRootLoginRule(),
            SwapDisabledRule(),
            LowDiskSpaceRule(),
            ManyPackagesRule(),
            MultiplePackageManagersRule(),
            NoInitDetectedRule(),
            OldKernelPackagesRule(),
            NoDnsRule(),
        ]
        for rule in rules:
            self.registry.register(rule)

    def analyze(self, snapshot: Snapshot) -> DoctorReport:
        recommendations = []
        for rule in self.registry.get_all():
            rec = rule.check(snapshot)
            if rec is not None:
                recommendations.append(rec)

        summary: dict[str, int] = {}
        for rec in recommendations:
            key = rec.severity.value
            summary[key] = summary.get(key, 0) + 1

        return DoctorReport(
            snapshot_id=snapshot.metadata.snapshot_id,
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations,
            summary=summary,
        )
