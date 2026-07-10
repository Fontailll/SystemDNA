from __future__ import annotations

from systemdna.schemas.snapshot_schema import CURRENT_SCHEMA_VERSION, validate_snapshot


def _valid_data() -> dict:
    return {
        "metadata": {
            "schema_version": 1,
            "application_version": "0.1.0",
            "created_at": "2025-01-01T00:00:00+00:00",
            "platform": "linux",
            "hostname": "test",
            "duration_ms": 100,
            "snapshot_id": "abc123",
        },
        "system": {
            "os_name": "Linux",
            "os_version": "5.15",
            "architecture": "x86_64",
            "hostname": "test",
            "timezone": "UTC",
            "locale": "C",
            "python_version": "3.11",
        },
    }


def test_valid_snapshot_passes() -> None:
    assert validate_snapshot(_valid_data()) is True


def test_schema_version_constant() -> None:
    assert isinstance(CURRENT_SCHEMA_VERSION, int)
    assert CURRENT_SCHEMA_VERSION >= 1


def test_invalid_data_not_dict() -> None:
    assert validate_snapshot("not a dict") is False
    assert validate_snapshot(42) is False
    assert validate_snapshot(None) is False  # type: ignore[arg-type]


def test_missing_metadata_fails() -> None:
    data = _valid_data()
    del data["metadata"]
    assert validate_snapshot(data) is False


def test_missing_system_fails() -> None:
    data = _valid_data()
    del data["system"]
    assert validate_snapshot(data) is False


def test_missing_required_metadata_keys_fails() -> None:
    data = _valid_data()
    del data["metadata"]["schema_version"]
    assert validate_snapshot(data) is False


def test_missing_required_system_keys_fails() -> None:
    data = _valid_data()
    del data["system"]["os_name"]
    assert validate_snapshot(data) is False


def test_metadata_not_dict_fails() -> None:
    data = _valid_data()
    data["metadata"] = "not a dict"
    assert validate_snapshot(data) is False


def test_system_not_dict_fails() -> None:
    data = _valid_data()
    data["system"] = None  # type: ignore[assignment]
    assert validate_snapshot(data) is False


def test_schema_version_must_be_int() -> None:
    data = _valid_data()
    data["metadata"]["schema_version"] = "1"
    assert validate_snapshot(data) is False


def test_schema_version_must_be_positive() -> None:
    data = _valid_data()
    data["metadata"]["schema_version"] = 0
    assert validate_snapshot(data) is False


def test_schema_version_negative_fails() -> None:
    data = _valid_data()
    data["metadata"]["schema_version"] = -1
    assert validate_snapshot(data) is False


def test_valid_with_extra_fields_passes() -> None:
    data = _valid_data()
    data["extra_field"] = "whatever"
    data["metadata"]["extra"] = True
    assert validate_snapshot(data) is True


def test_all_required_metadata_keys_checked() -> None:
    required = {"schema_version", "application_version", "created_at", "platform", "hostname", "duration_ms", "snapshot_id"}
    for key in required:
        data = _valid_data()
        del data["metadata"][key]
        assert validate_snapshot(data) is False, f"missing key '{key}' should fail"


def test_all_required_system_keys_checked() -> None:
    required = {"os_name", "os_version", "architecture", "hostname", "timezone", "locale", "python_version"}
    for key in required:
        data = _valid_data()
        del data["system"][key]
        assert validate_snapshot(data) is False, f"missing system key '{key}' should fail"


def test_empty_dict_fails() -> None:
    assert validate_snapshot({}) is False
