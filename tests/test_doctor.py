from __future__ import annotations

from datetime import datetime, timezone

import pytest

from systemdna.doctor.engine import DoctorEngine
from systemdna.models.configuration import ConfigurationInfo
from systemdna.models.doctor import Severity
from systemdna.models.hardware import DiskInfo, HardwareInfo, SwapInfo
from systemdna.models.metadata import SnapshotMetadata
from systemdna.models.network import NetworkInfo
from systemdna.models.packages import PackageInfo, PackageManager, PackagesInfo
from systemdna.models.security import FirewallStatus, SecurityInfo
from systemdna.models.services import InitSystem, ServicesInfo
from systemdna.models.snapshot import Snapshot
from systemdna.models.system import SystemInfo


def _make_snapshot(
    hardware: HardwareInfo | None = None,
    security: SecurityInfo | None = None,
    packages: PackagesInfo | None = None,
    services: ServicesInfo | None = None,
    network: NetworkInfo | None = None,
) -> Snapshot:
    return Snapshot(
        metadata=SnapshotMetadata(
            schema_version=1,
            application_version="0.1.0",
            created_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            platform="linux",
            hostname="test",
            duration_ms=100,
            snapshot_id="test-id",
        ),
        system=SystemInfo(
            os_name="Linux",
            os_version="1",
            architecture="x86_64",
            hostname="test",
            timezone="UTC",
            locale="C",
            python_version="3.11",
        ),
        hardware=hardware,
        security=security,
        packages=packages,
        services=services,
        network=network,
    )


def test_healthy_snapshot_no_recommendations() -> None:
    healthy = _make_snapshot(
        security=SecurityInfo(
            firewall=FirewallStatus(enabled=True, name="ufw"),
            ssh_password_auth=False,
            ssh_root_login=False,
        ),
        hardware=HardwareInfo(
            disks=[DiskInfo(
                device="/dev/sda", mount_point="/", filesystem="ext4",
                total_bytes=100000, used_bytes=50000, free_bytes=50000, percent=50.0,
            )],
            swap=SwapInfo(total_bytes=2048, used_bytes=0, free_bytes=2048, percent=0.0),
        ),
        packages=PackagesInfo(managers=[
            PackageManager(name="apt", packages=[
                PackageInfo(name="a", version="1", manager="apt"),
            ]),
        ]),
        services=ServicesInfo(init_system=InitSystem(name="systemd")),
        network=NetworkInfo(hostname="test", dns_servers=["8.8.8.8"]),
    )
    engine = DoctorEngine()
    report = engine.analyze(healthy)
    assert len(report.recommendations) == 0
    assert report.summary == {}


def test_firewall_disabled_rule() -> None:
    snap = _make_snapshot(
        security=SecurityInfo(
            firewall=FirewallStatus(enabled=False, name="ufw"),
            ssh_password_auth=False,
            ssh_root_login=False,
        ),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("firewall" in t.lower() for t in titles)


def test_firewall_none_triggers_unknown() -> None:
    snap = _make_snapshot(security=SecurityInfo())
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("unknown" in t.lower() for t in titles)


def test_ssh_password_auth_rule() -> None:
    snap = _make_snapshot(
        security=SecurityInfo(ssh_password_auth=True),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("password" in t.lower() for t in titles)


def test_ssh_password_auth_none_skips() -> None:
    snap = _make_snapshot(security=SecurityInfo(firewall=FirewallStatus(enabled=True)))
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert not any("password" in t.lower() for t in titles)


def test_swap_disabled_rule() -> None:
    snap = _make_snapshot(
        hardware=HardwareInfo(swap=SwapInfo(total_bytes=0, used_bytes=0, free_bytes=0, percent=0.0)),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("swap" in t.lower() for t in titles)


def test_swap_none_triggers_rule() -> None:
    snap = _make_snapshot(
        hardware=HardwareInfo(),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("swap" in t.lower() for t in titles)


def test_low_disk_space_rule() -> None:
    snap = _make_snapshot(
        hardware=HardwareInfo(
            disks=[DiskInfo(
                device="/dev/sda", mount_point="/", filesystem="ext4",
                total_bytes=100, used_bytes=95, free_bytes=5, percent=95.0,
            )],
        ),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("disk" in t.lower() for t in titles)


def test_low_disk_space_no_disk_skips() -> None:
    snap = _make_snapshot(
        hardware=HardwareInfo(),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert not any("disk" in t.lower() for t in titles)


def test_multiple_package_managers_rule() -> None:
    snap = _make_snapshot(
        packages=PackagesInfo(managers=[
            PackageManager(name="apt"),
            PackageManager(name="snap"),
            PackageManager(name="flatpak"),
        ]),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("package manager" in t.lower() for t in titles)


def test_recommendations_have_proper_severity() -> None:
    snap = _make_snapshot(
        security=SecurityInfo(
            firewall=FirewallStatus(enabled=False),
            ssh_password_auth=True,
            ssh_root_login=True,
        ),
        hardware=HardwareInfo(swap=SwapInfo(total_bytes=0, used_bytes=0, free_bytes=0, percent=0.0)),
        services=ServicesInfo(),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    for rec in report.recommendations:
        assert isinstance(rec.severity, Severity)
        assert rec.severity in (Severity.INFO, Severity.WARNING, Severity.ERROR)


def test_no_init_detected_error() -> None:
    snap = _make_snapshot(
        services=ServicesInfo(),
        security=SecurityInfo(firewall=FirewallStatus(enabled=True), ssh_password_auth=False),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    titles = [r.title for r in report.recommendations]
    assert any("init" in t.lower() for t in titles)


def test_report_contains_snapshot_id() -> None:
    snap = _make_snapshot(
        security=SecurityInfo(firewall=FirewallStatus(enabled=False)),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    assert report.snapshot_id == "test-id"
    assert report.timestamp is not None


def test_report_summary_counts() -> None:
    snap = _make_snapshot(
        security=SecurityInfo(
            firewall=FirewallStatus(enabled=False),
            ssh_password_auth=True,
        ),
        hardware=HardwareInfo(swap=SwapInfo(total_bytes=0, used_bytes=0, free_bytes=0, percent=0.0)),
        services=ServicesInfo(),
    )
    engine = DoctorEngine()
    report = engine.analyze(snap)
    total = sum(report.summary.values())
    assert total == len(report.recommendations)
