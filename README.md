# SystemDNA
<img width="1983" height="793" alt="SystemDNA" src="https://github.com/user-attachments/assets/cf191277-32ea-46ba-bab2-c9d064c33896" />

**Capture your system's DNA. Understand every change.**

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/Fontailll/SystemDNA/actions)
[![Python](https://img.shields.io/badge/python-3.13+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://github.com/Fontailll/SystemDNA/releases)

SystemDNA creates point-in-time snapshots of your Linux system — installed packages, running services, hardware, network configuration, users, security settings, and tracked configuration files. Each snapshot is a human-readable JSON file you can diff, analyze, and export.

Snapshots are designed for one-shot collection: invoke the command, get a complete picture of the system, and store the result. No daemons, no background agents, no continuous monitoring. This makes SystemDNA suitable for auditing, change tracking, CI/CD pipeline checks, and forensic analysis across heterogeneous Linux environments.

The snapshot diff engine compares any two snapshots and reports added, removed, and modified items per section. The doctor analysis engine runs built-in rules against a snapshot and surfaces recommendations — from security warnings to disk-space alerts. Export commands render snapshots as formatted Markdown or HTML reports suitable for sharing or archiving.

## Features

- **One-shot system snapshots** — no background daemons, no persistent agents
- **Cross-Linux-distribution support** — works on Debian, RHEL, Arch, and derivatives
- **Human-readable JSON snapshots** — each snapshot is a single structured JSON file
- **Snapshot diff engine** — compare any two snapshots and see what changed
- **System health analysis** — doctor rules flag security issues, disk pressure, configuration gaps
- **Export to JSON, Markdown, HTML** — generate reports for sharing or archiving
- **Plugin system** — extend collectors and doctor rules without modifying core code
- **Fully offline** — no telemetry, no tracking, no network calls

## Installation

> **Important:** SystemDNA collects system-wide information and must be installed
> **system-wide** (or with `pip install --user`). Do **not** install inside a
> Python virtual environment (`.venv`) — the application needs access to system
> paths, package databases, and service state files that are only visible from
> the host Python environment.
>
> If your distribution enforces PEP 668 (Arch, Fedora, etc.), add
> `--break-system-packages` to the install command or use `pipx`.

### pip (recommended)

```bash
pip install systemdna
```

### pip user install

```bash
pip install --user systemdna
```

### pipx

```bash
pipx install systemdna
```

### install script (Linux, no venv)

```bash
git clone https://github.com/Fontailll/SystemDNA.git
cd SystemDNA
bash scripts/install.sh
```

After install, restart your terminal or run `exec $SHELL` before using `systemdna`.

### from source

```bash
git clone https://github.com/Fontailll/SystemDNA.git
cd SystemDNA
pip install --user -e ".[dev]"
```

## Quick Start

```bash
# Create a snapshot of the current system
systemdna snapshot create

# Display the latest snapshot
systemdna snapshot show

# Compare the two most recent snapshots
systemdna diff latest

# Run doctor analysis on the latest snapshot
systemdna doctor run

# Export the latest snapshot as Markdown
systemdna export markdown --output report.md

# Calculate health score from the latest snapshot
systemdna score check
```

## Command Reference

| Command | Description |
|---------|-------------|
| `snapshot create` | Create a new system snapshot |
| `snapshot show [id]` | Display a snapshot (defaults to latest) |
| `diff latest [older_id]` | Compare latest snapshot with a previous one |
| `diff compare <left> <right>` | Compare two snapshots by ID |
| `doctor run [id]` | Analyze a snapshot with doctor rules |
| `history list` | List all snapshots |
| `history show [id]` | Display a snapshot |
| `history delete <id>` | Delete a snapshot |
| `history clear` | Delete all snapshots |
| `export json [id]` | Export snapshot as JSON |
| `export markdown [id]` | Export snapshot as Markdown report |
| `export html [id]` | Export snapshot as HTML report |
| `verify check [id]` | Verify snapshot integrity |
| `score check [id]` | Calculate system health score (0-100) |
| `info show` | Show current system information without creating a snapshot |
| `plugins list` | List configured plugin directories |
| `plugins info <name>` | Show plugin details |
| `config show` | Show current configuration |
| `config set <key> <value>` | Set a configuration value |
| `config path` | Show configuration and storage paths |
| `config reset` | Reset configuration to defaults |
| `version` | Show version information |

## Architecture Overview

SystemDNA is organized as a collection of independent collectors that each capture a subsystem (system info, hardware, network, packages, services, users, security, configuration). A snapshot engine runs collectors in parallel, assembles results into a typed Pydantic model, and serialises the model to JSON. The diff engine compares two snapshot models field by field. The doctor engine runs a set of rule classes against a snapshot to produce recommendations. A plugin loader discovers and instantiates third-party plugins that can register additional collectors and doctor rules.

## Requirements

- Python 3.13 or later
- Linux (tested on Debian, Ubuntu, Fedora, Arch Linux)

## Configuration

SystemDNA reads configuration from `~/.config/SystemDNA/config.json`. Use `systemdna config show` to view the current configuration and `systemdna config set` to change values.

| Key | Default | Description |
|-----|---------|-------------|
| `storage_dir` | `~/.local/share/SystemDNA` | Directory for snapshot storage |
| `snapshots_dir` | `{storage_dir}/snapshots` | Directory for snapshot files |
| `plugins_enabled` | `true` | Enable plugin loading |
| `plugin_dirs` | `[]` | Directories to scan for plugins |
| `log_level` | `WARNING` | Logging verbosity |
| `max_snapshots` | `100` | Maximum number of snapshots to retain |

## Plugin Development

Plugins are Python modules or packages dropped into a configured plugin directory. Each plugin subclasses `systemdna.plugins.base.Plugin` and can optionally implement `register_collectors()` and `register_doctor_rules()` to extend SystemDNA's capabilities.

```python
from systemdna.plugins.base import Plugin
from systemdna.collectors.base import Collector

class MyCollector(Collector):
    name = "my_collector"
    description = "Collects custom data"
    def collect(self):
        return {"key": "value"}

class MyPlugin(Plugin):
    name = "myplugin"
    version = "1.0.0"
    description = "Example plugin"
    def register_collectors(self):
        return [MyCollector]
    def initialize(self):
        pass
```

See [docs/plugins.md](docs/plugins.md) for the full plugin API.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contributing.md](docs/contributing.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.

## Documentation

- [Architecture](docs/architecture.md)
- [Collectors](docs/collectors.md)
- [Plugins](docs/plugins.md)
- [Configuration](docs/configuration.md)
- [Snapshot Schema](docs/snapshot-schema.md)
- [Contributing](docs/contributing.md)
