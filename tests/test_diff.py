from __future__ import annotations

from datetime import datetime, timezone

from systemdna.diff.engine import DiffEngine
from systemdna.models.configuration import ConfigurationInfo, TrackedFile
from systemdna.models.diff import SnapshotDiff
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


def _make_snapshot(
    snapshot_id: str = "id1",
    kernel: str = "5.15.0-100",
    hostname: str = "host-a",
    created_at: datetime | None = None,
) -> Snapshot:
    if created_at is None:
        created_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return Snapshot(
        metadata=SnapshotMetadata(
            schema_version=1,
            application_version="0.1.0",
            created_at=created_at,
            platform="linux",
            hostname=hostname,
            duration_ms=100,
            snapshot_id=snapshot_id,
        ),
        system=SystemInfo(
            os_name="Linux",
            os_version="5.15.0-100-generic",
            distribution="Ubuntu",
            kernel=kernel,
            architecture="x86_64",
            hostname=hostname,
            timezone="UTC",
            locale="C",
            python_version="3.11",
        ),
    )


def test_identical_snapshots_no_changes() -> None:
    left = _make_snapshot("id1", kernel="5.15.0-100")
    right = _make_snapshot("id2", kernel="5.15.0-100")
    engine = DiffEngine()
    result = engine.compare(left, right)
    assert isinstance(result, SnapshotDiff)
    assert result.summary["total"] == 0
    assert result.summary["added"] == 0
    assert result.summary["removed"] == 0
    assert result.summary["modified"] == 0


def test_different_kernel_version() -> None:
    left = _make_snapshot("id1", kernel="5.15.0-100")
    right = _make_snapshot("id2", kernel="6.0.0-1")
    engine = DiffEngine()
    result = engine.compare(left, right)
    assert result.summary["total"] == 1
    assert result.summary["modified"] == 1
    sys_sec = [s for s in result.sections if s.section == "system"]
    assert len(sys_sec) == 1
    assert sys_sec[0].entries[0].path == "system.kernel"


def test_added_packages() -> None:
    left = _make_snapshot("id1")
    right = _make_snapshot("id2")
    right.packages = PackagesInfo(
        managers=[
            PackageManager(
                name="apt",
                packages=[PackageInfo(name="curl", version="1.0", manager="apt")],
            ),
        ],
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    pkg_sec = [s for s in result.sections if s.section == "packages"]
    assert len(pkg_sec) == 1
    assert any(e.change_type == "added" for e in pkg_sec[0].entries)


def test_removed_services() -> None:
    left = _make_snapshot("id1")
    left.services = ServicesInfo(
        init_system=InitSystem(name="systemd"),
        services=[ServiceInfo(name="nginx", status="running", enabled=True)],
    )
    right = _make_snapshot("id2")
    right.services = ServicesInfo(
        init_system=InitSystem(name="systemd"),
        services=[],
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    svc_sec = [s for s in result.sections if s.section == "services"]
    assert len(svc_sec) == 1
    assert any(e.change_type == "removed" for e in svc_sec[0].entries)


def test_modified_configuration_files() -> None:
    left = _make_snapshot("id1")
    left.configuration = ConfigurationInfo(
        tracked_files=[
            TrackedFile(path="/etc/hosts", hash="oldhash", size_bytes=100),
        ],
    )
    right = _make_snapshot("id2")
    right.configuration = ConfigurationInfo(
        tracked_files=[
            TrackedFile(path="/etc/hosts", hash="newhash", size_bytes=100),
        ],
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    cfg_sec = [s for s in result.sections if s.section == "configuration"]
    assert len(cfg_sec) == 1
    assert any(e.change_type == "modified" for e in cfg_sec[0].entries)


def test_hardware_memory_change() -> None:
    left = _make_snapshot("id1")
    left.hardware = HardwareInfo(
        cpu=CpuInfo(model="Intel", vendor="GenuineIntel", logical_cores=4),
        memory=MemoryInfo(total_bytes=8192, available_bytes=4096, used_bytes=4096, percent=50.0),
    )
    right = _make_snapshot("id2")
    right.hardware = HardwareInfo(
        cpu=CpuInfo(model="Intel", vendor="GenuineIntel", logical_cores=8),
        memory=MemoryInfo(total_bytes=16384, available_bytes=8192, used_bytes=8192, percent=50.0),
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    hw_sec = [s for s in result.sections if s.section == "hardware"]
    assert len(hw_sec) == 1
    cpu_entries = [e for e in hw_sec[0].entries if "cpu" in e.path]
    assert len(cpu_entries) > 0


def test_hardware_disk_added() -> None:
    left = _make_snapshot("id1")
    left.hardware = HardwareInfo(disks=[])
    right = _make_snapshot("id2")
    right.hardware = HardwareInfo(
        disks=[DiskInfo(
            device="/dev/sdb", mount_point="/data", filesystem="ext4",
            total_bytes=1000, used_bytes=500, free_bytes=500, percent=50.0,
        )],
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    hw_sec = [s for s in result.sections if s.section == "hardware"]
    assert any(e.change_type == "added" and "disks" in e.path for e in hw_sec[0].entries)


def test_summary_counts_correct() -> None:
    left = _make_snapshot("id1")
    left.packages = PackagesInfo(
        managers=[PackageManager(
            name="apt",
            packages=[PackageInfo(name="pkg1", version="1.0", manager="apt")],
        )],
    )
    left.services = ServicesInfo(
        init_system=InitSystem(name="systemd"),
        services=[ServiceInfo(name="svc1", status="running", enabled=True)],
    )
    left.configuration = ConfigurationInfo(
        tracked_files=[TrackedFile(path="/etc/a", hash="aaa", size_bytes=10)],
    )

    right = _make_snapshot("id2")
    right.system.os_version = "6.0.0-1-generic"
    right.system.kernel = "6.0.0-1"

    engine = DiffEngine()
    result = engine.compare(left, right)
    assert result.summary["removed"] >= 2
    assert result.summary["added"] == 0
    assert result.summary["modified"] >= 2
    assert result.summary["total"] == result.summary["added"] + result.summary["removed"] + result.summary["modified"]


def test_diff_metadata_ids() -> None:
    left = _make_snapshot("left-id")
    right = _make_snapshot("right-id")
    engine = DiffEngine()
    result = engine.compare(left, right)
    assert result.left_id == "left-id"
    assert result.right_id == "right-id"
    assert "left_time" in result.model_dump()
    assert "right_time" in result.model_dump()


def test_none_sections_handled() -> None:
    left = _make_snapshot("id1")
    right = _make_snapshot("id2")
    engine = DiffEngine()
    result = engine.compare(left, right)
    for sec in result.sections:
        if sec.section == "hardware":
            assert sec.entries == []
        if sec.section == "network":
            assert sec.entries == []


def test_security_changes() -> None:
    left = _make_snapshot("id1")
    left.security = SecurityInfo(firewall=FirewallStatus(enabled=True, name="ufw"), ssh_password_auth=True)
    right = _make_snapshot("id2")
    right.security = SecurityInfo(firewall=FirewallStatus(enabled=False, name="ufw"), ssh_password_auth=False)
    engine = DiffEngine()
    result = engine.compare(left, right)
    sec_sec = [s for s in result.sections if s.section == "security"]
    assert len(sec_sec) == 1
    assert any(e.change_type == "modified" for e in sec_sec[0].entries)


def test_user_changes() -> None:
    left = _make_snapshot("id1")
    left.users = UsersInfo(
        users=[UserInfo(username="alice", uid=1000, gid=1000)],
        groups=[GroupInfo(name="alice", gid=1000)],
        current_user="alice",
    )
    right = _make_snapshot("id2")
    right.users = UsersInfo(
        users=[UserInfo(username="bob", uid=1001, gid=1001)],
        groups=[GroupInfo(name="bob", gid=1001)],
        current_user="bob",
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    usr_sec = [s for s in result.sections if s.section == "users"]
    assert len(usr_sec) == 1
    entries = usr_sec[0].entries
    assert any(e.change_type == "removed" for e in entries)
    assert any(e.change_type == "added" for e in entries)


def test_network_interface_changes() -> None:
    left = _make_snapshot("id1")
    left.network = NetworkInfo(
        hostname="h",
        interfaces=[NetworkInterface(name="eth0", mac_address="aa:bb", is_up=True)],
    )
    right = _make_snapshot("id2")
    right.network = NetworkInfo(
        hostname="h",
        interfaces=[NetworkInterface(name="eth0", mac_address="cc:dd", is_up=False)],
    )
    engine = DiffEngine()
    result = engine.compare(left, right)
    net_sec = [s for s in result.sections if s.section == "network"]
    assert len(net_sec) == 1
    assert any(e.change_type == "modified" for e in net_sec[0].entries)
