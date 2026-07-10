# Collectors

## Available Collectors

| Collector | Name | Description |
|-----------|------|-------------|
| System | `system` | OS name, version, kernel, architecture, hostname, timezone, locale, uptime |
| Hardware | `hardware` | CPU model/cores, memory, swap, disk devices and usage |
| Network | `network` | Interfaces (MAC, IPs, MTU, status), DNS servers, listening ports |
| Packages | `packages` | Installed packages from dpkg, RPM, pacman, apk, snap, flatpak |
| Services | `services` | Systemd services (status, enabled, PID, description) |
| Users | `users` | Local users (UID, GID, groups, shell, home), current user |
| Security | `security` | Firewall status, SELinux/AppArmor state, SSH password auth, root login |
| Configuration | `configuration` | Tracked configuration file hashes and metadata |

## Collector Interface

All collectors inherit from `systemdna.collectors.base.Collector[T]`:

```python
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")

class Collector(ABC, Generic[T]):
    name: str
    description: str

    @abstractmethod
    def collect(self) -> T:
        ...
```

- `name` — unique identifier used in configuration and CLI
- `description` — short description shown in logs
- `collect()` — called by `CollectorRunner`, returns a typed Pydantic model or raises an exception

## Adding a Custom Collector

Create a class that inherits from `Collector[YourModel]` and implements `collect()`. Register it with a `CollectorRegistry`:

```python
from systemdna.collectors.base import Collector
from systemdna.collectors.registry import CollectorRegistry
from pydantic import BaseModel

class MyData(BaseModel):
    value: str

class MyCollector(Collector[MyData]):
    name = "my_collector"
    description = "Collects custom data"

    def collect(self) -> MyData:
        return MyData(value="example")

registry = CollectorRegistry()
registry.register(MyCollector())
```

To have a custom collector loaded automatically, provide it via a plugin (see [plugins.md](plugins.md)).

## Configuration Options

Collectors can be filtered at runtime by passing collector names to `SnapshotEngine.create_snapshot(collector_names=[...])`. The CLI does not currently expose this filtering, but the API supports it.
