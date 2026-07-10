from __future__ import annotations

from systemdna.models.snapshot import Snapshot
from systemdna.scoring.models import ScoringFinding


def check_firewall(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.firewall is None:
        return ScoringFinding(
            title="No firewall detected",
            description="No firewall information was found on the system.",
            impact=15,
            severity="critical",
        )
    if not security.firewall.enabled:
        return ScoringFinding(
            title="Firewall not enabled",
            description=f"Firewall '{security.firewall.name or 'unknown'}' is installed but not enabled.",
            impact=5,
            severity="warning",
        )
    return None


def check_ssh_password(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.ssh_password_auth is None:
        return None
    if security.ssh_password_auth:
        return ScoringFinding(
            title="SSH password authentication enabled",
            description="Password-based SSH authentication is active. Key-based authentication is recommended.",
            impact=10,
            severity="warning",
        )
    return None


def check_ssh_root(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.ssh_root_login is None:
        return None
    if security.ssh_root_login:
        return ScoringFinding(
            title="SSH root login enabled",
            description="Direct SSH root login is permitted. This increases attack surface.",
            impact=10,
            severity="critical",
        )
    return None


def check_selinux(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.selinux_enforcing is None:
        return None
    if not security.selinux_enforcing:
        return ScoringFinding(
            title="SELinux not enforcing",
            description="SELinux is present but not in enforcing mode.",
            impact=5,
            severity="warning",
        )
    return None


def check_apparmor(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.apparmor_enforcing is None:
        return None
    if not security.apparmor_enforcing:
        return ScoringFinding(
            title="AppArmor not enforcing",
            description="AppArmor is present but not in enforcing mode.",
            impact=5,
            severity="warning",
        )
    return None


def check_lockdown(snapshot: Snapshot) -> ScoringFinding | None:
    security = snapshot.security
    if security is None or security.kernel_lockdown is None:
        return ScoringFinding(
            title="Kernel lockdown not detected",
            description="No kernel lockdown mode was detected.",
            impact=3,
            severity="info",
        )
    if security.kernel_lockdown.lower() not in ("integrity", "confidentiality"):
        return ScoringFinding(
            title="Kernel lockdown not enabled",
            description=f"Kernel lockdown mode is '{security.kernel_lockdown}'. Consider enabling integrity or confidentiality mode.",
            impact=3,
            severity="info",
        )
    return None


def check_swap(snapshot: Snapshot) -> ScoringFinding | None:
    hardware = snapshot.hardware
    if hardware is None or hardware.swap is None:
        return ScoringFinding(
            title="No swap configured",
            description="No swap space was detected on the system.",
            impact=5,
            severity="warning",
        )
    if hardware.swap.total_bytes <= 0:
        return ScoringFinding(
            title="No swap configured",
            description="Swap information is present but total size is zero.",
            impact=5,
            severity="warning",
        )
    return None


def check_disk_usage(snapshot: Snapshot) -> list[ScoringFinding]:
    findings: list[ScoringFinding] = []
    hardware = snapshot.hardware
    if hardware is None:
        return findings
    for disk in hardware.disks:
        if disk.percent > 95:
            findings.append(
                ScoringFinding(
                    title=f"Disk {disk.mount_point} critically full",
                    description=f"Disk usage at {disk.percent:.1f}% on {disk.mount_point}.",
                    impact=10,
                    severity="critical",
                )
            )
        elif disk.percent > 90:
            findings.append(
                ScoringFinding(
                    title=f"Disk {disk.mount_point} nearly full",
                    description=f"Disk usage at {disk.percent:.1f}% on {disk.mount_point}.",
                    impact=5,
                    severity="warning",
                )
            )
    return findings


def check_dns(snapshot: Snapshot) -> ScoringFinding | None:
    network = snapshot.network
    if network is None:
        return None
    if not network.dns_servers:
        return ScoringFinding(
            title="No DNS servers configured",
            description="No DNS servers were found in the network configuration.",
            impact=5,
            severity="warning",
        )
    return None


def check_packages_count(snapshot: Snapshot) -> ScoringFinding | None:
    packages = snapshot.packages
    if packages is None:
        return None
    total = sum(len(mgr.packages) for mgr in packages.managers)
    if total > 3000:
        return ScoringFinding(
            title="Excessive packages installed",
            description=f"System has {total} packages installed. Consider removing unused packages.",
            impact=5,
            severity="warning",
        )
    return None


def check_multiple_pm(snapshot: Snapshot) -> ScoringFinding | None:
    packages = snapshot.packages
    if packages is None:
        return None
    if len(packages.managers) > 2:
        names = ", ".join(mgr.name for mgr in packages.managers)
        return ScoringFinding(
            title="Multiple package managers detected",
            description=f"More than two package managers found: {names}.",
            impact=3,
            severity="info",
        )
    return None


def check_old_kernels(snapshot: Snapshot) -> ScoringFinding | None:
    packages = snapshot.packages
    if packages is None:
        return None
    kernel_pkgs: list[str] = []
    for mgr in packages.managers:
        for pkg in mgr.packages:
            name_lower = pkg.name.lower()
            if name_lower.startswith("linux-image-") or name_lower.startswith("kernel-"):
                kernel_pkgs.append(pkg.name)
    if len(kernel_pkgs) > 1:
        return ScoringFinding(
            title="Multiple kernel packages installed",
            description=f"{len(kernel_pkgs)} kernel packages found. Old kernels can be removed.",
            impact=3,
            severity="info",
        )
    return None


def check_init_detected(snapshot: Snapshot) -> ScoringFinding | None:
    services = snapshot.services
    if services is None or services.init_system is None:
        return ScoringFinding(
            title="Init system not detected",
            description="No init system (systemd, OpenRC, etc.) was detected.",
            impact=5,
            severity="warning",
        )
    return None


def check_failed_services(snapshot: Snapshot) -> list[ScoringFinding]:
    findings: list[ScoringFinding] = []
    services = snapshot.services
    if services is None:
        return findings
    failed = [
        svc for svc in services.services
        if svc.status.lower() in ("failed", "error", "inactive")
    ]
    for svc in failed[:3]:
        findings.append(
            ScoringFinding(
                title=f"Service '{svc.name}' in {svc.status} state",
                description=f"Service {svc.name} is {svc.status}.",
                impact=3,
                severity="warning",
            )
        )
    if len(failed) > 3:
        remaining = len(failed) - 3
        findings.append(
            ScoringFinding(
                title=f"{remaining} additional failing services",
                description=f"{remaining} more services are in a failed or inactive state.",
                impact=min(remaining, 7),
                severity="warning",
            )
        )
    return findings


def check_has_tracked_files(snapshot: Snapshot) -> ScoringFinding | None:
    configuration = snapshot.configuration
    if configuration is None:
        return ScoringFinding(
            title="No configuration tracking",
            description="No configuration tracking information was found.",
            impact=5,
            severity="warning",
        )
    if not configuration.tracked_files:
        return ScoringFinding(
            title="No tracked configuration files",
            description="No configuration files are being tracked for changes.",
            impact=5,
            severity="warning",
        )
    return None


def check_uptime(snapshot: Snapshot) -> ScoringFinding | None:
    system = snapshot.system
    if system is None or system.uptime_seconds is None:
        return None
    days = system.uptime_seconds / 86400
    if days > 90:
        return ScoringFinding(
            title="System uptime exceeds 90 days",
            description=f"System has been up for {days:.0f} days. A reboot may be needed for kernel updates.",
            impact=2,
            severity="info",
        )
    return None
