from __future__ import annotations

import contextlib
import re
import subprocess
from pathlib import Path

from systemdna.models.security import FirewallStatus, SecurityInfo


def _run_cmd(args: list[str], timeout: int = 15) -> str | None:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return None


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def get_firewall_status() -> FirewallStatus:
    ufw_output = _run_cmd(["ufw", "status"])
    if ufw_output is not None:
        lines = ufw_output.strip().splitlines()
        if lines:
            status_line = lines[0].lower()
            enabled = "active" in status_line or "enabled" in status_line
            name = "ufw"
            rules_count = None
            with contextlib.suppress(Exception):
                rules_count = len(lines) - 1
            return FirewallStatus(enabled=enabled, name=name, rules_count=rules_count)
    nft_output = _run_cmd(["nft", "list", "ruleset"])
    if nft_output is not None:
        rule_count = len([ln for ln in nft_output.splitlines() if ln.strip()])
        return FirewallStatus(
            enabled=True,
            name="nftables",
            rules_count=rule_count,
        )
    iptables_output = _run_cmd(["iptables", "-L", "-n"])
    if iptables_output is not None:
        rule_count = 0
        for line in iptables_output.splitlines():
            if line.strip().startswith(("ACCEPT", "DROP", "REJECT")):
                rule_count += 1
        return FirewallStatus(
            enabled=True,
            name="iptables",
            rules_count=rule_count if rule_count > 0 else None,
        )
    return FirewallStatus(enabled=None, name=None, rules_count=None)


def get_selinux_status() -> bool | None:
    enforce_file = Path("/sys/fs/selinux/enforce")
    val = _read_file(enforce_file)
    if val is not None:
        try:
            return int(val) == 1
        except ValueError:
            return None
    getenforce_output = _run_cmd(["getenforce"])
    if getenforce_output is not None:
        status = getenforce_output.strip().lower()
        if status == "enforcing":
            return True
        elif status in {"permissive", "disabled"}:
            return False
    return None


def get_apparmor_status() -> bool | None:
    enabled_file = Path("/sys/kernel/security/apparmor/enabled")
    val = _read_file(enabled_file)
    if val is not None:
        try:
            enabled = int(val) == 1
        except ValueError:
            enabled = False
        if not enabled:
            return False
        profiles_file = Path("/sys/kernel/security/apparmor/profiles")
        profiles_content = _read_file(profiles_file)
        if profiles_content is not None:
            return True
        return None
    return None


def get_kernel_lockdown() -> str | None:
    lockdown_file = Path("/sys/kernel/security/lockdown")
    val = _read_file(lockdown_file)
    if val is not None:
        parts = val.split()
        for p in parts:
            if p.startswith("["):
                return p.strip("[]")
        return parts[0] if parts else None
    return None


def get_ssh_config() -> tuple[bool | None, bool | None]:
    sshd_config = Path("/etc/ssh/sshd_config")
    content = _read_file(sshd_config)
    if content is None:
        return None, None
    password_auth: bool | None = None
    permit_root: bool | None = None
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        m = re.match(r"^\s*PasswordAuthentication\s+(\S+)", stripped)
        if m:
            val = m.group(1).lower()
            if val == "yes":
                password_auth = True
            elif val == "no":
                password_auth = False
        m = re.match(r"^\s*PermitRootLogin\s+(\S+)", stripped)
        if m:
            val = m.group(1).lower()
            if val in ("yes", "without-password", "prohibit-password"):
                permit_root = val != "no"
            elif val == "no":
                permit_root = False
    return password_auth, permit_root


def get_security_info() -> SecurityInfo:
    ssh_pw, ssh_root = get_ssh_config()
    return SecurityInfo(
        firewall=get_firewall_status(),
        selinux_enforcing=get_selinux_status(),
        apparmor_enforcing=get_apparmor_status(),
        kernel_lockdown=get_kernel_lockdown(),
        ssh_password_auth=ssh_pw,
        ssh_root_login=ssh_root,
    )
