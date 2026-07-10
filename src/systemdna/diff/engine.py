from __future__ import annotations

from systemdna.models.configuration import ConfigurationInfo
from systemdna.models.diff import DiffEntry, SectionDiff, SnapshotDiff
from systemdna.models.hardware import HardwareInfo
from systemdna.models.network import NetworkInfo
from systemdna.models.packages import PackagesInfo
from systemdna.models.security import SecurityInfo
from systemdna.models.services import ServiceInfo, ServicesInfo
from systemdna.models.snapshot import Snapshot
from systemdna.models.system import SystemInfo
from systemdna.models.users import UsersInfo


class DiffEngine:

    def compare(self, left: Snapshot, right: Snapshot) -> SnapshotDiff:
        sections = [
            SectionDiff(section="system", entries=self._compare_system(left.system, right.system)),
            SectionDiff(section="hardware", entries=self._compare_hardware(left.hardware, right.hardware)),
            SectionDiff(section="network", entries=self._compare_network(left.network, right.network)),
            SectionDiff(section="packages", entries=self._compare_packages(left.packages, right.packages)),
            SectionDiff(section="services", entries=self._compare_services(left.services, right.services)),
            SectionDiff(section="users", entries=self._compare_users(left.users, right.users)),
            SectionDiff(section="security", entries=self._compare_security(left.security, right.security)),
            SectionDiff(section="configuration", entries=self._compare_configuration(left.configuration, right.configuration)),
        ]

        total_added = 0
        total_removed = 0
        total_modified = 0
        for sec in sections:
            for entry in sec.entries:
                if entry.change_type == "added":
                    total_added += 1
                elif entry.change_type == "removed":
                    total_removed += 1
                elif entry.change_type == "modified":
                    total_modified += 1

        summary = {
            "total": total_added + total_removed + total_modified,
            "added": total_added,
            "removed": total_removed,
            "modified": total_modified,
        }

        return SnapshotDiff(
            left_id=left.metadata.snapshot_id,
            right_id=right.metadata.snapshot_id,
            left_time=left.metadata.created_at.isoformat(),
            right_time=right.metadata.created_at.isoformat(),
            sections=sections,
            summary=summary,
        )

    def _compare_system(self, left: SystemInfo, right: SystemInfo) -> list[DiffEntry]:
        if left == right:
            return []
        entries: list[DiffEntry] = []
        fields = [
            ("kernel", left.kernel, right.kernel),
            ("os_version", left.os_version, right.os_version),
            ("hostname", left.hostname, right.hostname),
            ("architecture", left.architecture, right.architecture),
            ("timezone", left.timezone, right.timezone),
        ]
        for path, old_val, new_val in fields:
            if old_val != new_val:
                entries.append(DiffEntry(
                    path=f"system.{path}",
                    change_type="modified",
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                ))
        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_hardware(self, left: HardwareInfo | None, right: HardwareInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        if left is None:
            if right is not None:
                if right.cpu:
                    entries.append(DiffEntry(path="hardware.cpu.model", change_type="added", new_value=right.cpu.model))
                    entries.append(DiffEntry(path="hardware.cpu.logical_cores", change_type="added", new_value=str(right.cpu.logical_cores)))
                for disk in right.disks:
                    entries.append(DiffEntry(path=f"hardware.disks.{disk.device}", change_type="added", new_value=f"{disk.mount_point} {disk.filesystem}"))
                if right.swap is not None:
                    entries.append(DiffEntry(path="hardware.swap.total_bytes", change_type="added", new_value=str(right.swap.total_bytes)))
            entries.sort(key=lambda e: e.path)
            return entries

        if right is None:
            if left.cpu:
                entries.append(DiffEntry(path="hardware.cpu.model", change_type="removed", old_value=left.cpu.model))
                entries.append(DiffEntry(path="hardware.cpu.logical_cores", change_type="removed", old_value=str(left.cpu.logical_cores)))
            for disk in left.disks:
                entries.append(DiffEntry(path=f"hardware.disks.{disk.device}", change_type="removed", old_value=f"{disk.mount_point} {disk.filesystem}"))
            if left.swap is not None:
                entries.append(DiffEntry(path="hardware.swap.total_bytes", change_type="removed", old_value=str(left.swap.total_bytes)))
            entries.sort(key=lambda e: e.path)
            return entries

        if left.cpu and right.cpu:
            if left.cpu.model != right.cpu.model:
                entries.append(DiffEntry(path="hardware.cpu.model", change_type="modified", old_value=left.cpu.model, new_value=right.cpu.model))
            if left.cpu.logical_cores != right.cpu.logical_cores:
                entries.append(DiffEntry(path="hardware.cpu.logical_cores", change_type="modified", old_value=str(left.cpu.logical_cores), new_value=str(right.cpu.logical_cores)))

        left_disks = {d.device: d for d in left.disks}
        right_disks = {d.device: d for d in right.disks}
        for dev in sorted(set(left_disks.keys()) | set(right_disks.keys())):
            if dev in left_disks and dev not in right_disks:
                d = left_disks[dev]
                entries.append(DiffEntry(path=f"hardware.disks.{dev}", change_type="removed", old_value=f"{d.mount_point} {d.filesystem}"))
            elif dev not in left_disks and dev in right_disks:
                d = right_disks[dev]
                entries.append(DiffEntry(path=f"hardware.disks.{dev}", change_type="added", new_value=f"{d.mount_point} {d.filesystem}"))
            else:
                ld = left_disks[dev]
                rd = right_disks[dev]
                if ld.mount_point != rd.mount_point or ld.filesystem != rd.filesystem or ld.total_bytes != rd.total_bytes:
                    entries.append(DiffEntry(path=f"hardware.disks.{dev}", change_type="modified", old_value=f"{ld.mount_point} {ld.filesystem}", new_value=f"{rd.mount_point} {rd.filesystem}"))

        if left.swap and right.swap and left.swap.total_bytes != right.swap.total_bytes:
            entries.append(DiffEntry(path="hardware.swap.total_bytes", change_type="modified", old_value=str(left.swap.total_bytes), new_value=str(right.swap.total_bytes)))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_network(self, left: NetworkInfo | None, right: NetworkInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        if left is None:
            if right is not None:
                for iface in right.interfaces:
                    entries.append(DiffEntry(path=f"network.interfaces.{iface.name}", change_type="added", new_value=iface.mac_address))
                if right.dns_servers:
                    entries.append(DiffEntry(path="network.dns_servers", change_type="added", new_value=",".join(right.dns_servers)))
                for port in right.listening_ports:
                    entries.append(DiffEntry(path=f"network.ports.{port.protocol}:{port.port}", change_type="added", new_value=port.address))
            entries.sort(key=lambda e: e.path)
            return entries

        if right is None:
            for iface in left.interfaces:
                entries.append(DiffEntry(path=f"network.interfaces.{iface.name}", change_type="removed", old_value=iface.mac_address))
            if left.dns_servers:
                entries.append(DiffEntry(path="network.dns_servers", change_type="removed", old_value=",".join(left.dns_servers)))
            for port in left.listening_ports:
                entries.append(DiffEntry(path=f"network.ports.{port.protocol}:{port.port}", change_type="removed", old_value=port.address))
            entries.sort(key=lambda e: e.path)
            return entries

        left_ifaces = {i.name: i for i in left.interfaces}
        right_ifaces = {i.name: i for i in right.interfaces}
        for name in sorted(set(left_ifaces.keys()) | set(right_ifaces.keys())):
            if name not in left_ifaces:
                iface = right_ifaces[name]
                entries.append(DiffEntry(path=f"network.interfaces.{name}", change_type="added", new_value=iface.mac_address))
            elif name not in right_ifaces:
                iface = left_ifaces[name]
                entries.append(DiffEntry(path=f"network.interfaces.{name}", change_type="removed", old_value=iface.mac_address))
            else:
                li = left_ifaces[name]
                ri = right_ifaces[name]
                if li.mac_address != ri.mac_address:
                    entries.append(DiffEntry(path=f"network.interfaces.{name}.mac", change_type="modified", old_value=li.mac_address, new_value=ri.mac_address))
                if li.ipv4 != ri.ipv4:
                    entries.append(DiffEntry(path=f"network.interfaces.{name}.ipv4", change_type="modified", old_value=",".join(li.ipv4), new_value=",".join(ri.ipv4)))
                if li.is_up != ri.is_up:
                    entries.append(DiffEntry(path=f"network.interfaces.{name}.is_up", change_type="modified", old_value=str(li.is_up), new_value=str(ri.is_up)))

        if left.dns_servers != right.dns_servers:
            entries.append(DiffEntry(path="network.dns_servers", change_type="modified", old_value=",".join(left.dns_servers), new_value=",".join(right.dns_servers)))

        left_ports = {(p.protocol, p.port, p.address) for p in left.listening_ports}
        right_ports = {(p.protocol, p.port, p.address) for p in right.listening_ports}
        for k in sorted(left_ports - right_ports):
            entries.append(DiffEntry(path=f"network.ports.{k[0]}:{k[1]}", change_type="removed", old_value=k[2]))
        for k in sorted(right_ports - left_ports):
            entries.append(DiffEntry(path=f"network.ports.{k[0]}:{k[1]}", change_type="added", new_value=k[2]))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_packages(self, left: PackagesInfo | None, right: PackagesInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        left_pkgs: dict[tuple[str, str], str] = {}
        if left is not None:
            for mgr in left.managers:
                for pkg in mgr.packages:
                    left_pkgs[(pkg.name, mgr.name)] = pkg.version

        right_pkgs: dict[tuple[str, str], str] = {}
        if right is not None:
            for mgr in right.managers:
                for pkg in mgr.packages:
                    right_pkgs[(pkg.name, mgr.name)] = pkg.version

        for key in sorted(set(left_pkgs.keys()) | set(right_pkgs.keys())):
            label = f"{key[0]} ({key[1]})"
            if key not in left_pkgs:
                entries.append(DiffEntry(path=f"packages.{label}", change_type="added", new_value=right_pkgs[key]))
            elif key not in right_pkgs:
                entries.append(DiffEntry(path=f"packages.{label}", change_type="removed", old_value=left_pkgs[key]))
            elif left_pkgs[key] != right_pkgs[key]:
                entries.append(DiffEntry(path=f"packages.{label}", change_type="modified", old_value=left_pkgs[key], new_value=right_pkgs[key]))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_services(self, left: ServicesInfo | None, right: ServicesInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        left_svcs: dict[str, ServiceInfo] = {}
        if left is not None:
            for s in left.services:
                left_svcs[s.name] = s

        right_svcs: dict[str, ServiceInfo] = {}
        if right is not None:
            for s in right.services:
                right_svcs[s.name] = s

        for name in sorted(set(left_svcs.keys()) | set(right_svcs.keys())):
            if name not in left_svcs:
                entries.append(DiffEntry(path=f"services.{name}", change_type="added", new_value=right_svcs[name].status))
            elif name not in right_svcs:
                entries.append(DiffEntry(path=f"services.{name}", change_type="removed", old_value=left_svcs[name].status))
            else:
                ls = left_svcs[name]
                rs = right_svcs[name]
                if ls.status != rs.status:
                    entries.append(DiffEntry(path=f"services.{name}.status", change_type="modified", old_value=ls.status, new_value=rs.status))
                if ls.enabled != rs.enabled:
                    entries.append(DiffEntry(path=f"services.{name}.enabled", change_type="modified", old_value=str(ls.enabled) if ls.enabled is not None else None, new_value=str(rs.enabled) if rs.enabled is not None else None))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_users(self, left: UsersInfo | None, right: UsersInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        left_users: dict[str, list[str]] = {}
        if left is not None:
            for u in left.users:
                left_users[u.username] = u.groups

        right_users: dict[str, list[str]] = {}
        if right is not None:
            for u in right.users:
                right_users[u.username] = u.groups

        for username in sorted(set(left_users.keys()) | set(right_users.keys())):
            if username not in left_users:
                entries.append(DiffEntry(path=f"users.{username}", change_type="added", new_value=",".join(right_users[username])))
            elif username not in right_users:
                entries.append(DiffEntry(path=f"users.{username}", change_type="removed", old_value=",".join(left_users[username])))
            else:
                old_groups = left_users[username]
                new_groups = right_users[username]
                if sorted(old_groups) != sorted(new_groups):
                    entries.append(DiffEntry(path=f"users.{username}.groups", change_type="modified", old_value=",".join(old_groups), new_value=",".join(new_groups)))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_security(self, left: SecurityInfo | None, right: SecurityInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        if left is None:
            if right is not None:
                if right.firewall is not None:
                    entries.append(DiffEntry(path="security.firewall.enabled", change_type="added", new_value=str(right.firewall.enabled)))
                if right.ssh_password_auth is not None:
                    entries.append(DiffEntry(path="security.ssh_password_auth", change_type="added", new_value=str(right.ssh_password_auth)))
                if right.ssh_root_login is not None:
                    entries.append(DiffEntry(path="security.ssh_root_login", change_type="added", new_value=str(right.ssh_root_login)))
            entries.sort(key=lambda e: e.path)
            return entries

        if right is None:
            if left.firewall is not None:
                entries.append(DiffEntry(path="security.firewall.enabled", change_type="removed", old_value=str(left.firewall.enabled)))
            if left.ssh_password_auth is not None:
                entries.append(DiffEntry(path="security.ssh_password_auth", change_type="removed", old_value=str(left.ssh_password_auth)))
            if left.ssh_root_login is not None:
                entries.append(DiffEntry(path="security.ssh_root_login", change_type="removed", old_value=str(left.ssh_root_login)))
            entries.sort(key=lambda e: e.path)
            return entries

        if left.firewall is not None and right.firewall is not None:
            if left.firewall.enabled != right.firewall.enabled:
                entries.append(DiffEntry(path="security.firewall.enabled", change_type="modified", old_value=str(left.firewall.enabled), new_value=str(right.firewall.enabled)))
            if left.firewall.name != right.firewall.name:
                entries.append(DiffEntry(path="security.firewall.name", change_type="modified", old_value=left.firewall.name, new_value=right.firewall.name))
        if left.ssh_password_auth != right.ssh_password_auth:
            entries.append(DiffEntry(path="security.ssh_password_auth", change_type="modified", old_value=str(left.ssh_password_auth), new_value=str(right.ssh_password_auth)))
        if left.ssh_root_login != right.ssh_root_login:
            entries.append(DiffEntry(path="security.ssh_root_login", change_type="modified", old_value=str(left.ssh_root_login), new_value=str(right.ssh_root_login)))

        entries.sort(key=lambda e: e.path)
        return entries

    def _compare_configuration(self, left: ConfigurationInfo | None, right: ConfigurationInfo | None) -> list[DiffEntry]:
        if left is None and right is None:
            return []
        entries: list[DiffEntry] = []

        left_files: dict[str, str] = {}
        if left is not None:
            for f in left.tracked_files:
                left_files[f.path] = f.hash

        right_files: dict[str, str] = {}
        if right is not None:
            for f in right.tracked_files:
                right_files[f.path] = f.hash

        for path in sorted(set(left_files.keys()) | set(right_files.keys())):
            if path not in left_files:
                entries.append(DiffEntry(path=f"configuration.files.{path}", change_type="added", new_value=right_files[path]))
            elif path not in right_files:
                entries.append(DiffEntry(path=f"configuration.files.{path}", change_type="removed", old_value=left_files[path]))
            elif left_files[path] != right_files[path]:
                entries.append(DiffEntry(path=f"configuration.files.{path}", change_type="modified", old_value=left_files[path], new_value=right_files[path]))

        entries.sort(key=lambda e: e.path)
        return entries
