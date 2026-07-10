from __future__ import annotations

from datetime import datetime, timezone

from systemdna.models.snapshot import Snapshot
from systemdna.scoring import rules
from systemdna.scoring.models import (
    CategoryScore,
    HealthScore,
    ScoreCategory,
    ScoringFinding,
)


class ScoringEngine:
    def score(self, snapshot: Snapshot) -> HealthScore:
        security_findings = self._collect_security(snapshot)
        hygiene_findings = self._collect_hygiene(snapshot)
        service_findings = self._collect_services(snapshot)
        config_findings = self._collect_configuration(snapshot)

        security_score = self._calculate_category_score(
            security_findings, 40, 0.40, ScoreCategory.SECURITY,
        )
        hygiene_score = self._calculate_category_score(
            hygiene_findings, 30, 0.30, ScoreCategory.HYGIENE,
        )
        service_score = self._calculate_category_score(
            service_findings, 15, 0.15, ScoreCategory.SERVICES,
        )
        config_score = self._calculate_category_score(
            config_findings, 15, 0.15, ScoreCategory.CONFIGURATION,
        )

        categories = [security_score, hygiene_score, service_score, config_score]

        overall = (
            security_score.score
            + hygiene_score.score
            + service_score.score
            + config_score.score
        )

        all_findings = (
            security_findings + hygiene_findings + service_findings + config_findings
        )

        critical_count = sum(1 for f in all_findings if f.severity == "critical")
        warning_count = sum(1 for f in all_findings if f.severity == "warning")
        info_count = sum(1 for f in all_findings if f.severity == "info")

        return HealthScore(
            snapshot_id=snapshot.metadata.snapshot_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_score=min(max(overall, 0), 100),
            categories=categories,
            max_possible=100,
            findings_count=len(all_findings),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
        )

    def _calculate_category_score(
        self,
        findings: list[ScoringFinding],
        max_score: int,
        weight: float,
        category: ScoreCategory,
    ) -> CategoryScore:
        total_impact = sum(f.impact for f in findings)
        earned = max(max_score - total_impact, 0)
        return CategoryScore(
            category=category,
            score=earned,
            max_score=max_score,
            weight=weight,
            findings=findings,
        )

    def _collect_security(self, snapshot: Snapshot) -> list[ScoringFinding]:
        findings: list[ScoringFinding] = []
        checkers = [
            rules.check_firewall,
            rules.check_ssh_password,
            rules.check_ssh_root,
            rules.check_selinux,
            rules.check_apparmor,
            rules.check_lockdown,
        ]
        for checker in checkers:
            result = checker(snapshot)
            if result is not None:
                findings.append(result)
        return findings

    def _collect_hygiene(self, snapshot: Snapshot) -> list[ScoringFinding]:
        findings: list[ScoringFinding] = []
        single_checkers = [
            rules.check_swap,
            rules.check_dns,
            rules.check_packages_count,
            rules.check_multiple_pm,
            rules.check_old_kernels,
        ]
        for checker in single_checkers:
            result = checker(snapshot)
            if result is not None:
                findings.append(result)
        findings.extend(rules.check_disk_usage(snapshot))
        return findings

    def _collect_services(self, snapshot: Snapshot) -> list[ScoringFinding]:
        findings: list[ScoringFinding] = []
        init_finding = rules.check_init_detected(snapshot)
        if init_finding is not None:
            findings.append(init_finding)
        findings.extend(rules.check_failed_services(snapshot))
        return findings

    def _collect_configuration(self, snapshot: Snapshot) -> list[ScoringFinding]:
        findings: list[ScoringFinding] = []
        tracked_finding = rules.check_has_tracked_files(snapshot)
        if tracked_finding is not None:
            findings.append(tracked_finding)
        uptime_finding = rules.check_uptime(snapshot)
        if uptime_finding is not None:
            findings.append(uptime_finding)
        return findings
