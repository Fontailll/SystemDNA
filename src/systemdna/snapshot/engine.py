from __future__ import annotations

import logging
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import orjson

from systemdna.collectors.base import CollectorResult
from systemdna.collectors.registry import CollectorRegistry
from systemdna.collectors.runner import CollectorRunner
from systemdna.core.config import Config, ConfigManager
from systemdna.core.exceptions import SnapshotError
from systemdna.models.metadata import SnapshotMetadata
from systemdna.models.snapshot import Snapshot
from systemdna.version import __version__

logger = logging.getLogger(__name__)

_SNAPSHOT_SCHEMA_VERSION = 1


class SnapshotEngine:
    """Orchestrates collector execution and snapshot creation/persistence."""

    def __init__(
        self,
        config: Config | None = None,
        registry: CollectorRegistry | None = None,
        runner: CollectorRunner | None = None,
    ) -> None:
        if config is None:
            config = ConfigManager().config
        self._config = config
        self._registry = registry or CollectorRegistry()
        self._runner = runner or CollectorRunner(
            timeout=30.0,
        )

    @property
    def registry(self) -> CollectorRegistry:
        return self._registry

    @property
    def runner(self) -> CollectorRunner:
        return self._runner

    def _build_metadata(self, duration_ms: int) -> SnapshotMetadata:
        """Construct snapshot metadata with system identifiers."""
        hostname = platform.node()
        return SnapshotMetadata(
            schema_version=_SNAPSHOT_SCHEMA_VERSION,
            application_version=__version__,
            created_at=datetime.now(tz=timezone.utc),
            platform="linux",
            hostname=hostname,
            duration_ms=duration_ms,
        )

    def _map_results(
        self,
        results: list[CollectorResult],
    ) -> dict[str, Any]:
        """Map collector results to Snapshot model field names."""
        field_map: dict[str, str] = {
            "system": "system",
            "hardware": "hardware",
            "network": "network",
            "packages": "packages",
            "services": "services",
            "users": "users",
            "security": "security",
            "configuration": "configuration",
        }
        snapshot_data: dict[str, Any] = {}
        for result in results:
            if not result.success:
                logger.warning(
                    "Skipping collector '%s' due to failure: %s",
                    result.name,
                    result.error,
                )
                continue
            field_name = field_map.get(result.name)
            if field_name and result.data is not None:
                snapshot_data[field_name] = result.data
        return snapshot_data

    def create_snapshot(
        self,
        collector_names: list[str] | None = None,
        notes: str | None = None,
    ) -> Snapshot:
        """Run collectors and assemble a complete Snapshot.

        Args:
            collector_names: Optional list of collector names to run.
                Runs all if None.
            notes: Optional user-provided notes for the snapshot.

        Returns:
            A fully populated Snapshot instance.

        Raises:
            SnapshotError: If the required system collector fails.
        """
        collectors = self._registry.all()
        start_time = time.monotonic()

        results = self._runner.run(collectors, names=collector_names)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        system_result = next((r for r in results if r.name == "system"), None)
        if system_result is None or not system_result.success:
            error_detail = system_result.error if system_result else "not executed"
            raise SnapshotError(
                f"System collector is required but failed: {error_detail}"
            )

        metadata = self._build_metadata(duration_ms=elapsed_ms)
        if notes:
            object.__setattr__(metadata, "notes", notes)

        snapshot_fields = self._map_results(results)
        snapshot_fields["metadata"] = metadata

        try:
            snapshot = Snapshot(**snapshot_fields)
        except Exception as exc:
            raise SnapshotError(
                f"Failed to construct Snapshot from collector results: {exc}",
                original=exc,
            ) from exc

        return snapshot

    def save_snapshot(
        self,
        snapshot: Snapshot,
        path: Path | None = None,
    ) -> Path:
        """Serialize a snapshot to JSON and write it to disk.

        Args:
            snapshot: The snapshot to persist.
            path: Explicit file path. If None, a path is generated from the
                snapshot timestamp inside the configured snapshots directory.

        Returns:
            The path the snapshot was written to.
        """
        if path is None:
            snapshots_dir = self._config.snapshots_dir
            if snapshots_dir is None:
                raise SnapshotError("No snapshots directory configured")
            snapshots_dir.mkdir(parents=True, exist_ok=True)

            timestamp = snapshot.metadata.created_at
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            ts = timestamp.strftime("%Y-%m-%dT%H-%M-%S")
            short_id = snapshot.metadata.snapshot_id[:8]
            filename = f"snapshot-{ts}-{short_id}.json"
            path = snapshots_dir / filename

        try:
            payload = snapshot.model_dump(mode="json")
            raw = orjson.dumps(payload, option=orjson.OPT_INDENT_2)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        except orjson.JSONEncodeError as exc:
            raise SnapshotError(
                f"Failed to serialize snapshot: {exc}",
                original=exc,
            ) from exc
        except OSError as exc:
            raise SnapshotError(
                f"Failed to write snapshot to {path}: {exc}",
                original=exc,
            ) from exc

        logger.info("Snapshot saved to %s", path)
        return path

    @staticmethod
    def load_snapshot(path: Path) -> Snapshot:
        """Deserialize a snapshot from a JSON file.

        Args:
            path: Path to the snapshot JSON file.

        Returns:
            A deserialized Snapshot instance.

        Raises:
            SnapshotError: If the file cannot be read or parsed.
        """
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise SnapshotError(
                f"Snapshot file not found: {path}",
                original=exc,
            ) from exc
        except OSError as exc:
            raise SnapshotError(
                f"Failed to read snapshot file {path}: {exc}",
                original=exc,
            ) from exc

        try:
            payload = orjson.loads(raw)
        except orjson.JSONDecodeError as exc:
            raise SnapshotError(
                f"Failed to parse snapshot JSON from {path}: {exc}",
                original=exc,
            ) from exc

        try:
            snapshot = Snapshot(**payload)
        except Exception as exc:
            raise SnapshotError(
                f"Failed to construct Snapshot from data in {path}: {exc}",
                original=exc,
            ) from exc

        return snapshot
