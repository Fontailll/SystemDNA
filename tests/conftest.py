from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from systemdna.collectors.base import Collector, CollectorResult
from systemdna.core.config import ConfigManager
from systemdna.models.configuration import ConfigurationInfo, TrackedFile
from systemdna.models.doctor import Severity
from systemdna.models.hardware import CpuInfo, DiskInfo, HardwareInfo, MemoryInfo, SwapInfo
from systemdna.models.metadata import SnapshotMetadata
from systemdna.models.network import (
    ListeningPort,
    NetworkInfo,
    NetworkInterface,
    RouteInfo,
)
from systemdna.models.packages import PackageInfo, PackageManager, PackagesInfo
from systemdna.models.security import FirewallStatus, SecurityInfo
from systemdna.models.services import InitSystem, ServiceInfo, ServicesInfo
from systemdna.models.snapshot import Snapshot
from systemdna.models.system import SystemInfo
from systemdna.models.users import GroupInfo, UserInfo, UsersInfo
from systemdna.storage.manager import SnapshotStorageManager
from systemdna.version import __version__


@pytest.fixture
def sample_snapshot_data() -> Snapshot:
    return Snapshot(
        metadata=SnapshotMetadata(
            schema_version=1,
            application_version=__version__,
            created_at=datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
            platform="linux",
            hostname="test-host",
            duration_ms=1234,
            snapshot_id="abc12345",
            notes="test snapshot",
        ),
        system=SystemInfo(
            os_name="Linux",
            os_version="5.15.0-100-generic",
            distribution="Ubuntu",
            kernel="5.15.0-100-generic",
            architecture="x86_64",
            hostname="test-host",
            timezone="UTC",
            locale="en_US.UTF-8",
            python_version="3.11.4",
            machine_id="abcd1234machineid",
            boot_time=datetime(2025, 6, 15, 8, 0, 0, tzinfo=timezone.utc),
            uptime_seconds=9000.0,
        ),
        hardware=HardwareInfo(
            cpu=CpuInfo(
                model="Intel(R) Core(TM) i7-10750H",
                vendor="GenuineIntel",
                logical_cores=12,
                physical_cores=6,
                clock_speed_mhz=2600.0,
            ),
            memory=MemoryInfo(
                total_bytes=17179869184,
                available_bytes=8589934592,
                used_bytes=8589934592,
                percent=50.0,
            ),
            swap=SwapInfo(
                total_bytes=2147483648,
                used_bytes=0,
                free_bytes=2147483648,
                percent=0.0,
            ),
            disks=[
                DiskInfo(
                    device="/dev/sda1",
                    mount_point="/",
                    filesystem="ext4",
                    total_bytes=107374182400,
                    used_bytes=53687091200,
                    free_bytes=53687091200,
                    percent=50.0,
                ),
            ],
        ),
        network=NetworkInfo(
            hostname="test-host",
            domain_name="example.local",
            dns_servers=["8.8.8.8", "1.1.1.1"],
            interfaces=[
                NetworkInterface(
                    name="eth0",
                    mac_address="00:11:22:33:44:55",
                    ipv4=["192.168.1.100"],
                    ipv6=["fe80::211:22ff:fe33:4455"],
                    mtu=1500,
                    is_up=True,
                ),
            ],
            listening_ports=[
                ListeningPort(
                    protocol="tcp",
                    port=22,
                    address="0.0.0.0",
                    pid=1234,
                    process="sshd",
                ),
            ],
            routes=[
                RouteInfo(
                    destination="0.0.0.0",
                    gateway="192.168.1.1",
                    netmask="0.0.0.0",
                    interface="eth0",
                ),
            ],
        ),
        packages=PackagesInfo(
            managers=[
                PackageManager(
                    name="apt",
                    packages=[
                        PackageInfo(
                            name="curl",
                            version="7.81.0-1",
                            manager="apt",
                            repository="main",
                        ),
                        PackageInfo(
                            name="git",
                            version="2.34.1-1",
                            manager="apt",
                            repository="main",
                        ),
                    ],
                ),
            ],
        ),
        services=ServicesInfo(
            init_system=InitSystem(name="systemd"),
            services=[
                ServiceInfo(
                    name="sshd",
                    status="running",
                    enabled=True,
                    startup_type="auto",
                    pid=1234,
                    description="OpenSSH server",
                ),
                ServiceInfo(
                    name="cron",
                    status="running",
                    enabled=True,
                    startup_type="auto",
                    pid=5678,
                    description="Regular background program",
                ),
            ],
        ),
        users=UsersInfo(
            users=[
                UserInfo(
                    username="testuser",
                    uid=1000,
                    gid=1000,
                    groups=["testuser", "sudo"],
                    shell="/bin/bash",
                    home="/home/testuser",
                ),
            ],
            groups=[
                GroupInfo(
                    name="testuser",
                    gid=1000,
                    members=["testuser"],
                ),
                GroupInfo(
                    name="sudo",
                    gid=27,
                    members=["testuser"],
                ),
            ],
            current_user="testuser",
        ),
        security=SecurityInfo(
            firewall=FirewallStatus(
                enabled=True,
                name="ufw",
                rules_count=5,
            ),
            selinux_enforcing=False,
            apparmor_enforcing=True,
            kernel_lockdown="none",
            ssh_password_auth=False,
            ssh_root_login=False,
        ),
        configuration=ConfigurationInfo(
            tracked_files=[
                TrackedFile(
                    path="/etc/ssh/sshd_config",
                    hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                    size_bytes=3200,
                    modified_time="2025-06-01T12:00:00",
                    permissions="644",
                ),
            ],
        ),
    )


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    d = tmp_path / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def snapshot_storage(tmp_path: Path) -> SnapshotStorageManager:
    storage_dir = tmp_path / "snapshots"
    storage_dir.mkdir(parents=True, exist_ok=True)
    mgr = SnapshotStorageManager(storage_dir)

    import json

    snap1 = {
        "metadata": {
            "schema_version": 1,
            "application_version": "0.1.0",
            "created_at": "2025-06-15T10:00:00+00:00",
            "platform": "linux",
            "hostname": "host-a",
            "duration_ms": 500,
            "snapshot_id": "aaaaaa01",
        },
        "system": {
            "os_name": "Linux",
            "os_version": "5.15.0-100",
            "architecture": "x86_64",
            "hostname": "host-a",
            "timezone": "timezone.utc",
            "locale": "C",
            "python_version": "3.11",
        },
    }
    snap2 = {
        "metadata": {
            "schema_version": 1,
            "application_version": "0.1.0",
            "created_at": "2025-06-15T11:00:00+00:00",
            "platform": "linux",
            "hostname": "host-a",
            "duration_ms": 600,
            "snapshot_id": "aaaaaa02",
        },
        "system": {
            "os_name": "Linux",
            "os_version": "5.15.0-101",
            "architecture": "x86_64",
            "hostname": "host-a",
            "timezone": "timezone.utc",
            "locale": "C",
            "python_version": "3.11",
        },
    }

    for snap, ts, sid in [
        (snap1, "2025-06-15T10-00-00", "aaaaaa01"),
        (snap2, "2025-06-15T11-00-00", "aaaaaa02"),
    ]:
        fname = f"snapshot-{ts}-{sid}.json"
        (storage_dir / fname).write_text(json.dumps(snap), encoding="utf-8")

    return mgr


@pytest.fixture
def mock_collector() -> MagicMock:
    collector = MagicMock(spec=Collector)
    collector.name = "mock"
    collector.description = "Mock collector for testing"
    collector.collect.return_value = {"key": "value"}
    return collector


@pytest.fixture(autouse=True)
def disable_platform_calls() -> None:
    with (
        patch("systemdna.utils.system.platform") as mock_platform,
        patch("systemdna.utils.system.socket.gethostname", return_value="test-host"),
        patch("systemdna.utils.system.getpass.getuser", return_value="testuser"),
        patch("systemdna.utils.system.get_distribution", return_value=None),
    ):
        mock_platform.system.return_value = "Linux"
        mock_platform.release.return_value = "5.15.0-100-generic"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.python_version.return_value = "3.11.4"
        mock_platform.version.return_value = "10.0.19045"
        mock_platform.node.return_value = "test-host"
        yield
