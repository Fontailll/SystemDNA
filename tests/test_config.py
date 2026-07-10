from __future__ import annotations

import json
from pathlib import Path

from systemdna.core.config import Config, ConfigManager, _default_config_dir, _default_storage_dir
from systemdna.core.exceptions import ConfigError


def test_default_config_values() -> None:
    cfg = Config()
    assert cfg.plugins_enabled is True
    assert cfg.log_level == "WARNING"
    assert cfg.max_snapshots == 100
    assert cfg.plugin_dirs == []
    assert cfg.snapshots_dir is not None
    assert isinstance(cfg.storage_dir, Path)


def test_snapshots_dir_defaults_to_storage_subdir() -> None:
    cfg = Config()
    assert cfg.snapshots_dir == cfg.storage_dir / "snapshots"


def test_config_manager_loads_defaults_when_no_file(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    cfg = mgr.load()
    assert isinstance(cfg, Config)
    assert cfg.max_snapshots == 100


def test_config_manager_saves_and_reloads(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    original = mgr.load()
    original.max_snapshots = 42
    original.log_level = "DEBUG"
    mgr.save(original)

    mgr2 = ConfigManager(config_dir)
    reloaded = mgr2.load()
    assert reloaded.max_snapshots == 42
    assert reloaded.log_level == "DEBUG"


def test_config_file_created_on_first_load(config_dir: Path) -> None:
    config_path = config_dir / "config.json"
    assert not config_path.exists()
    mgr = ConfigManager(config_dir)
    mgr.load()
    assert config_path.exists()


def test_config_manager_reset(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    cfg = mgr.load()
    cfg.max_snapshots = 999
    mgr.save(cfg)

    mgr.reset()
    assert mgr.config.max_snapshots == 100


def test_config_path_resolution() -> None:
    mgr = ConfigManager()
    assert str(mgr._config_path).endswith("config.json")


def test_load_invalid_json_raises_error(config_dir: Path) -> None:
    config_path = config_dir / "config.json"
    config_path.write_text("not valid json", encoding="utf-8")
    mgr = ConfigManager(config_dir)
    import pytest

    with pytest.raises(ConfigError):
        mgr.load()


def test_load_invalid_field_type_raises_error(config_dir: Path) -> None:
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps({"max_snapshots": "not-an-int"}), encoding="utf-8")
    mgr = ConfigManager(config_dir)
    import pytest

    with pytest.raises(ConfigError):
        mgr.load()


def test_save_no_config_raises_error(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    import pytest

    with pytest.raises(ConfigError, match="No config to save"):
        mgr.save(None)


def test_custom_storage_dir_persists(config_dir: Path) -> None:
    custom = Path("/custom/storage")
    cfg = Config(storage_dir=custom)
    assert cfg.storage_dir == custom
    assert cfg.snapshots_dir == custom / "snapshots"


def test_config_property_caches(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    c1 = mgr.config
    c2 = mgr.config
    assert c1 is c2


def test_config_manager_config_dir_property(config_dir: Path) -> None:
    mgr = ConfigManager(config_dir)
    assert mgr._config_dir == config_dir
    assert mgr._config_path == config_dir / "config.json"


def test_default_config_dir_is_callable() -> None:
    result = _default_config_dir()
    assert isinstance(result, Path)


def test_default_storage_dir_is_callable() -> None:
    result = _default_storage_dir()
    assert isinstance(result, Path)
