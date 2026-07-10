CURRENT_SCHEMA_VERSION = 1

_REQUIRED_TOP_LEVEL_KEYS = {"metadata", "system"}
_REQUIRED_METADATA_KEYS = {
    "schema_version",
    "application_version",
    "created_at",
    "platform",
    "hostname",
    "duration_ms",
    "snapshot_id",
}
_REQUIRED_SYSTEM_KEYS = {
    "os_name",
    "os_version",
    "architecture",
    "hostname",
    "timezone",
    "locale",
    "python_version",
}


def validate_snapshot(data: dict[str, object]) -> bool:
    if not isinstance(data, dict):
        return False

    if not _REQUIRED_TOP_LEVEL_KEYS.issubset(data.keys()):
        return False

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return False
    if not _REQUIRED_METADATA_KEYS.issubset(metadata.keys()):
        return False

    system = data.get("system")
    if not isinstance(system, dict):
        return False
    if not _REQUIRED_SYSTEM_KEYS.issubset(system.keys()):
        return False

    schema_version = metadata.get("schema_version")
    return not (not isinstance(schema_version, int) or schema_version < 1)
