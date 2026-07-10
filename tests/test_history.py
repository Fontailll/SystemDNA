from __future__ import annotations

from pathlib import Path

import pytest

from systemdna.history.engine import HistoryEngine
from systemdna.storage.manager import SnapshotStorageManager


@pytest.fixture
def history_engine(snapshot_storage: SnapshotStorageManager) -> HistoryEngine:
    return HistoryEngine(snapshot_storage)


def test_list_snapshots(history_engine: HistoryEngine) -> None:
    snaps = history_engine.list_snapshots()
    assert len(snaps) == 2
    assert snaps[0]["hostname"] == "host-a"


def test_list_snapshots_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty_data")
    engine = HistoryEngine(mgr)
    assert engine.list_snapshots() == []


def test_show_snapshot(history_engine: HistoryEngine) -> None:
    snapshot = history_engine.show_snapshot("aaaaaa01")
    assert snapshot.metadata.snapshot_id == "aaaaaa01"
    assert snapshot.system.os_name == "Linux"


def test_show_snapshot_not_found(history_engine: HistoryEngine) -> None:
    from systemdna.core.exceptions import StorageError

    with pytest.raises(StorageError):
        history_engine.show_snapshot("nonexistent")


def test_delete_snapshot(history_engine: HistoryEngine) -> None:
    assert history_engine.delete_snapshot("aaaaaa01") is True
    assert len(history_engine.list_snapshots()) == 1


def test_delete_snapshot_not_found(history_engine: HistoryEngine) -> None:
    assert history_engine.delete_snapshot("nonexistent") is False


def test_clear_history(history_engine: HistoryEngine) -> None:
    assert history_engine.clear_history() is True
    assert history_engine.list_snapshots() == []


def test_get_latest_snapshot(history_engine: HistoryEngine) -> None:
    latest = history_engine.get_latest_snapshot()
    assert latest is not None
    assert latest.metadata.snapshot_id == "aaaaaa02"


def test_get_latest_snapshot_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    engine = HistoryEngine(mgr)
    assert engine.get_latest_snapshot() is None


def test_get_latest_path(history_engine: HistoryEngine) -> None:
    path = history_engine.get_latest_path()
    assert path is not None
    assert "aaaaaa02" in path.name


def test_get_latest_path_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    engine = HistoryEngine(mgr)
    assert engine.get_latest_path() is None


def test_list_snapshots_entries_have_required_keys(history_engine: HistoryEngine) -> None:
    snaps = history_engine.list_snapshots()
    for entry in snaps:
        assert "id" in entry
        assert "timestamp" in entry
        assert "hostname" in entry
        assert "platform" in entry
        assert "file_size" in entry
