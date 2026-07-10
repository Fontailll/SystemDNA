from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from systemdna.collectors.base import CollectorResult
from systemdna.core.exceptions import SnapshotError
from systemdna.models.system import SystemInfo
from systemdna.snapshot.engine import SnapshotEngine


def test_engine_creates_snapshot_with_metadata() -> None:
    engine = SnapshotEngine()
    assert engine.registry is not None
    assert engine.runner is not None


def test_create_snapshot_fails_without_system_collector() -> None:
    engine = SnapshotEngine()
    engine.registry._collectors.clear()
    with pytest.raises(SnapshotError, match="System collector is required but failed"):
        engine.create_snapshot()


def test_create_snapshot_handles_collector_failures_gracefully() -> None:
    with patch("systemdna.snapshot.engine.platform.node", return_value="h"):
        engine = SnapshotEngine()

        mock_system = MagicMock()
        mock_system.name = "system"
        mock_system.collect.return_value = SystemInfo(
            os_name="Linux", os_version="1", architecture="x86",
            hostname="h", timezone="U", locale="C", python_version="3",
        )

        mock_bad = MagicMock()
        mock_bad.name = "hardware"
        mock_bad.collect.side_effect = RuntimeError("oops")

        engine.registry._collectors = {
            "system": mock_system,
            "hardware": mock_bad,
        }

        snapshot = engine.create_snapshot()
        assert snapshot is not None
        assert snapshot.metadata.hostname == "h"
        assert snapshot.system is not None
        assert snapshot.hardware is None


def test_snapshot_save_load_roundtrip(tmp_path: Path) -> None:
    engine = SnapshotEngine()

    mock_system = MagicMock()
    mock_system.name = "system"
    mock_system.collect.return_value = SystemInfo(
        os_name="Linux", os_version="5.15", architecture="x86_64",
        hostname="test-host", timezone="UTC", locale="C", python_version="3.11",
    )
    engine.registry._collectors = {"system": mock_system}

    snapshot = engine.create_snapshot(notes="roundtrip test")
    save_path = engine.save_snapshot(snapshot, path=tmp_path / "test_snap.json")

    assert save_path.exists()

    loaded = SnapshotEngine.load_snapshot(save_path)
    assert loaded.metadata.snapshot_id == snapshot.metadata.snapshot_id
    assert loaded.system.os_name == "Linux"
    assert loaded.metadata.notes == "roundtrip test"


def test_save_snapshot_without_path_uses_config(tmp_path: Path) -> None:
    from systemdna.core.config import Config

    config = Config(storage_dir=tmp_path)
    engine = SnapshotEngine(config=config)

    mock_system = MagicMock()
    mock_system.name = "system"
    mock_system.collect.return_value = SystemInfo(
        os_name="Linux", os_version="1", architecture="x86",
        hostname="h", timezone="U", locale="C", python_version="3",
    )
    engine.registry._collectors = {"system": mock_system}

    snapshot = engine.create_snapshot()
    path = engine.save_snapshot(snapshot)
    assert path.exists()
    assert path.parent == config.snapshots_dir


def test_load_snapshot_file_not_found() -> None:
    with pytest.raises(SnapshotError, match="Snapshot file not found"):
        SnapshotEngine.load_snapshot(Path("/nonexistent/snap.json"))


def test_load_snapshot_invalid_json(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not json", encoding="utf-8")
    with pytest.raises(SnapshotError, match="Failed to parse snapshot JSON"):
        SnapshotEngine.load_snapshot(bad_file)


def test_load_snapshot_invalid_model(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"metadata": {}}', encoding="utf-8")
    with pytest.raises(SnapshotError, match="Failed to construct Snapshot from data"):
        SnapshotEngine.load_snapshot(bad_file)


def test_metadata_populated_correctly() -> None:
    engine = SnapshotEngine()

    mock_system = MagicMock()
    mock_system.name = "system"
    mock_system.collect.return_value = SystemInfo(
        os_name="Linux", os_version="1", architecture="x86",
        hostname="h", timezone="U", locale="C", python_version="3",
    )
    engine.registry._collectors = {"system": mock_system}

    with patch("systemdna.snapshot.engine.platform.node", return_value="custom-host"):
        snapshot = engine.create_snapshot()

    assert snapshot.metadata.hostname == "custom-host"
    assert snapshot.metadata.platform == "linux"
    assert snapshot.metadata.schema_version == 1
    assert snapshot.metadata.application_version is not None
    assert snapshot.metadata.duration_ms >= 0


def test_save_snapshot_os_error(tmp_path: Path) -> None:
    engine = SnapshotEngine()

    mock_system = MagicMock()
    mock_system.name = "system"
    mock_system.collect.return_value = SystemInfo(
        os_name="Linux", os_version="1", architecture="x86",
        hostname="h", timezone="U", locale="C", python_version="3",
    )
    engine.registry._collectors = {"system": mock_system}

    snapshot = engine.create_snapshot()

    with patch.object(Path, "write_bytes", side_effect=OSError("denied")):
        with pytest.raises(SnapshotError, match="Failed to write snapshot"):
            engine.save_snapshot(snapshot, path=tmp_path / "fail.json")


def test_engine_config_none_falls_back_to_default() -> None:
    engine = SnapshotEngine(config=None)
    assert engine._config is not None
