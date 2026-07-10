from __future__ import annotations

from systemdna.core.config import Config, ConfigManager
from systemdna.diff.engine import DiffEngine
from systemdna.doctor.engine import DoctorEngine
from systemdna.export.engine import ExportEngine
from systemdna.history.engine import HistoryEngine
from systemdna.snapshot.engine import SnapshotEngine
from systemdna.storage.manager import SnapshotStorageManager


def get_config() -> Config:
    return ConfigManager().config


def get_snapshot_engine() -> SnapshotEngine:
    return SnapshotEngine(config=get_config())


def get_storage_manager() -> SnapshotStorageManager:
    config = get_config()
    snapshots_dir = config.snapshots_dir
    if snapshots_dir is None:
        snapshots_dir = config.storage_dir / "snapshots"
    return SnapshotStorageManager(snapshots_dir)


def get_history_engine() -> HistoryEngine:
    return HistoryEngine(get_storage_manager())


def get_diff_engine() -> DiffEngine:
    return DiffEngine()


def get_doctor_engine() -> DoctorEngine:
    return DoctorEngine()


def get_export_engine() -> ExportEngine:
    return ExportEngine()
