from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from systemdna.collectors.base import Collector
from systemdna.collectors.registry import CollectorRegistry
from systemdna.core.exceptions import PluginError
from systemdna.doctor.registry import DoctorRegistry, DoctorRule
from systemdna.plugins.base import Plugin
from systemdna.plugins.loader import PluginLoader, _is_plugin_subclass
from systemdna.plugins.manager import PluginManager


class GoodPlugin(Plugin):
    name = "test-plugin"
    version = "1.0.0"
    description = "A test plugin"

    def initialize(self) -> None:
        pass

    def cleanup(self) -> None:
        pass


class FailingInitPlugin(Plugin):
    name = "failing-init"
    version = "0.1.0"
    description = "Fails on init"

    def initialize(self) -> None:
        msg = "init failure"
        raise RuntimeError(msg)


class NoNamePlugin(Plugin):
    version = "0.1.0"
    description = "Missing name"

    def initialize(self) -> None:
        pass


class PluginWithCollectors(Plugin):
    name = "collector-plugin"
    version = "0.1.0"
    description = "Has collectors"

    def initialize(self) -> None:
        pass

    def register_collectors(self) -> list[type[Collector[object]]]:
        return [MockCollector]  # type: ignore[list-item]


class MockCollector(Collector[dict[str, str]]):
    name = "mock-collector"
    description = "Mock collector from plugin"

    def collect(self) -> dict[str, str]:
        return {"from": "plugin"}


class MockDoctorRule(DoctorRule):
    name = "mock-rule"
    description = "Mock doctor rule"
    severity = "info"  # type: ignore[assignment]

    def check(self, snapshot: Any) -> None:
        return None


class PluginWithRules(Plugin):
    name = "rule-plugin"
    version = "0.1.0"
    description = "Has rules"

    def initialize(self) -> None:
        pass

    def register_doctor_rules(self) -> list[type[DoctorRule]]:
        return [MockDoctorRule]


def test_plugin_base_interface() -> None:
    assert Plugin.initialize is not None
    assert Plugin.register_collectors is not None
    assert Plugin.register_doctor_rules is not None
    assert Plugin.cleanup is not None


def test_good_plugin_instantiation() -> None:
    plugin = GoodPlugin()
    assert plugin.name == "test-plugin"
    assert plugin.version == "1.0.0"
    assert plugin.description == "A test plugin"


def test_is_plugin_subclass() -> None:
    assert _is_plugin_subclass(GoodPlugin) is True
    assert _is_plugin_subclass(Plugin) is False
    assert _is_plugin_subclass(object) is False


def test_loader_discover_plugins_with_mock_file(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "my_plugin.py"
    plugin_file.write_text(
        "from systemdna.plugins.base import Plugin\n"
        "class MyCoolPlugin(Plugin):\n"
        "    name = 'cool-plugin'\n"
        "    version = '2.0'\n"
        "    description = 'Cool plugin'\n"
        "    def initialize(self): pass\n",
        encoding="utf-8",
    )

    loader = PluginLoader([plugin_dir])
    plugins = loader.discover_plugins()
    assert len(plugins) == 1
    assert plugins[0].name == "cool-plugin"


def test_loader_discover_returns_empty_for_missing_dir() -> None:
    loader = PluginLoader([Path("/nonexistent/plugins")])
    assert loader.discover_plugins() == []


def test_loader_load_plugin(tmp_path: Path) -> None:
    plugin_file = tmp_path / "single_plugin.py"
    plugin_file.write_text(
        "from systemdna.plugins.base import Plugin\n"
        "class SinglePlugin(Plugin):\n"
        "    name = 'single'\n"
        "    version = '1.0'\n"
        "    description = 'Single plugin'\n"
        "    def initialize(self): pass\n",
        encoding="utf-8",
    )

    loader = PluginLoader([tmp_path])
    plugin = loader.load_plugin(plugin_file)
    assert plugin is not None
    assert plugin.name == "single"


def test_loader_load_nonexistent_plugin() -> None:
    loader = PluginLoader([Path("/tmp")])
    result = loader.load_plugin(Path("/nonexistent.py"))
    assert result is None


def test_loader_get_available_plugins(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "avail_plugins"
    plugin_dir.mkdir()
    (plugin_dir / "some_plugin.py").write_text(
        "from systemdna.plugins.base import Plugin\n"
        "class AvailablePlugin(Plugin):\n"
        "    name = 'avail'\n"
        "    version = '1.0'\n"
        "    description = 'Available'\n"
        "    def initialize(self): pass\n",
        encoding="utf-8",
    )

    loader = PluginLoader([plugin_dir])
    available = loader.get_available_plugins()
    assert len(available) >= 1
    assert any(a["name"] == "avail" for a in available)


def test_loader_skips_init_py(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "skip_init"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("", encoding="utf-8")
    loader = PluginLoader([plugin_dir])
    assert loader.discover_plugins() == []


def test_plugin_manager_lifecycle() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    assert manager.get_active_plugins() == []
    assert manager.get_available() == []


def test_plugin_manager_load_all() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    loaded = manager.load_all()
    assert loaded == []


def test_plugin_manager_enable_plugin_not_found() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    result = manager.enable_plugin("nonexistent")
    assert result is False


def test_plugin_manager_disable_plugin_not_active() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    result = manager.disable_plugin("nonexistent")
    assert result is False


def test_plugin_manager_disable_cleans_up() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    plugin = GoodPlugin()
    manager._activate(plugin)
    assert "test-plugin" in manager._active

    result = manager.disable_plugin("test-plugin")
    assert result is True
    assert "test-plugin" not in manager._active


def test_plugin_manager_get_plugin_info_active() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    plugin = GoodPlugin()
    manager._activate(plugin)

    info = manager.get_plugin_info("test-plugin")
    assert info is not None
    assert info["name"] == "test-plugin"
    assert info["active"] is True


def test_plugin_manager_get_plugin_info_not_found() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    assert manager.get_plugin_info("nonexistent") is None


def test_error_handling_for_bad_plugins() -> None:
    plugin = FailingInitPlugin()
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()

    with pytest.raises(PluginError, match="initialize"):
        manager = PluginManager(PluginLoader([]), collector_registry, doctor_registry)
        manager._activate(plugin)


def test_plugin_with_collectors_registers_them() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    plugin = PluginWithCollectors()
    manager._activate(plugin)

    registered = collector_registry.get("mock-collector")
    assert registered is not None


def test_safe_instantiate_missing_attributes() -> None:
    with pytest.raises(PluginError, match="missing required attributes"):
        PluginLoader._safe_instantiate(NoNamePlugin)


def test_plugin_with_doctor_rules_registers_them() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    plugin = PluginWithRules()
    manager._activate(plugin)

    assert len(doctor_registry.get_all()) > 0


def test_loader_import_module_from_file_nonexistent() -> None:
    result = PluginLoader._import_module_from_file(Path("/nonexistent/module.py"))
    assert result is None


def test_loader_import_package_nonexistent() -> None:
    result = PluginLoader._import_package(Path("/nonexistent/package"))
    assert result is None


def test_plugin_manager_load_all_skips_duplicates() -> None:
    collector_registry = CollectorRegistry()
    doctor_registry = DoctorRegistry()
    loader = PluginLoader([])
    manager = PluginManager(loader, collector_registry, doctor_registry)

    manager._activate(GoodPlugin())
    result = manager.load_all()
    assert result == []
