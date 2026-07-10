from __future__ import annotations

import socket
import struct
from pathlib import Path

import psutil  # type: ignore[import-untyped]

from systemdna.models.network import (
    ListeningPort,
    NetworkInfo,
    NetworkInterface,
    RouteInfo,
)


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def get_interfaces() -> list[NetworkInterface]:
    interfaces: list[NetworkInterface] = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
    except Exception:
        return interfaces
    for name in addrs:
        mac: str | None = None
        ipv4: list[str] = []
        ipv6: list[str] = []
        for snic in addrs[name]:
            if snic.family == psutil.AF_LINK:
                mac = snic.address
            elif snic.family == socket.AF_INET:
                ipv4.append(snic.address)
            elif snic.family == socket.AF_INET6:
                ipv6.append(snic.address)
        stat = stats.get(name)
        interfaces.append(
            NetworkInterface(
                name=name,
                mac_address=mac,
                ipv4=ipv4,
                ipv6=ipv6,
                mtu=stat.mtu if stat else None,
                is_up=stat.isup if stat else False,
            )
        )
    return interfaces


def _hex_ip_to_str(hex_ip: str) -> str:
    try:
        raw = bytes.fromhex(hex_ip.zfill(8))[::-1]
        return ".".join(str(b) for b in raw)
    except (ValueError, AttributeError):
        return hex_ip


def _hex_ipv6_to_str(hex_ip: str) -> str:
    try:
        raw = bytes.fromhex(hex_ip)[:16]
        parts = [f"{raw[i]:02x}{raw[i+1]:02x}" for i in range(0, 16, 2)]
        return ":".join(parts)
    except (ValueError, AttributeError):
        return hex_ip


def _parse_proc_net_tcp(kind: str = "tcp") -> list[ListeningPort]:
    path = Path(f"/proc/net/{kind}")
    content = _read_file(path)
    if content is None:
        return []
    ports: list[ListeningPort] = []
    for line in content.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_addr = parts[1]
        state_hex = parts[3]
        try:
            state = int(state_hex, 16)
        except ValueError:
            continue
        if state != 0x0A:
            continue
        addr_part, _, port_hex = local_addr.partition(":")
        try:
            port = int(port_hex, 16)
        except ValueError:
            continue
        protocol = "tcp" if kind in ("tcp", "tcp6") else "udp"
        if kind.endswith("6"):
            address = _hex_ipv6_to_str(addr_part)
        else:
            address = _hex_ip_to_str(addr_part)
        ports.append(
            ListeningPort(
                protocol=protocol,
                port=port,
                address=address,
                pid=None,
                process=None,
            )
        )
    return ports


def _get_pids_from_connections() -> dict[tuple[str, int], int]:
    result: dict[tuple[str, int], int] = {}
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.status == "LISTEN":
                proto = "tcp" if conn.type == socket.SOCK_STREAM else "udp"
                key = (proto, conn.laddr.port)
                if key not in result and conn.pid:
                    result[key] = conn.pid
    except (psutil.AccessDenied, PermissionError):
        pass
    return result


def get_listening_ports() -> list[ListeningPort]:
    ports: list[ListeningPort] = []
    for kind in ("tcp", "tcp6", "udp", "udp6"):
        ports.extend(_parse_proc_net_tcp(kind))
    pid_map = _get_pids_from_connections()
    for p in ports:
        key = (p.protocol, p.port)
        pid = pid_map.get(key)
        if pid is not None:
            p.pid = pid
            try:
                proc = psutil.Process(pid)
                p.process = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return ports


def get_routes() -> list[RouteInfo]:
    content = _read_file(Path("/proc/net/route"))
    if content is None:
        return []
    routes: list[RouteInfo] = []
    for line in content.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue
        iface = parts[0]
        dest = parts[1]
        gateway = parts[2]
        mask = parts[7]
        try:
            dest_ip = socket.inet_ntoa(struct.pack("<I", int(dest, 16)))
            gw_ip = socket.inet_ntoa(struct.pack("<I", int(gateway, 16)))
            mask_ip = socket.inet_ntoa(struct.pack("<I", int(mask, 16)))
        except (ValueError, OSError):
            continue
        routes.append(
            RouteInfo(
                destination=dest_ip,
                gateway=gw_ip,
                netmask=mask_ip,
                interface=iface,
            )
        )
    return routes


def get_dns() -> list[str]:
    content = _read_file(Path("/etc/resolv.conf"))
    if content is None:
        return []
    servers: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("nameserver "):
            parts = stripped.split(None, 1)
            if len(parts) >= 2:
                servers.append(parts[1])
    return servers


def get_network_info() -> NetworkInfo:
    return NetworkInfo(
        hostname=socket.gethostname(),
        domain_name=None,
        dns_servers=get_dns(),
        interfaces=get_interfaces(),
        listening_ports=get_listening_ports(),
        routes=get_routes(),
    )
