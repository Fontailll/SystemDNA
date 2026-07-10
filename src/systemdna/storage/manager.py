from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import orjson

from systemdna.core.exceptions import StorageError

logger = logging.getLogger(__name__)

_SNAPSHOT_FILE_PATTERN = re.compile(
    r"^snapshot-(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})-([a-f0-9]{8})\.json$"
)


class SnapshotStorageManager:

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir

    def create_storage(self) -> None:
        try:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                f"Failed to create storage directory {self._storage_dir}: {exc}",
                original=exc,
            ) from exc

    def list_snapshots(self) -> list[dict[str, Any]]:
        if not self._storage_dir.is_dir():
            return []

        entries: list[dict[str, Any]] = []
        for child in sorted(self._storage_dir.iterdir()):
            if not child.is_file():
                continue
            parsed = self._parse_snapshot_id(child.name)
            if parsed is None:
                continue
            try:
                raw = orjson.loads(child.read_bytes())
            except (orjson.JSONDecodeError, OSError):
                logger.exception("Failed to read snapshot file %s", child)
                continue
            metadata = raw.get("metadata", {})
            file_size = child.stat().st_size
            entries.append({
                "id": parsed,
                "timestamp": metadata.get("created_at", ""),
                "hostname": metadata.get("hostname", ""),
                "platform": metadata.get("platform", ""),
                "file_size": file_size,
            })

        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries

    def get_snapshot_path(self, snapshot_id: str) -> Path:
        if not self._storage_dir.is_dir():
            raise StorageError(
                f"Storage directory does not exist: {self._storage_dir}"
            )
        for child in self._storage_dir.iterdir():
            if not child.is_file():
                continue
            parsed = self._parse_snapshot_id(child.name)
            if parsed == snapshot_id:
                return child
        raise StorageError(
            f"No snapshot found with ID '{snapshot_id}' in {self._storage_dir}"
        )

    def delete_snapshot(self, snapshot_id: str) -> bool:
        try:
            path = self.get_snapshot_path(snapshot_id)
        except StorageError:
            return False
        try:
            path.unlink()
            logger.info("Deleted snapshot %s (%s)", snapshot_id, path)
            return True
        except OSError:
            logger.exception(
                "Failed to delete snapshot %s (%s)", snapshot_id, path
            )
            return False

    def clear_all(self) -> bool:
        if not self._storage_dir.is_dir():
            return True
        success = True
        for child in list(self._storage_dir.iterdir()):
            if not child.is_file():
                continue
            if self._parse_snapshot_id(child.name) is not None:
                try:
                    child.unlink()
                except OSError:
                    logger.exception(
                        "Failed to delete snapshot file %s", child
                    )
                    success = False
        return success

    def get_latest(self) -> Path | None:
        if not self._storage_dir.is_dir():
            return None
        candidates: list[tuple[str, Path]] = []
        for child in self._storage_dir.iterdir():
            if not child.is_file():
                continue
            m = _SNAPSHOT_FILE_PATTERN.match(child.name)
            if m:
                candidates.append((m.group(1), child))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def get_snapshot_count(self) -> int:
        if not self._storage_dir.is_dir():
            return 0
        count = 0
        for child in self._storage_dir.iterdir():
            if child.is_file() and self._parse_snapshot_id(child.name) is not None:
                count += 1
        return count

    @staticmethod
    def _parse_snapshot_id(filename: str) -> str | None:
        m = _SNAPSHOT_FILE_PATTERN.match(filename)
        return m.group(2) if m else None
