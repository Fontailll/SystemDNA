# Architecture

## Overview

SystemDNA follows a collector-based architecture where each subsystem of the machine is captured by an independent collector class. Collectors are registered in a central registry and executed concurrently by a runner. Results are assembled into a typed Pydantic model and serialised to JSON.

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       CLI (typer)                        │
│  snapshot  diff  doctor  history  export  verify  info   │
└──────┬──────────────────────────────────────────────────┘
       │ dispatches to
       ▼
┌─────────────────────────────────────────────────────────┐
│                   SnapshotEngine                          │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │Collector   │  │Collector     │  │Storage           │  │
│  │Registry    │  │Runner        │  │(filesystem)      │  │
│  └────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐     ┌──────────────────┐
│DiffEngine    │     │DoctorEngine      │
│compares two  │     │runs rules against│
│Snapshot      │     │a Snapshot        │
│models        │     │                  │
└──────────────┘     └──────────────────┘
                            │
                            ▼
                     ┌──────────────────┐
                     │ExportEngine      │
                     │JSON / Markdown   │
                     │/ HTML            │
                     └──────────────────┘
┌─────────────────────────────────────────────────────────┐
│                   Plugin System                           │
│  PluginLoader → discovers plugins on disk                │
│  PluginManager → activates plugins, registers            │
│                  collectors and doctor rules              │
└─────────────────────────────────────────────────────────┘
```

## Data Flow — Snapshot Creation

1. `systemdna snapshot create` invokes `SnapshotEngine.create_snapshot()`
2. `SnapshotEngine` retrieves all registered collectors from `CollectorRegistry`
3. Collectors are passed to `CollectorRunner.run()` which executes them concurrently using a `ThreadPoolExecutor`, each with a 30-second timeout
4. Each `Collector.collect()` returns a typed Pydantic model (or `None` on failure)
5. `SnapshotEngine._map_results()` maps collector results to `Snapshot` model fields
6. A `Snapshot` instance is assembled with metadata (timestamp, hostname, schema version, duration)
7. `SnapshotEngine.save_snapshot()` serialises the model to JSON via orjson and writes it to the configured snapshots directory

## Collector System Design

Each collector implements the `Collector[T]` ABC:

```python
class Collector(ABC, Generic[T]):
    name: str
    description: str

    @abstractmethod
    def collect(self) -> T:
        ...
```

Built-in collectors: `system`, `hardware`, `network`, `packages`, `services`, `users`, `security`, `configuration`.

Collectors are Linux-specific and live in `src/systemdna/platform/linux/`. Each collector calls OS utilities (e.g. `lshw`, `ip`, `dpkg`, `systemctl`, `getent`) and parses files under `/proc`, `/sys`, `/etc`.

The `CollectorRunner` executes collectors in parallel, captures timing, and converts exceptions into `CollectorResult` objects so a single failing collector does not block the entire snapshot.

## Plugin System Design

Plugins are Python files or packages placed in directories listed in `plugin_dirs`. The `PluginLoader` scans these directories, imports modules, and finds concrete subclasses of `Plugin`. The `PluginManager` activates each plugin by calling `initialize()` and then registering any collectors and doctor rules the plugin exposes.

Plugins can:
- Register new collectors via `register_collectors()`
- Register new doctor rules via `register_doctor_rules()`

## Storage Format

Snapshots are stored as JSON files named `snapshot-{timestamp}-{short_id}.json` in the configured snapshots directory. The JSON structure mirrors the `Snapshot` Pydantic model exactly.
