from __future__ import annotations

from pathlib import Path
from typing import Any

from systemdna.models.snapshot import Snapshot
from systemdna.snapshot.engine import SnapshotEngine
from systemdna.storage.manager import SnapshotStorageManager


class HistoryEngine:

    def __init__(self, storage_manager: SnapshotStorageManager) -> None:
        self._storage = storage_manager

    def list_snapshots(self) -> list[dict[str, Any]]:
        return self._storage.list_snapshots()

    def show_snapshot(self, snapshot_id: str) -> Snapshot:
        path = self._storage.get_snapshot_path(snapshot_id)
        return SnapshotEngine.load_snapshot(path)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        return self._storage.delete_snapshot(snapshot_id)

    def clear_history(self) -> bool:
        return self._storage.clear_all()

    def get_latest_snapshot(self) -> Snapshot | None:
        latest = self._storage.get_latest()
        if latest is None:
            return None
        return SnapshotEngine.load_snapshot(latest)

    def get_latest_path(self) -> Path | None:
        return self._storage.get_latest()
