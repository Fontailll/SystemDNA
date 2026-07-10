from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import BaseModel, Field

from systemdna.core.exceptions import ConfigError

APP_NAME = "SystemDNA"


def _default_storage_dir() -> Path:
    return Path.home() / ".local" / "share" / APP_NAME


def _default_config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


class Config(BaseModel):
    storage_dir: Path = Field(default_factory=_default_storage_dir)
    snapshots_dir: Path | None = Field(default=None)
    plugins_enabled: bool = Field(default=True)
    plugin_dirs: list[Path] = Field(default_factory=list)
    log_level: str = Field(default="WARNING")
    max_snapshots: int = Field(default=100, ge=1)

    def model_post_init(self, __context: object) -> None:
        if self.snapshots_dir is None:
            object.__setattr__(self, "snapshots_dir", self.storage_dir / "snapshots")


class ConfigManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or _default_config_dir()
        self._config_path = self._config_dir / "config.json"
        self._config: Config | None = None

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self) -> Config:
        if self._config_path.exists():
            try:
                raw = json.loads(self._config_path.read_text(encoding="utf-8"))
                self._config = Config(**raw)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ConfigError(
                    f"Failed to parse config at {self._config_path}",
                    original=exc,
                ) from exc
        else:
            self._config = Config()
            self.save(self._config)
        return self._config

    def save(self, config: Config | None = None) -> None:
        cfg = config or self._config
        if cfg is None:
            raise ConfigError("No config to save")
        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = cfg.model_dump(mode="json")
        serialised: dict[str, object] = {}
        for key, value in data.items():
            if isinstance(value, str) and key.endswith("_dir"):
                serialised[key] = value
            else:
                serialised[key] = value
        self._config_path.write_text(
            json.dumps(serialised, indent=2),
            encoding="utf-8",
        )

    def reset(self) -> Config:
        self._config = Config()
        self.save(self._config)
        return self._config
