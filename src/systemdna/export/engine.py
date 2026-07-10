from __future__ import annotations

from pathlib import Path

import orjson

from systemdna.core.exceptions import ExportError
from systemdna.models.snapshot import Snapshot
from systemdna.version import __version__

_KIB = 1024.0
_BYTE_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")


def _format_bytes(n: int | float) -> str:
    for unit in _BYTE_UNITS:
        if abs(n) < _KIB:
            return f"{n:.1f} {unit}"
        n /= _KIB
    return f"{n:.1f} PiB"


def _fmt(val: object) -> str:
    if val is None:
        return "N/A"
    if isinstance(val, bool):
        return "Yes" if val else "No"
    return str(val)


def _metadata_pairs(snapshot: Snapshot) -> list[tuple[str, str]]:
    m = snapshot.metadata
    return [
        ("Snapshot ID", m.snapshot_id),
        (
            "Created At",
            m.created_at.isoformat()
            if hasattr(m.created_at, "isoformat")
            else str(m.created_at),
        ),
        ("Application Version", m.application_version),
        ("Schema Version", str(m.schema_version)),
        ("Platform", m.platform),
        ("Hostname", m.hostname),
        ("Duration (ms)", str(m.duration_ms)),
        ("Notes", m.notes or ""),
    ]


def _system_pairs(snapshot: Snapshot) -> list[tuple[str, str]]:
    s = snapshot.system
    return [
        ("OS Name", _fmt(s.os_name)),
        ("OS Version", _fmt(s.os_version)),
        ("Distribution", _fmt(s.distribution)),
        ("Kernel", _fmt(s.kernel)),
        ("Architecture", _fmt(s.architecture)),
        ("Hostname", _fmt(s.hostname)),
        ("Timezone", _fmt(s.timezone)),
        ("Locale", _fmt(s.locale)),
        ("Python Version", _fmt(s.python_version)),
        ("Machine ID", _fmt(s.machine_id)),
        ("Boot Time", _fmt(s.boot_time)),
        ("Uptime (seconds)", _fmt(s.uptime_seconds)),
    ]


def _hardware_pairs(snapshot: Snapshot) -> list[tuple[str, str]]:
    h = snapshot.hardware
    if h is None:
        return [("(no hardware data collected)", "")]
    pairs: list[tuple[str, str]] = []
    if h.cpu:
        pairs.append(("CPU Model", _fmt(h.cpu.model)))
        pairs.append(("CPU Vendor", _fmt(h.cpu.vendor)))
        pairs.append(("Logical Cores", str(h.cpu.logical_cores)))
        pairs.append(("Physical Cores", _fmt(h.cpu.physical_cores)))
        pairs.append(("Clock Speed (MHz)", _fmt(h.cpu.clock_speed_mhz)))
    if h.memory:
        pairs.append(("Total Memory", _format_bytes(h.memory.total_bytes)))
        pairs.append(("Available Memory", _format_bytes(h.memory.available_bytes)))
        pairs.append(("Used Memory", _format_bytes(h.memory.used_bytes)))
        pairs.append(("Memory Usage", f"{h.memory.percent:.1f}%"))
    if h.swap:
        pairs.append(("Total Swap", _format_bytes(h.swap.total_bytes)))
        pairs.append(("Used Swap", _format_bytes(h.swap.used_bytes)))
        pairs.append(("Swap Usage", f"{h.swap.percent:.1f}%"))
    return pairs


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    header = "| " + " | ".join(headers) + " |"
    lines = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def _markdown_section(title: str, pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return ""
    lines = [f"## {title}\n"]
    rows: list[list[str]] = []
    for key, val in pairs:
        if key and val:
            rows.append([key, val])
    if rows:
        lines.append(_markdown_table(["Field", "Value"], rows))
    return "\n".join(lines)


def _build_html_table(headers: list[str], rows: list[list[str]]) -> str:
    parts = ["<table>", "  <thead><tr>"]
    for h in headers:
        parts.append(f"    <th>{_html_escape(h)}</th>")
    parts.append("  </tr></thead>")
    parts.append("  <tbody>")
    for row in rows:
        parts.append("    <tr>")
        for cell in row:
            parts.append(f"      <td>{_html_escape(cell)}</td>")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def _html_escape(s: str) -> str:
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s.replace('"', "&quot;")


def _build_html_section(
    title: str,
    pairs: list[tuple[str, str]],
) -> str:
    if not pairs:
        return ""
    lines = [f"<h2>{_html_escape(title)}</h2>"]
    rows: list[list[str]] = []
    for key, val in pairs:
        if key and val:
            rows.append([key, val])
    if rows:
        lines.append(_build_html_table(["Field", "Value"], rows))
    return "\n".join(lines)


_CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;line-height:1.6;padding:2rem}
h1{color:#e94560;font-size:2rem;margin-bottom:.5rem}
h2{color:#0f3460;background:#e94560;display:inline-block;padding:.3rem 1rem;margin:2rem 0 1rem;border-radius:4px;font-size:1.3rem}
h3{color:#e94560;margin:1rem 0 .5rem;font-size:1.1rem}
p{margin:.5rem 0}
a{color:#53a8b6}
table{width:100%;border-collapse:collapse;margin:1rem 0;background:#16213e;border-radius:4px;overflow:hidden}
th,td{text-align:left;padding:.5rem .75rem;border-bottom:1px solid #0f3460}
th{background:#0f3460;color:#e94560;font-weight:600}
tr:hover{background:#1a1a3e}
code{background:#0f3460;padding:.1rem .4rem;border-radius:3px;font-size:.9rem}
pre{background:#0f3460;padding:1rem;border-radius:4px;overflow-x:auto;margin:.5rem 0}
.footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #0f3460;font-size:.85rem;color:#888}
@media(max-width:768px){body{padding:1rem}table{font-size:.85rem}}
"""


class ExportEngine:

    def export_json(self, snapshot: Snapshot, path: Path | None = None) -> str:
        try:
            data = snapshot.model_dump(mode="json")
            raw = orjson.dumps(data, option=orjson.OPT_INDENT_2)
            content = raw.decode("utf-8")
        except (orjson.JSONEncodeError, ValueError) as exc:
            raise ExportError(
                f"Failed to serialize snapshot to JSON: {exc}",
                original=exc,
            ) from exc

        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            except OSError as exc:
                raise ExportError(
                    f"Failed to write JSON export to {path}: {exc}",
                    original=exc,
                ) from exc

        return content

    def export_markdown(self, snapshot: Snapshot, path: Path | None = None) -> str:
        sections: list[str] = [
            "# SystemDNA Snapshot Report\n",
        ]

        md = snapshot.metadata
        info_rows = [
            ("Snapshot ID", md.snapshot_id),
            (
                "Created At",
                md.created_at.isoformat()
                if hasattr(md.created_at, "isoformat")
                else str(md.created_at),
            ),
            ("Application Version", md.application_version),
            ("Schema Version", str(md.schema_version)),
            ("Platform", md.platform),
            ("Hostname", md.hostname),
            ("Duration (ms)", str(md.duration_ms)),
        ]
        if md.notes:
            info_rows.append(("Notes", md.notes))

        sections.append("## Snapshot Information\n")
        kv_rows = [[k, v] for k, v in info_rows]
        sections.append(_markdown_table(["Field", "Value"], kv_rows))

        sys_pairs = _system_pairs(snapshot)
        sections.append(_markdown_section("System Information", sys_pairs))

        hw = _hardware_pairs(snapshot)
        if hw:
            sections.append(_markdown_section("Hardware Information", hw))

        if snapshot.hardware and snapshot.hardware.disks:
            sections.append("## Disks\n")
            disk_rows: list[list[str]] = []
            for d in snapshot.hardware.disks:
                disk_rows.append([
                    d.device,
                    d.mount_point,
                    d.filesystem,
                    _format_bytes(d.total_bytes),
                    _format_bytes(d.used_bytes),
                    f"{d.percent:.1f}%",
                ])
            sections.append(_markdown_table(
                ["Device", "Mount", "FS", "Total", "Used", "Usage"],
                disk_rows,
            ))

        if snapshot.network:
            n = snapshot.network
            net_pairs: list[tuple[str, str]] = [
                ("Hostname", _fmt(n.hostname)),
                ("Domain Name", _fmt(n.domain_name)),
                ("DNS Servers", ", ".join(n.dns_servers) if n.dns_servers else "N/A"),
            ]
            sections.append(_markdown_section("Network Information", net_pairs))

            if n.interfaces:
                sections.append("### Network Interfaces\n")
                iface_rows: list[list[str]] = []
                for iface in n.interfaces:
                    iface_rows.append([
                        iface.name,
                        _fmt(iface.mac_address),
                        ", ".join(iface.ipv4) if iface.ipv4 else "N/A",
                        ", ".join(iface.ipv6) if iface.ipv6 else "N/A",
                        _fmt(iface.mtu),
                        "Up" if iface.is_up else "Down",
                    ])
                sections.append(_markdown_table(
                    ["Interface", "MAC", "IPv4", "IPv6", "MTU", "Status"],
                    iface_rows,
                ))

            if n.listening_ports:
                sections.append("### Listening Ports\n")
                port_rows: list[list[str]] = []
                for p in n.listening_ports:
                    port_rows.append([
                        p.protocol,
                        str(p.port),
                        p.address,
                        _fmt(p.pid),
                        _fmt(p.process),
                    ])
                sections.append(_markdown_table(
                    ["Protocol", "Port", "Address", "PID", "Process"],
                    port_rows,
                ))

        if snapshot.packages:
            sections.append("## Packages\n")
            for mgr in snapshot.packages.managers:
                sections.append(f"### {mgr.name}\n")
                if mgr.packages:
                    pkg_rows: list[list[str]] = []
                    for pkg in mgr.packages:
                        pkg_rows.append([pkg.name, pkg.version, _fmt(pkg.repository)])
                    sections.append(_markdown_table(
                        ["Package", "Version", "Repository"],
                        pkg_rows,
                    ))
                else:
                    sections.append("No packages recorded.\n")

        if snapshot.services:
            svc = snapshot.services
            init_name = svc.init_system.name if svc.init_system else "unknown"
            sections.append(f"## Services (init: {init_name})\n")
            if svc.services:
                svc_rows: list[list[str]] = []
                for s in svc.services:
                    svc_rows.append([
                        s.name,
                        _fmt(s.status),
                        "Yes" if s.enabled else "No" if s.enabled is False else "N/A",
                        _fmt(s.startup_type),
                        _fmt(s.pid),
                        _fmt(s.description),
                    ])
                sections.append(_markdown_table(
                    ["Name", "Status", "Enabled", "Startup Type", "PID", "Description"],
                    svc_rows,
                ))

        if snapshot.users:
            u = snapshot.users
            sections.append(f"## Users (current: {u.current_user})\n")
            if u.users:
                user_rows: list[list[str]] = []
                for usr in u.users:
                    user_rows.append([
                        usr.username,
                        _fmt(usr.uid),
                        _fmt(usr.gid),
                        ", ".join(usr.groups) if usr.groups else "N/A",
                        _fmt(usr.shell),
                        _fmt(usr.home),
                    ])
                sections.append(_markdown_table(
                    ["Username", "UID", "GID", "Groups", "Shell", "Home"],
                    user_rows,
                ))

        if snapshot.security:
            sec = snapshot.security
            fw_enabled = _fmt(sec.firewall.enabled if sec.firewall else None)
            fw_name = _fmt(sec.firewall.name if sec.firewall else None)
            sec_pairs: list[tuple[str, str]] = [
                ("Firewall Enabled", fw_enabled),
                ("Firewall Name", fw_name),
                ("SELinux Enforcing", _fmt(sec.selinux_enforcing)),
                ("AppArmor Enforcing", _fmt(sec.apparmor_enforcing)),
                ("Kernel Lockdown", _fmt(sec.kernel_lockdown)),
                ("SSH Password Auth", _fmt(sec.ssh_password_auth)),
                ("SSH Root Login", _fmt(sec.ssh_root_login)),
            ]
            sections.append(_markdown_section("Security", sec_pairs))

        if snapshot.configuration and snapshot.configuration.tracked_files:
            sections.append("## Tracked Configuration Files\n")
            cf_rows: list[list[str]] = []
            for f in snapshot.configuration.tracked_files:
                cf_rows.append([
                    f.path,
                    f.hash,
                    _format_bytes(f.size_bytes),
                    _fmt(f.modified_time),
                    _fmt(f.permissions),
                ])
            sections.append(_markdown_table(
                ["Path", "Hash", "Size", "Modified", "Permissions"],
                cf_rows,
            ))

        content = "\n".join(sections)

        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            except OSError as exc:
                raise ExportError(
                    f"Failed to write Markdown export to {path}: {exc}",
                    original=exc,
                ) from exc

        return content

    def export_html(self, snapshot: Snapshot, path: Path | None = None) -> str:
        md = snapshot.metadata
        created = (
            md.created_at.isoformat()
            if hasattr(md.created_at, "isoformat")
            else str(md.created_at)
        )

        sections_html: list[str] = []

        sections_html.append("<h1>SystemDNA Snapshot Report</h1>")

        info_rows: list[list[str]] = [
            ["Snapshot ID", md.snapshot_id],
            ["Created At", created],
            ["Application Version", md.application_version],
            ["Schema Version", str(md.schema_version)],
            ["Platform", md.platform],
            ["Hostname", md.hostname],
            ["Duration (ms)", str(md.duration_ms)],
        ]
        if md.notes:
            info_rows.append(["Notes", md.notes])
        sections_html.append("<h2>Snapshot Information</h2>")
        sections_html.append(_build_html_table(["Field", "Value"], info_rows))

        sys_pairs = _system_pairs(snapshot)
        sections_html.append(
            _build_html_section("System Information", sys_pairs)
        )

        hw = _hardware_pairs(snapshot)
        if hw:
            sections_html.append(_build_html_section("Hardware Information", hw))

        if snapshot.hardware and snapshot.hardware.disks:
            sections_html.append("<h2>Disks</h2>")
            disk_rows: list[list[str]] = []
            for d in snapshot.hardware.disks:
                disk_rows.append([
                    d.device,
                    d.mount_point,
                    d.filesystem,
                    _format_bytes(d.total_bytes),
                    _format_bytes(d.used_bytes),
                    f"{d.percent:.1f}%",
                ])
            sections_html.append(_build_html_table(
                ["Device", "Mount", "FS", "Total", "Used", "Usage"],
                disk_rows,
            ))

        if snapshot.network:
            n = snapshot.network
            sections_html.append(_build_html_section("Network Information", [
                ("Hostname", _fmt(n.hostname)),
                ("Domain Name", _fmt(n.domain_name)),
                ("DNS Servers", ", ".join(n.dns_servers) if n.dns_servers else "N/A"),
            ]))

            if n.interfaces:
                sections_html.append("<h3>Network Interfaces</h3>")
                iface_rows: list[list[str]] = []
                for iface in n.interfaces:
                    iface_rows.append([
                        iface.name,
                        _fmt(iface.mac_address),
                        ", ".join(iface.ipv4) if iface.ipv4 else "N/A",
                        ", ".join(iface.ipv6) if iface.ipv6 else "N/A",
                        _fmt(iface.mtu),
                        "Up" if iface.is_up else "Down",
                    ])
                sections_html.append(_build_html_table(
                    ["Interface", "MAC", "IPv4", "IPv6", "MTU", "Status"],
                    iface_rows,
                ))

            if n.listening_ports:
                sections_html.append("<h3>Listening Ports</h3>")
                port_rows: list[list[str]] = []
                for p in n.listening_ports:
                    port_rows.append([
                        p.protocol,
                        str(p.port),
                        p.address,
                        _fmt(p.pid),
                        _fmt(p.process),
                    ])
                sections_html.append(_build_html_table(
                    ["Protocol", "Port", "Address", "PID", "Process"],
                    port_rows,
                ))

        if snapshot.packages:
            sections_html.append("<h2>Packages</h2>")
            for mgr in snapshot.packages.managers:
                sections_html.append(f"<h3>{_html_escape(mgr.name)}</h3>")
                if mgr.packages:
                    pkg_rows: list[list[str]] = []
                    for pkg in mgr.packages:
                        pkg_rows.append([pkg.name, pkg.version, _fmt(pkg.repository)])
                    sections_html.append(_build_html_table(
                        ["Package", "Version", "Repository"],
                        pkg_rows,
                    ))
                else:
                    sections_html.append("<p>No packages recorded.</p>")

        if snapshot.services:
            svc = snapshot.services
            init_name = svc.init_system.name if svc.init_system else "unknown"
            sections_html.append(f"<h2>Services (init: {_html_escape(init_name)})</h2>")
            if svc.services:
                svc_rows: list[list[str]] = []
                for s in svc.services:
                    svc_rows.append([
                        s.name,
                        _fmt(s.status),
                        "Yes" if s.enabled else "No" if s.enabled is False else "N/A",
                        _fmt(s.startup_type),
                        _fmt(s.pid),
                        _fmt(s.description),
                    ])
                sections_html.append(_build_html_table(
                    ["Name", "Status", "Enabled", "Startup Type", "PID", "Description"],
                    svc_rows,
                ))

        if snapshot.users:
            u = snapshot.users
            escaped_user = _html_escape(u.current_user)
            sections_html.append(
                f"<h2>Users (current: {escaped_user})</h2>"
            )
            if u.users:
                user_rows: list[list[str]] = []
                for usr in u.users:
                    user_rows.append([
                        usr.username,
                        _fmt(usr.uid),
                        _fmt(usr.gid),
                        ", ".join(usr.groups) if usr.groups else "N/A",
                        _fmt(usr.shell),
                        _fmt(usr.home),
                    ])
                sections_html.append(_build_html_table(
                    ["Username", "UID", "GID", "Groups", "Shell", "Home"],
                    user_rows,
                ))

        if snapshot.security:
            sec = snapshot.security
            fw_enabled = _fmt(sec.firewall.enabled if sec.firewall else None)
            fw_name = _fmt(sec.firewall.name if sec.firewall else None)
            sec_pairs: list[tuple[str, str]] = [
                ("Firewall Enabled", fw_enabled),
                ("Firewall Name", fw_name),
                ("SELinux Enforcing", _fmt(sec.selinux_enforcing)),
                ("AppArmor Enforcing", _fmt(sec.apparmor_enforcing)),
                ("Kernel Lockdown", _fmt(sec.kernel_lockdown)),
                ("SSH Password Auth", _fmt(sec.ssh_password_auth)),
                ("SSH Root Login", _fmt(sec.ssh_root_login)),
            ]
            sections_html.append(
                _build_html_section("Security", sec_pairs)
            )

        if snapshot.configuration and snapshot.configuration.tracked_files:
            sections_html.append("<h2>Tracked Configuration Files</h2>")
            cf_rows: list[list[str]] = []
            for f in snapshot.configuration.tracked_files:
                cf_rows.append([
                    _html_escape(f.path),
                    f.hash,
                    _format_bytes(f.size_bytes),
                    _fmt(f.modified_time),
                    _fmt(f.permissions),
                ])
            sections_html.append(_build_html_table(
                ["Path", "Hash", "Size", "Modified", "Permissions"],
                cf_rows,
            ))

        footer = (
            f'<p class="footer">Generated by SystemDNA v{__version__} &mdash; '
            f"Snapshot {md.snapshot_id}</p>"
        )
        body = "\n".join(sections_html) + "\n" + footer
        html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f"<title>SystemDNA Snapshot Report &mdash; "
            f"{_html_escape(md.hostname)}</title>\n"
            f"<style>\n{_CSS}\n</style>\n"
            "</head>\n"
            f"<body>\n{body}\n</body>\n"
            "</html>\n"
        )

        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8")
            except OSError as exc:
                raise ExportError(
                    f"Failed to write HTML export to {path}: {exc}",
                    original=exc,
                ) from exc

        return html
