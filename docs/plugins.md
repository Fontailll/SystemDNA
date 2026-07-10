# Plugins

## Plugin Structure

A plugin is a Python file or package placed in a directory listed in the `plugin_dirs` configuration option. Each plugin must contain a concrete subclass of `systemdna.plugins.base.Plugin`.

### Minimal Plugin

```python
from systemdna.plugins.base import Plugin

class MyPlugin(Plugin):
    name = "myplugin"
    version = "1.0.0"
    description = "My custom plugin"

    def initialize(self) -> None:
        pass
```

## Plugin API

### Required Attributes

- `name` — unique plugin identifier
- `version` — plugin version string
- `description` — short description

### Required Methods

- `initialize(self) -> None` — called when the plugin is activated. Perform setup, validate dependencies, etc.

### Optional Methods

- `register_collectors(self) -> list[type[Collector[object]]]` — return collector classes to register with the system
- `register_doctor_rules(self) -> list[type[DoctorRule]]` — return doctor rule classes to register
- `cleanup(self) -> None` — called when the plugin is disabled. Release resources.

## Registering Collectors

```python
from systemdna.collectors.base import Collector
from systemdna.plugins.base import Plugin
from pydantic import BaseModel

class CustomData(BaseModel):
    temperature: float

class TemperatureCollector(Collector[CustomData]):
    name = "temperature"
    description = "Collects CPU temperature"
    def collect(self) -> CustomData:
        return CustomData(temperature=42.5)

class HardwareMonitorPlugin(Plugin):
    name = "hardware-monitor"
    version = "1.0.0"
    description = "Adds hardware monitoring collectors"

    def initialize(self) -> None:
        pass

    def register_collectors(self) -> list[type[Collector[object]]]:
        return [TemperatureCollector]
```

## Registering Doctor Rules

```python
from systemdna.doctor.registry import DoctorRule
from systemdna.models.doctor import Recommendation, Severity
from systemdna.models.snapshot import Snapshot

class HighTemperatureRule(DoctorRule):
    name = "high-temperature"
    description = "CPU temperature is elevated"
    severity = Severity.WARNING

    def check(self, snapshot: Snapshot) -> Recommendation | None:
        # access custom collector data via snapshot
        return None

class MonitorPlugin(Plugin):
    name = "monitor"
    version = "1.0.0"
    description = "Monitoring rules"
    def initialize(self) -> None:
        pass
    def register_doctor_rules(self) -> list[type[DoctorRule]]:
        return [HighTemperatureRule]
```

## Example Plugin

A complete minimal plugin file (saved as `myplugin.py` in a plugin directory):

```python
from systemdna.plugins.base import Plugin

class ExamplePlugin(Plugin):
    name = "example"
    version = "0.1.0"
    description = "Example SystemDNA plugin"

    def initialize(self) -> None:
        print(f"Plugin {self.name} v{self.version} initialized")

    def cleanup(self) -> None:
        print(f"Plugin {self.name} cleaned up")
```
