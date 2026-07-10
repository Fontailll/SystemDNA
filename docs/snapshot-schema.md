# Snapshot Schema

## Schema Versioning

Each snapshot has a `schema_version` field in its metadata. The current version is **1**. Backward-incompatible changes will increment this version.

## Top-Level Structure

```json
{
  "metadata": { ... },
  "system": { ... },
  "hardware": { ... },
  "network": { ... },
  "packages": { ... },
  "services": { ... },
  "users": { ... },
  "security": { ... },
  "configuration": { ... }
}
```

`metadata` and `system` are always present. The remaining sections are optional — they will be `null` if the collector failed or was not run.

## Sections

### metadata

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | integer | Schema version number (currently 1) |
| `application_version` | string | SystemDNA version that created the snapshot |
| `created_at` | string (ISO 8601) | Timestamp when the snapshot was created |
| `platform` | string | Platform identifier (e.g. `"linux"`) |
| `hostname` | string | Machine hostname |
| `duration_ms` | integer | Total snapshot creation time in milliseconds |
| `snapshot_id` | string | Short hex identifier (8 characters) |
| `notes` | string or null | User-provided notes |

### system

| Field | Type | Description |
|-------|------|-------------|
| `os_name` | string | Operating system name (e.g. `"Ubuntu"`, `"Fedora"`) |
| `os_version` | string | Operating system version |
| `distribution` | string or null | Distribution identifier |
| `kernel` | string or null | Kernel release string |
| `architecture` | string | CPU architecture |
| `hostname` | string | System hostname |
| `timezone` | string or null | System timezone |
| `locale` | string or null | System locale |
| `python_version` | string | Python version running SystemDNA |
| `machine_id` | string or null | `/etc/machine-id` content |
| `boot_time` | string or null | System boot timestamp |
| `uptime_seconds` | float or null | System uptime in seconds |

### hardware

| Field | Type | Description |
|-------|------|-------------|
| `cpu` | object or null | CPU model, vendor, logical/physical cores, clock speed |
| `memory` | object or null | Total, available, used bytes and usage percent |
| `swap` | object or null | Total, used bytes and usage percent |
| `disks` | array | List of disk devices with device, mount point, filesystem, sizes, usage percent |

### network

| Field | Type | Description |
|-------|------|-------------|
| `hostname` | string or null | Network hostname |
| `domain_name` | string or null | DNS domain name |
| `dns_servers` | array of strings | Configured DNS servers |
| `interfaces` | array | Network interfaces (name, MAC, IPv4/IPv6 addresses, MTU, status) |
| `listening_ports` | array | Listening ports (protocol, port, address, PID, process name) |

### packages

| Field | Type | Description |
|-------|------|-------------|
| `managers` | array | Package manager entries, each with name and array of packages (name, version, repository) |

### services

| Field | Type | Description |
|-------|------|-------------|
| `init_system` | object or null | Init system name and version |
| `services` | array | Services (name, status, enabled, startup type, PID, description) |

### users

| Field | Type | Description |
|-------|------|-------------|
| `current_user` | string | Currently logged-in user |
| `users` | array | User accounts (username, UID, GID, groups, shell, home) |

### security

| Field | Type | Description |
|-------|------|-------------|
| `firewall` | object or null | Firewall name and whether it is enabled |
| `selinux_enforcing` | boolean or null | Whether SELinux is in enforcing mode |
| `apparmor_enforcing` | boolean or null | Whether AppArmor is in enforcing mode |
| `kernel_lockdown` | string or null | Kernel lockdown mode |
| `ssh_password_auth` | boolean or null | Whether SSH password authentication is enabled |
| `ssh_root_login` | boolean or null | Whether SSH root login is permitted |

### configuration

| Field | Type | Description |
|-------|------|-------------|
| `tracked_files` | array | Tracked configuration files (path, SHA256 hash, size, modification time, permissions) |
