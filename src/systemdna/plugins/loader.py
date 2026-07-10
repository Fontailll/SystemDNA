from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from types import ModuleType

from systemdna.core.exceptions import PluginError
from systemdna.plugins.base import Plugin

logger = logging.getLogger(__name__)


class PluginLoader:
    """Discovers and loads plugins from filesystem directories."""

    def __init__(self, plugin_dirs: list[Path]) -> None:
        self._plugin_dirs = plugin_dirs

    def discover_plugins(self) -> list[Plugin]:
        """Scan plugin dirs, import modules, instantiate Plugin subclasses."""
        plugins: list[Plugin] = []
        for directory in self._plugin_dirs:
            if not directory.is_dir():
                logger.warning("Plugin directory does not exist: %s", directory)
                continue
            for entry in directory.iterdir():
                plugin = self._load_entry(entry)
                if plugin is not None:
                    plugins.append(plugin)
        return plugins

    def load_plugin(self, plugin_path: Path) -> Plugin | None:
        """Load a single plugin from a file or package path."""
        plugin = self._load_entry(plugin_path)
        return plugin

    def get_available_plugins(self) -> list[dict[str, str | None]]:
        """Return metadata about discovered plugins without fully loading them."""
        results: list[dict[str, str | None]] = []
        for directory in self._plugin_dirs:
            if not directory.is_dir():
                continue
            for entry in directory.iterdir():
                if entry.suffix == ".py" and entry.name != "__init__.py":
                    module = self._import_module_from_file(entry)
                    if module is None:
                        continue
                    for _, cls in inspect.getmembers(module, inspect.isclass):
                        if _is_plugin_subclass(cls) and cls is not Plugin:
                            results.append(
                                {
                                    "name": getattr(cls, "name", None),
                                    "version": getattr(cls, "version", None),
                                    "description": getattr(cls, "description", None),
                                    "path": str(entry),
                                }
                            )
                elif entry.is_dir() and (entry / "__init__.py").exists():
                    package_module = self._import_package(entry)
                    if package_module is None:
                        continue
                    for _, cls in inspect.getmembers(package_module, inspect.isclass):
                        if _is_plugin_subclass(cls) and cls is not Plugin:
                            results.append(
                                {
                                    "name": getattr(cls, "name", None),
                                    "version": getattr(cls, "version", None),
                                    "description": getattr(cls, "description", None),
                                    "path": str(entry),
                                }
                            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_entry(self, entry: Path) -> Plugin | None:
        """Load a plugin from a file or package directory entry."""
        if entry.suffix == ".py" and entry.name != "__init__.py":
            module = self._import_module_from_file(entry)
        elif entry.is_dir() and (entry / "__init__.py").exists():
            module = self._import_package(entry)
        else:
            return None

        if module is None:
            return None

        return self._instantiate_plugin_from_module(module)

    def _instantiate_plugin_from_module(self, module: ModuleType) -> Plugin | None:
        """Find the first Plugin subclass in *module* and instantiate it."""
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if _is_plugin_subclass(cls) and cls is not Plugin:
                try:
                    return self._safe_instantiate(cls)
                except PluginError:
                    return None
        return None

    @staticmethod
    def _safe_instantiate(plugin_cls: type[Plugin]) -> Plugin:
        """Instantiate a plugin class after validating required attributes."""
        missing = [
            attr
            for attr in ("name", "version", "description")
            if not hasattr(plugin_cls, attr)
            or inspect.isfunction(getattr(plugin_cls, attr))
            or inspect.ismethod(getattr(plugin_cls, attr))
        ]
        if missing:
            raise PluginError(
                f"Plugin class {plugin_cls.__qualname__} is missing required "
                f"attributes: {', '.join(missing)}"
            )
        try:
            instance: Plugin = plugin_cls()
        except Exception as exc:
            raise PluginError(
                f"Failed to instantiate plugin {plugin_cls.__qualname__}: {exc}",
                original=exc,
            ) from exc
        return instance

    @staticmethod
    def _import_module_from_file(path: Path) -> ModuleType | None:
        """Import a single .py file as a module."""
        module_name = f"_systemdna_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            logger.warning("Cannot create module spec for %s", path)
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            logger.warning(
                "Failed to import plugin module %s", path, exc_info=True
            )
            sys.modules.pop(module_name, None)
            return None
        return module

    @staticmethod
    def _import_package(package_dir: Path) -> ModuleType | None:
        """Import a package directory (directory with __init__.py) as a module."""
        module_name = f"_systemdna_plugin_{package_dir.name}"
        init_path = package_dir / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            module_name, init_path, submodule_search_locations=[str(package_dir)]
        )
        if spec is None or spec.loader is None:
            logger.warning("Cannot create module spec for package %s", package_dir)
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            logger.warning(
                "Failed to import plugin package %s", package_dir, exc_info=True
            )
            sys.modules.pop(module_name, None)
            return None
        return module


def _is_plugin_subclass(cls: type) -> bool:
    """Return True if *cls* is a concrete subclass of Plugin."""
    return (
        inspect.isclass(cls)
        and issubclass(cls, Plugin)
        and cls is not Plugin
        and not inspect.isabstract(cls)
    )
