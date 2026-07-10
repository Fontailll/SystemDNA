from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from systemdna.collectors.registry import CollectorRegistry
from systemdna.core.exceptions import PluginError
from systemdna.doctor.registry import DoctorRegistry
from systemdna.plugins.base import Plugin
from systemdna.plugins.loader import PluginLoader

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages the lifecycle of plugins: loading, enabling, disabling, and info."""

    def __init__(
        self,
        plugin_loader: PluginLoader,
        collector_registry: CollectorRegistry,
        doctor_registry: DoctorRegistry,
    ) -> None:
        self._loader = plugin_loader
        self._collector_registry = collector_registry
        self._doctor_registry = doctor_registry
        self._active: dict[str, Plugin] = {}
        self._available: list[dict[str, str | None]] | None = None

    def load_all(self) -> list[Plugin]:
        """Discover and fully load every available plugin."""
        plugins = self._loader.discover_plugins()
        loaded: list[Plugin] = []
        for plugin in plugins:
            if plugin.name in self._active:
                logger.warning(
                    "Plugin '%s' is already active, skipping duplicate", plugin.name
                )
                continue
            try:
                self._activate(plugin)
                loaded.append(plugin)
            except PluginError:
                logger.warning("Failed to load plugin '%s'", plugin.name, exc_info=True)
        return loaded

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a specific plugin by name. Returns True on success."""
        if plugin_name in self._active:
            logger.info("Plugin '%s' is already active", plugin_name)
            return True

        available = self.get_available()
        for meta in available:
            if meta.get("name") == plugin_name:
                path_str = meta.get("path")
                if path_str is None:
                    continue

                plugin = self._loader.load_plugin(Path(path_str))
                if plugin is None:
                    return False
                try:
                    self._activate(plugin)
                    return True
                except PluginError:
                    logger.warning(
                        "Failed to enable plugin '%s'", plugin_name, exc_info=True
                    )
                    return False
        logger.warning("Plugin '%s' not found among available plugins", plugin_name)
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Unload an active plugin. Returns True if active and removed."""
        plugin = self._active.pop(plugin_name, None)
        if plugin is None:
            return False

        try:
            plugin.cleanup()
        except Exception:
            logger.warning(
                "Error during cleanup of plugin '%s'", plugin_name, exc_info=True
            )

        for collector_collector in plugin.register_collectors():
            collector_name = getattr(collector_collector, "name", None)
            if collector_name is not None:
                self._collector_registry.remove(collector_name)

        logger.info("Plugin '%s' disabled", plugin_name)
        return True

    def get_active_plugins(self) -> list[Plugin]:
        """Return a list of currently active plugins."""
        return list(self._active.values())

    def get_available(self) -> list[dict[str, str | None]]:
        """Return metadata for all available (discovered) plugins."""
        if self._available is None:
            self._available = self._loader.get_available_plugins()
        return self._available

    def get_plugin_info(self, plugin_name: str) -> dict[str, Any] | None:
        """Get detailed info about a plugin by name."""
        active = self._active.get(plugin_name)
        if active is not None:
            return {
                "name": active.name,
                "version": active.version,
                "description": active.description,
                "active": True,
                "collectors": [c.name for c in active.register_collectors()],
                "doctor_rules": [
                    r.name for r in active.register_doctor_rules()
                ],
            }

        for meta in self.get_available():
            if meta.get("name") == plugin_name:
                return {
                    "name": meta.get("name"),
                    "version": meta.get("version"),
                    "description": meta.get("description"),
                    "active": False,
                    "collectors": [],
                    "doctor_rules": [],
                }

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _activate(self, plugin: Plugin) -> None:
        """Initialize a plugin and register its collectors and doctor rules."""
        try:
            plugin.initialize()
        except Exception as exc:
            raise PluginError(
                f"initialize() failed for plugin '{plugin.name}': {exc}",
                original=exc,
            ) from exc

        for collector_cls in plugin.register_collectors():
            try:
                collector_instance = collector_cls()
                self._collector_registry.register(collector_instance)
            except Exception as exc:
                logger.warning(
                    "Failed to register collector %s from plugin '%s': %s",
                    getattr(collector_cls, "__name__", collector_cls),
                    plugin.name,
                    exc,
                )

        for rule_cls in plugin.register_doctor_rules():
            try:
                rule_instance = rule_cls()
                self._doctor_registry.register(rule_instance)
            except Exception as exc:
                logger.warning(
                    "Failed to register doctor rule %s from plugin '%s': %s",
                    getattr(rule_cls, "__name__", rule_cls),
                    plugin.name,
                    exc,
                )

        self._active[plugin.name] = plugin
        logger.info("Plugin '%s' (v%s) loaded", plugin.name, plugin.version)
