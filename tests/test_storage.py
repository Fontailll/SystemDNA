from __future__ import annotations

from pathlib import Path

import orjson

from systemdna.core.exceptions import StorageError
from systemdna.storage.manager import SnapshotStorageManager


def test_create_storage_directory(tmp_path: Path) -> None:
    storage_dir = tmp_path / "new_storage"
    mgr = SnapshotStorageManager(storage_dir)
    assert not storage_dir.exists()
    mgr.create_storage()
    assert storage_dir.is_dir()


def test_create_storage_idempotent(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    mgr = SnapshotStorageManager(storage_dir)
    mgr.create_storage()
    assert storage_dir.is_dir()


def test_list_snapshots_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    assert mgr.list_snapshots() == []


def test_list_snapshots_with_files(snapshot_storage: SnapshotStorageManager) -> None:
    snaps = snapshot_storage.list_snapshots()
    assert len(snaps) == 2


def test_list_snapshots_sorted_by_timestamp(snapshot_storage: SnapshotStorageManager) -> None:
    snaps = snapshot_storage.list_snapshots()
    assert len(snaps) >= 2
    timestamps = [s["timestamp"] for s in snaps]
    assert timestamps == sorted(timestamps, reverse=True)


def test_list_snapshots_metadata_fields(snapshot_storage: SnapshotStorageManager) -> None:
    snaps = snapshot_storage.list_snapshots()
    for entry in snaps:
        assert "id" in entry
        assert "timestamp" in entry
        assert "hostname" in entry
        assert "platform" in entry
        assert "file_size" in entry
        assert entry["hostname"] == "host-a"


def test_parse_snapshot_id_valid() -> None:
    mgr = SnapshotStorageManager(Path("/tmp"))
    result = mgr._parse_snapshot_id("snapshot-2025-06-15T10-00-00-aaaaaa01.json")
    assert result == "aaaaaa01"


def test_parse_snapshot_id_invalid() -> None:
    mgr = SnapshotStorageManager(Path("/tmp"))
    assert mgr._parse_snapshot_id("random.file.json") is None
    assert mgr._parse_snapshot_id("snapshot-bad.json") is None
    assert mgr._parse_snapshot_id(".json") is None


def test_get_snapshot_path_found(snapshot_storage: SnapshotStorageManager) -> None:
    path = snapshot_storage.get_snapshot_path("aaaaaa01")
    assert path.exists()
    assert "aaaaaa01" in path.name


def test_get_snapshot_path_not_found(snapshot_storage: SnapshotStorageManager) -> None:
    import pytest

    with pytest.raises(StorageError, match="No snapshot found"):
        snapshot_storage.get_snapshot_path("nonexistent")


def test_get_snapshot_path_no_storage(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "nonexistent")
    import pytest

    with pytest.raises(StorageError, match="Storage directory does not exist"):
        mgr.get_snapshot_path("abc")


def test_delete_snapshot_exists(snapshot_storage: SnapshotStorageManager) -> None:
    assert snapshot_storage.delete_snapshot("aaaaaa01") is True
    assert len(snapshot_storage.list_snapshots()) == 1


def test_delete_snapshot_not_found(snapshot_storage: SnapshotStorageManager) -> None:
    assert snapshot_storage.delete_snapshot("nonexistent") is False


def test_clear_all(snapshot_storage: SnapshotStorageManager) -> None:
    assert snapshot_storage.clear_all() is True
    assert len(snapshot_storage.list_snapshots()) == 0


def test_clear_all_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    assert mgr.clear_all() is True


def test_get_latest(snapshot_storage: SnapshotStorageManager) -> None:
    latest = snapshot_storage.get_latest()
    assert latest is not None
    data = orjson.loads(latest.read_bytes())
    assert data["metadata"]["snapshot_id"] == "aaaaaa02"


def test_get_latest_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    assert mgr.get_latest() is None


def test_get_snapshot_count(snapshot_storage: SnapshotStorageManager) -> None:
    assert snapshot_storage.get_snapshot_count() == 2


def test_get_snapshot_count_empty(tmp_path: Path) -> None:
    mgr = SnapshotStorageManager(tmp_path / "empty")
    assert mgr.get_snapshot_count() == 0


def test_list_snapshots_skips_non_snapshot_files(tmp_path: Path) -> None:
    storage_dir = tmp_path / "mixed"
    storage_dir.mkdir()
    (storage_dir / "readme.txt").write_text("hello", encoding="utf-8")

    snap = {
        "metadata": {
            "schema_version": 1, "application_version": "0.1.0",
            "created_at": "2025-01-01T00:00:00+00:00",
            "platform": "linux", "hostname": "h", "duration_ms": 0,
            "snapshot_id": "deadbeef",
        },
        "system": {
            "os_name": "L", "os_version": "1", "architecture": "x",
            "hostname": "h", "timezone": "U", "locale": "C", "python_version": "3",
        },
    }
    (storage_dir / "snapshot-2025-01-01T00-00-00-deadbeef.json").write_text(
        orjson.dumps(snap).decode(), encoding="utf-8",
    )

    mgr = SnapshotStorageManager(storage_dir)
    snaps = mgr.list_snapshots()
    assert len(snaps) == 1
    assert snaps[0]["id"] == "deadbeef"


def test_storage_dir_property(tmp_path: Path) -> None:
    p = tmp_path / "x"
    mgr = SnapshotStorageManager(p)
    assert mgr.storage_dir == p


def test_get_snapshot_path_ignores_directories(snapshot_storage: SnapshotStorageManager) -> None:
    (snapshot_storage.storage_dir / "subdir").mkdir()
    path = snapshot_storage.get_snapshot_path("aaaaaa01")
    assert path.exists()
    assert path.is_file()


def test_parse_snapshot_id_edge_cases() -> None:
    mgr = SnapshotStorageManager(Path("/tmp"))
    assert mgr._parse_snapshot_id("snapshot-1970-01-01T00-00-00-00000000.json") == "00000000"
    assert mgr._parse_snapshot_id("") is None
