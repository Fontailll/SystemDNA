from __future__ import annotations

from datetime import datetime, timezone

from systemdna.models.configuration import ConfigurationInfo, TrackedFile
from systemdna.models.hardware import CpuInfo, DiskInfo, HardwareInfo, MemoryInfo, SwapInfo
from systemdna.models.metadata import SnapshotMetadata
from systemdna.models.network import NetworkInfo, NetworkInterface
from systemdna.models.packages import PackageInfo, PackageManager, PackagesInfo
from systemdna.models.security import FirewallStatus, SecurityInfo
from systemdna.models.services import InitSystem, ServiceInfo, ServicesInfo
from systemdna.models.snapshot import Snapshot
from systemdna.models.system import SystemInfo
from systemdna.scoring.engine import ScoringEngine
from systemdna.scoring.models import HealthScore


def _base_metadata() -> SnapshotMetadata:
    return SnapshotMetadata(
        schema_version=1,
        application_version="0.1.0",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        platform="linux",
        hostname="test",
        duration_ms=100,
        snapshot_id="test-id",
    )


def _base_system() -> SystemInfo:
    return SystemInfo(
        os_name="Linux",
        os_version="1.0",
        architecture="x86_64",
        hostname="test",
        timezone="UTC",
        locale="C",
        python_version="3.13",
    )


def _tracked_file() -> TrackedFile:
    return TrackedFile(
        path="/etc/ssh/sshd_config",
        hash="a" * 64,
        size_bytes=3200,
        modified_time="2026-01-01T00:00:00",
        permissions="644",
    )


def _good_security(**overrides) -> SecurityInfo:
    defaults = dict(
        firewall=FirewallStatus(enabled=True, name="ufw", rules_count=5),
        selinux_enforcing=None,
        apparmor_enforcing=None,
        kernel_lockdown="integrity",
        ssh_password_auth=False,
        ssh_root_login=False,
    )
    defaults.update(overrides)
    return SecurityInfo(**defaults)


def _good_hardware(**overrides) -> HardwareInfo:
    defaults = dict(
        cpu=CpuInfo(model="Intel Core i7", vendor="Intel", logical_cores=8, physical_cores=4),
        memory=MemoryInfo(total_bytes=16 * 1024**3, available_bytes=8 * 1024**3, used_bytes=8 * 1024**3, percent=50.0),
        swap=SwapInfo(total_bytes=2 * 1024**3, used_bytes=0, free_bytes=2 * 1024**3, percent=0.0),
        disks=[DiskInfo(device="/dev/sda1", mount_point="/", filesystem="ext4", total_bytes=100 * 1024**3, used_bytes=50 * 1024**3, free_bytes=50 * 1024**3, percent=50.0)],
    )
    defaults.update(overrides)
    return HardwareInfo(**defaults)


def _good_network(**overrides) -> NetworkInfo:
    defaults = dict(
        hostname="test",
        domain_name="example.com",
        dns_servers=["8.8.8.8", "1.1.1.1"],
        interfaces=[NetworkInterface(name="eth0", mac_address="00:11:22:33:44:55", ipv4=["192.168.1.1"], mtu=1500, is_up=True)],
    )
    defaults.update(overrides)
    return NetworkInfo(**defaults)


def _good_packages(**overrides) -> PackagesInfo:
    defaults = dict(
        managers=[
            PackageManager(name="apt", packages=[
                PackageInfo(name="curl", version="7.0", manager="apt"),
            ]),
        ],
    )
    defaults.update(overrides)
    return PackagesInfo(**defaults)


def _good_services(**overrides) -> ServicesInfo:
    defaults = dict(
        init_system=InitSystem(name="systemd"),
        services=[
            ServiceInfo(name="sshd", status="running", enabled=True),
        ],
    )
    defaults.update(overrides)
    return ServicesInfo(**defaults)


def _good_configuration() -> ConfigurationInfo:
    return ConfigurationInfo(tracked_files=[_tracked_file()])


def _perfect_snapshot() -> Snapshot:
    return Snapshot(
        metadata=_base_metadata(),
        system=_base_system(),
        hardware=_good_hardware(),
        network=_good_network(),
        packages=_good_packages(),
        services=_good_services(),
        configuration=_good_configuration(),
        security=_good_security(),
    )


def test_perfect_snapshot_scores_100() -> None:
    snapshot = _perfect_snapshot()
    engine = ScoringEngine()
    health = engine.score(snapshot)
    assert health.overall_score == 100
    assert health.findings_count == 0


def test_no_firewall_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.security.firewall = None
    engine = ScoringEngine()
    health = engine.score(snapshot)
    security_cat = next(c for c in health.categories if c.category.value == "security")
    assert security_cat.score < 40
    assert any(f.title == "No firewall detected" for f in security_cat.findings)


def test_ssh_password_auth_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.security.ssh_password_auth = True
    engine = ScoringEngine()
    health = engine.score(snapshot)
    security_cat = next(c for c in health.categories if c.category.value == "security")
    assert security_cat.score < 40
    assert any("SSH password" in f.title for f in security_cat.findings)


def test_ssh_root_login_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.security.ssh_root_login = True
    engine = ScoringEngine()
    health = engine.score(snapshot)
    security_cat = next(c for c in health.categories if c.category.value == "security")
    assert security_cat.score < 40
    assert any("root login" in f.title for f in security_cat.findings)


def test_no_swap_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.hardware.swap = SwapInfo(total_bytes=0, used_bytes=0, free_bytes=0, percent=0.0)
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("swap" in f.title.lower() for f in hygiene_cat.findings)


def test_full_disk_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.hardware.disks = [
        DiskInfo(device="/dev/sda1", mount_point="/", filesystem="ext4",
                 total_bytes=100 * 1024**3, used_bytes=98 * 1024**3,
                 free_bytes=2 * 1024**3, percent=98.0),
    ]
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("critically full" in f.title for f in hygiene_cat.findings)


def test_no_dns_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.network.dns_servers = []
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("DNS" in f.title for f in hygiene_cat.findings)


def test_failed_services_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.services.services = [
        ServiceInfo(name="sshd", status="running", enabled=True),
        ServiceInfo(name="nginx", status="failed", enabled=True),
        ServiceInfo(name="redis", status="inactive", enabled=False),
    ]
    engine = ScoringEngine()
    health = engine.score(snapshot)
    services_cat = next(c for c in health.categories if c.category.value == "services")
    assert services_cat.score < 15
    assert len(services_cat.findings) > 0


def test_excessive_packages_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    many_packages = [PackageInfo(name=f"pkg-{i}", version="1.0", manager="apt") for i in range(3001)]
    snapshot.packages = PackagesInfo(
        managers=[PackageManager(name="apt", packages=many_packages)],
    )
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("Excessive packages" in f.title for f in hygiene_cat.findings)


def test_multiple_package_managers_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.packages = PackagesInfo(
        managers=[
            PackageManager(name="apt", packages=[PackageInfo(name="a", version="1", manager="apt")]),
            PackageManager(name="yum", packages=[PackageInfo(name="b", version="1", manager="yum")]),
            PackageManager(name="snap", packages=[PackageInfo(name="c", version="1", manager="snap")]),
        ],
    )
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("Multiple package managers" in f.title for f in hygiene_cat.findings)


def test_old_kernels_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.packages = PackagesInfo(
        managers=[
            PackageManager(name="apt", packages=[
                PackageInfo(name="linux-image-5.15.0-100-generic", version="5.15.0-100", manager="apt"),
                PackageInfo(name="linux-image-5.15.0-99-generic", version="5.15.0-99", manager="apt"),
            ]),
        ],
    )
    engine = ScoringEngine()
    health = engine.score(snapshot)
    hygiene_cat = next(c for c in health.categories if c.category.value == "hygiene")
    assert hygiene_cat.score < 30
    assert any("kernel" in f.title.lower() for f in hygiene_cat.findings)


def test_high_uptime_deducts_points() -> None:
    snapshot = _perfect_snapshot()
    snapshot.system.uptime_seconds = 100 * 86400.0
    engine = ScoringEngine()
    health = engine.score(snapshot)
    config_cat = next(c for c in health.categories if c.category.value == "configuration")
    assert config_cat.score < 15
    assert any("uptime" in f.title.lower() for f in config_cat.findings)


def test_health_score_str_includes_score() -> None:
    snapshot = _perfect_snapshot()
    engine = ScoringEngine()
    health = engine.score(snapshot)
    text = str(health)
    assert "100" in text


def test_score_never_below_zero() -> None:
    snapshot = Snapshot(
        metadata=_base_metadata(),
        system=SystemInfo(
            os_name="Linux",
            os_version="1.0",
            architecture="x86_64",
            hostname="test",
            timezone="UTC",
            locale="C",
            python_version="3.13",
            uptime_seconds=200 * 86400.0,
        ),
        hardware=HardwareInfo(
            disks=[DiskInfo(device="/dev/sda1", mount_point="/", filesystem="ext4",
                            total_bytes=100 * 1024**3, used_bytes=99 * 1024**3,
                            free_bytes=1 * 1024**3, percent=99.0)],
        ),
        network=NetworkInfo(hostname="test", dns_servers=[]),
        packages=PackagesInfo(managers=[
            PackageManager(name="apt", packages=[
                PackageInfo(name=f"pkg-{i}", version="1.0", manager="apt") for i in range(4000)
            ]),
            PackageManager(name="yum", packages=[]),
            PackageManager(name="snap", packages=[]),
            PackageManager(name="dnf", packages=[]),
        ]),
        services=ServicesInfo(
            init_system=None,
            services=[
                ServiceInfo(name=f"svc-{i}", status="failed") for i in range(10)
            ],
        ),
        security=SecurityInfo(
            firewall=None,
            ssh_password_auth=True,
            ssh_root_login=True,
            selinux_enforcing=False,
            apparmor_enforcing=False,
        ),
        configuration=None,
    )
    engine = ScoringEngine()
    health = engine.score(snapshot)
    assert health.overall_score >= 0


def test_empty_snapshot_handling() -> None:
    snapshot = Snapshot(
        metadata=_base_metadata(),
        system=_base_system(),
    )
    engine = ScoringEngine()
    health = engine.score(snapshot)
    assert health.overall_score >= 0
    assert health.overall_score <= 100
    assert isinstance(health, HealthScore)
