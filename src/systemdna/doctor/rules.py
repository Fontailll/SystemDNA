from __future__ import annotations

from systemdna.doctor.registry import DoctorRule
from systemdna.models.doctor import Recommendation, Severity
from systemdna.models.snapshot import Snapshot


class FirewallDisabledRule(DoctorRule):
    name = "firewall-disabled"
    description = "Firewall is disabled"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        security = snapshot.security
        if security is None or security.firewall is None:
            return Recommendation(
                severity=self.severity,
                title="Firewall status unknown",
                description="Could not determine firewall status",
                suggested_fix="Install and enable a firewall (ufw, firewalld, iptables)",
            )
        if not security.firewall.enabled:
            return Recommendation(
                severity=self.severity,
                title="Firewall is disabled",
                description=f"Firewall ({security.firewall.name or 'unknown'}) is not enabled",
                suggested_fix="Enable the firewall to protect the system",
                reference="https://wiki.ubuntu.com/UncomplicatedFirewall",
            )
        return None


class SSHPasswordAuthRule(DoctorRule):
    name = "ssh-password-auth"
    description = "SSH password authentication is enabled"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        security = snapshot.security
        if security is None or security.ssh_password_auth is None:
            return None
        if security.ssh_password_auth:
            return Recommendation(
                severity=self.severity,
                title="SSH password authentication is enabled",
                description="SSH allows password-based authentication which is susceptible to brute-force attacks",
                suggested_fix="Disable password authentication and use SSH keys only: set 'PasswordAuthentication no' in /etc/ssh/sshd_config",
                reference="https://www.ssh.com/academy/ssh/password-authentication",
            )
        return None


class SSHRootLoginRule(DoctorRule):
    name = "ssh-root-login"
    description = "SSH root login is enabled"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        security = snapshot.security
        if security is None or security.ssh_root_login is None:
            return None
        if security.ssh_root_login:
            return Recommendation(
                severity=self.severity,
                title="SSH root login is enabled",
                description="Direct SSH login as root is permitted which is a security risk",
                suggested_fix="Disable root SSH login: set 'PermitRootLogin no' in /etc/ssh/sshd_config",
                reference="https://www.ssh.com/academy/ssh/root-login",
            )
        return None


class SwapDisabledRule(DoctorRule):
    name = "swap-disabled"
    description = "No swap space configured"
    severity = Severity.INFO

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        hardware = snapshot.hardware
        if hardware is None:
            return None
        swap = hardware.swap
        if swap is None or swap.total_bytes == 0:
            return Recommendation(
                severity=self.severity,
                title="No swap space configured",
                description="The system has no swap space, which may cause issues under memory pressure",
                suggested_fix="Consider creating a swap file: fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile",
                reference="https://help.ubuntu.com/community/SwapFaq",
            )
        return None


class LowDiskSpaceRule(DoctorRule):
    name = "low-disk-space"
    description = "Disk usage exceeds 90%"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        hardware = snapshot.hardware
        if hardware is None or not hardware.disks:
            return None
        for disk in hardware.disks:
            if disk.percent > 90:
                return Recommendation(
                    severity=self.severity,
                    title=f"Low disk space on {disk.mount_point}",
                    description=f"Disk '{disk.device}' mounted at {disk.mount_point} is {disk.percent:.1f}% full",
                    suggested_fix=f"Free up space on {disk.mount_point} by removing unnecessary files, cleaning package cache, or expanding the partition",
                )
        return None


class ManyPackagesRule(DoctorRule):
    name = "many-packages"
    description = "More than 2000 packages installed"
    severity = Severity.INFO

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        packages = snapshot.packages
        if packages is None:
            return None
        total = sum(len(mgr.packages) for mgr in packages.managers)
        if total > 2000:
            return Recommendation(
                severity=self.severity,
                title=f"Large number of packages installed ({total})",
                description=f"The system has {total} installed packages which may indicate package bloat",
                suggested_fix="Review and remove unused packages with 'apt autoremove' or 'dnf autoremove'",
            )
        return None


class MultiplePackageManagersRule(DoctorRule):
    name = "multiple-package-managers"
    description = "More than 2 package managers detected"
    severity = Severity.INFO

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        packages = snapshot.packages
        if packages is None:
            return None
        count = len(packages.managers)
        if count > 2:
            names = [m.name for m in packages.managers]
            return Recommendation(
                severity=self.severity,
                title=f"Multiple package managers detected ({count})",
                description=f"Package managers in use: {', '.join(names)}. Multiple package managers can lead to dependency conflicts",
                suggested_fix="Stick to one primary package manager to avoid conflicts",
            )
        return None


class NoInitDetectedRule(DoctorRule):
    name = "no-init-detected"
    description = "Init system could not be detected"
    severity = Severity.ERROR

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        services = snapshot.services
        if services is None or services.init_system is None:
            return Recommendation(
                severity=self.severity,
                title="Init system could not be detected",
                description="No init system (systemd, sysvinit, etc.) was detected on this system",
                suggested_fix="Ensure a supported init system is installed",
            )
        return None


class OldKernelPackagesRule(DoctorRule):
    name = "old-kernel-packages"
    description = "Multiple kernel packages detected"
    severity = Severity.INFO

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        packages = snapshot.packages
        if packages is None:
            return None
        kernel_prefixes = ("linux-image", "linux-headers", "kernel-", "linux-modules")
        kernel_pkgs: list[str] = []
        for mgr in packages.managers:
            for pkg in mgr.packages:
                if any(pkg.name.startswith(p) for p in kernel_prefixes):
                    kernel_pkgs.append(pkg.name)
        if len(kernel_pkgs) > 4:
            return Recommendation(
                severity=self.severity,
                title=f"Multiple kernel packages installed ({len(kernel_pkgs)})",
                description=f"Found {len(kernel_pkgs)} kernel-related packages which may indicate old kernels are not being cleaned up",
                suggested_fix="Remove old unused kernels: 'apt autoremove --purge' or 'package-cleanup --oldkernels --count=2'",
                reference="https://help.ubuntu.com/community/Lubuntu/Documentation/RemoveOldKernels",
            )
        return None


class NoDnsRule(DoctorRule):
    name = "no-dns-servers"
    description = "No DNS servers configured"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        network = snapshot.network
        if network is None:
            return None
        if not network.dns_servers:
            return Recommendation(
                severity=self.severity,
                title="No DNS servers configured",
                description="No DNS servers were found in the system configuration",
                suggested_fix="Configure DNS servers in /etc/resolv.conf or via your network manager",
                reference="https://wiki.archlinux.org/title/Domain_name_resolution",
            )
        return None
