from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

import orjson

from systemdna.models.configuration import ConfigurationInfo, TrackedFile
from systemdna.models.diff import DiffEntry, SectionDiff, SnapshotDiff
from systemdna.models.doctor import DoctorReport, Recommendation, Severity
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


def test_metadata_creates_default_uuid() -> None:
    m1 = SnapshotMetadata(
        schema_version=1,
        application_version="0.1.0",
        platform="linux",
        hostname="h1",
        duration_ms=100,
    )
    m2 = SnapshotMetadata(
        schema_version=1,
        application_version="0.1.0",
        platform="linux",
        hostname="h2",
        duration_ms=200,
    )
    assert m1.snapshot_id != m2.snapshot_id
    assert uuid.UUID(m1.snapshot_id)


def test_metadata_accepts_explicit_id() -> None:
    m = SnapshotMetadata(
        schema_version=1,
        application_version="0.1.0",
        platform="linux",
        hostname="h1",
        duration_ms=100,
        snapshot_id="my-custom-id",
    )
    assert m.snapshot_id == "my-custom-id"


def test_metadata_field_defaults() -> None:
    m = SnapshotMetadata(
        schema_version=1,
        application_version="0.1.0",
        platform="linux",
        hostname="h1",
        duration_ms=100,
    )
    assert m.notes is None
    assert isinstance(m.created_at, datetime)
    assert isinstance(m.snapshot_id, str)


def test_system_info_all_fields() -> None:
    dt = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    s = SystemInfo(
        os_name="Linux",
        os_version="5.15.0-100",
        distribution="Ubuntu",
        kernel="5.15.0-100-generic",
        architecture="x86_64",
        hostname="test",
        timezone="timezone.utc",
        locale="C",
        python_version="3.11",
        machine_id="abc",
        boot_time=dt,
        uptime_seconds=12345.0,
    )
    assert s.os_name == "Linux"
    assert s.boot_time == dt
    assert s.uptime_seconds == 12345.0


def test_hardware_info_nested_models() -> None:
    cpu = CpuInfo(model="M1", vendor="Apple", logical_cores=8, physical_cores=8, clock_speed_mhz=3200.0)
    mem = MemoryInfo(total_bytes=1, available_bytes=1, used_bytes=0, percent=0.0)
    swap = SwapInfo(total_bytes=1, used_bytes=0, free_bytes=1, percent=0.0)
    disk = DiskInfo(
        device="/dev/sda", mount_point="/", filesystem="ext4",
        total_bytes=100, used_bytes=50, free_bytes=50, percent=50.0,
    )
    hw = HardwareInfo(cpu=cpu, memory=mem, swap=swap, disks=[disk])
    assert hw.cpu is not None
    assert hw.cpu.model == "M1"
    assert hw.memory is not None
    assert len(hw.disks) == 1
    assert hw.disks[0].device == "/dev/sda"


def test_packages_info() -> None:
    pkg = PackageInfo(name="nginx", version="1.18", manager="apt", repository="main")
    mgr = PackageManager(name="apt", packages=[pkg])
    pkgs = PackagesInfo(managers=[mgr])
    assert len(pkgs.managers) == 1
    assert pkgs.managers[0].packages[0].name == "nginx"


def test_services_info() -> None:
    svc = ServiceInfo(name="nginx", status="running", enabled=True, startup_type="auto", pid=123, description="web")
    init = InitSystem(name="systemd")
    svcs = ServicesInfo(init_system=init, services=[svc])
    assert svcs.init_system is not None
    assert svcs.init_system.name == "systemd"
    assert svcs.services[0].name == "nginx"


def test_network_info() -> None:
    iface = NetworkInterface(
        name="eth0", mac_address="aa:bb:cc:dd:ee:ff",
        ipv4=["10.0.0.1"], ipv6=["::1"], mtu=1500, is_up=True,
    )
    port = ListeningPort(protocol="tcp", port=80, address="0.0.0.0", pid=1, process="nginx")
    route = RouteInfo(destination="0.0.0.0", gateway="10.0.0.1", netmask="0.0.0.0", interface="eth0")
    net = NetworkInfo(
        hostname="test", domain_name="local", dns_servers=["8.8.8.8"],
        interfaces=[iface], listening_ports=[port], routes=[route],
    )
    assert len(net.interfaces) == 1
    assert net.interfaces[0].name == "eth0"
    assert net.listening_ports[0].port == 80
    assert net.routes[0].gateway == "10.0.0.1"


def test_users_info() -> None:
    user = UserInfo(username="alice", uid=1001, gid=1001, groups=["alice"], shell="/bin/zsh", home="/home/alice")
    group = GroupInfo(name="alice", gid=1001, members=["alice"])
    users = UsersInfo(users=[user], groups=[group], current_user="alice")
    assert users.current_user == "alice"
    assert users.users[0].username == "alice"
    assert users.groups[0].name == "alice"


def test_security_info() -> None:
    fw = FirewallStatus(enabled=True, name="ufw", rules_count=5)
    sec = SecurityInfo(
        firewall=fw, selinux_enforcing=False, apparmor_enforcing=True,
        kernel_lockdown="none", ssh_password_auth=False, ssh_root_login=False,
    )
    assert sec.firewall is not None
    assert sec.firewall.enabled is True
    assert sec.selinux_enforcing is False
    assert sec.ssh_password_auth is False


def test_configuration_info() -> None:
    tf = TrackedFile(
        path="/etc/hosts",
        hash="a" * 64,
        size_bytes=200,
        modified_time="2025-01-01T00:00:00",
        permissions="644",
    )
    cfg = ConfigurationInfo(tracked_files=[tf])
    assert len(cfg.tracked_files) == 1
    assert cfg.tracked_files[0].path == "/etc/hosts"


def test_diff_models() -> None:
    entry = DiffEntry(path="system.kernel", change_type="modified", old_value="5.15", new_value="6.0")
    sd = SectionDiff(section="system", entries=[entry])
    diff = SnapshotDiff(
        left_id="left", right_id="right",
        left_time="2025-01-01", right_time="2025-01-02",
        sections=[sd], summary={"total": 1, "modified": 1},
    )
    assert diff.left_id == "left"
    assert diff.right_id == "right"
    assert diff.sections[0].section == "system"
    assert diff.sections[0].entries[0].change_type == "modified"
    assert diff.summary["total"] == 1


def test_diff_entry_types() -> None:
    for ct in ("added", "removed", "modified"):
        e = DiffEntry(path="x", change_type=ct)  # type: ignore[arg-type]
        assert e.change_type == ct


def test_doctor_models() -> None:
    rec = Recommendation(
        severity=Severity.WARNING,
        title="Firewall disabled",
        description="The firewall is not enabled",
        suggested_fix="Enable ufw",
        reference="https://example.com",
    )
    report = DoctorReport(
        snapshot_id="abc123",
        timestamp="2025-01-01T00:00:00",
        recommendations=[rec],
        summary={"warning": 1},
    )
    assert rec.severity == Severity.WARNING
    assert rec.severity.value == "warning"
    assert report.snapshot_id == "abc123"
    assert report.summary["warning"] == 1


def test_severity_enum_values() -> None:
    assert Severity.INFO.value == "info"
    assert Severity.WARNING.value == "warning"
    assert Severity.ERROR.value == "error"


def test_serialization_roundtrip(sample_snapshot_data: Snapshot) -> None:
    raw = sample_snapshot_data.model_dump(mode="json")
    serialized = orjson.dumps(raw)
    deserialized = orjson.loads(serialized)
    restored = Snapshot(**deserialized)
    assert restored.metadata.snapshot_id == sample_snapshot_data.metadata.snapshot_id
    assert restored.system.kernel == sample_snapshot_data.system.kernel
    assert restored.hardware is not None
    assert restored.hardware.cpu is not None
    assert restored.hardware.cpu.model == sample_snapshot_data.hardware.cpu.model
    assert restored.packages is not None
    assert len(restored.packages.managers) == 1
    assert restored.network is not None
    assert len(restored.network.interfaces) == 1
    assert restored.services is not None
    assert len(restored.services.services) == 2
    assert restored.users is not None
    assert len(restored.users.users) == 1
    assert restored.security is not None
    assert restored.security.firewall is not None
    assert restored.configuration is not None
    assert len(restored.configuration.tracked_files) == 1


def test_optional_sections_can_be_none() -> None:
    snap = Snapshot(
        metadata=SnapshotMetadata(
            schema_version=1, application_version="0.1.0",
            platform="linux", hostname="h", duration_ms=0,
        ),
        system=SystemInfo(
            os_name="L", os_version="1", architecture="x86",
            hostname="h", timezone="U", locale="C", python_version="3",
        ),
    )
    assert snap.hardware is None
    assert snap.network is None
    assert snap.packages is None
    assert snap.services is None
    assert snap.users is None
    assert snap.security is None
    assert snap.configuration is None


def test_float_nan_serialization_uses_ser_json_supersets() -> None:
    hw = HardwareInfo(
        cpu=CpuInfo(model="x", vendor="y", logical_cores=1),
        memory=MemoryInfo(total_bytes=1, available_bytes=1, used_bytes=1, percent=50.0),
    )
    raw = hw.model_dump(mode="json")
    serialized = orjson.dumps(raw)
    deserialized = orjson.loads(serialized)
    restored = HardwareInfo(**deserialized)
    assert restored.memory is not None
    assert restored.memory.percent == 50.0
