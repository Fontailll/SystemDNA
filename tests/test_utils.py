from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from systemdna.utils.hash import hash_bytes, hash_file
from systemdna.utils.system import (
    detect_platform,
    get_architecture,
    get_hostname,
    get_os_name,
    get_os_version,
    get_python_version,
    get_timezone,
    get_username,
)
from systemdna.utils.time import format_timestamp, parse_timestamp, timestamp_to_filename


def test_hash_bytes_known_value() -> None:
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert hash_bytes(data) == expected


def test_hash_bytes_empty() -> None:
    expected = hashlib.sha256(b"").hexdigest()
    assert hash_bytes(b"") == expected


def test_hash_file_known_value(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    content = b"hello file"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert hash_file(f) == expected


def test_hash_file_large(tmp_path: Path) -> None:
    f = tmp_path / "large.bin"
    content = b"a" * 100000
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert hash_file(f) == expected


def test_format_timestamp_with_tz() -> None:
    dt = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = format_timestamp(dt)
    assert "2025-06-15T10:30:00" in result
    assert "+00:00" in result


def test_format_timestamp_without_tz() -> None:
    dt = datetime(2025, 6, 15, 10, 30, 0)
    result = format_timestamp(dt)
    assert "+00:00" in result


def test_parse_timestamp_with_tz() -> None:
    result = parse_timestamp("2025-06-15T10:30:00+00:00")
    assert result.year == 2025
    assert result.month == 6
    assert result.day == 15
    assert result.tzinfo is not None


def test_parse_timestamp_without_tz() -> None:
    result = parse_timestamp("2025-06-15T10:30:00")
    assert result.tzinfo is not None
    assert result.tzinfo == timezone.utc


def test_timestamp_to_filename() -> None:
    dt = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = timestamp_to_filename(dt)
    assert result == "20250615T103000Z"


def test_timestamp_to_filename_without_tz() -> None:
    dt = datetime(2025, 6, 15, 10, 30, 0)
    result = timestamp_to_filename(dt)
    assert result == "20250615T103000Z"


def test_timestamp_to_filename_roundtrip() -> None:
    original = datetime(2025, 12, 25, 23, 59, 59, tzinfo=timezone.utc)
    filename = timestamp_to_filename(original)
    date_part = filename[:8]
    time_part = filename[9:15]
    iso = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}+00:00"
    parsed = parse_timestamp(iso)
    assert parsed.year == original.year
    assert parsed.month == original.month
    assert parsed.day == original.day
    assert parsed.hour == original.hour
    assert parsed.minute == original.minute


def test_detect_platform() -> None:
    result = detect_platform()
    assert isinstance(result, str)
    assert result in ("linux", "windows", "macos")


def test_get_hostname() -> None:
    result = get_hostname()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_username() -> None:
    result = get_username()
    assert isinstance(result, str)


def test_get_python_version() -> None:
    result = get_python_version()
    assert isinstance(result, str)
    assert result.startswith("3.")


def test_get_architecture() -> None:
    result = get_architecture()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_os_name() -> None:
    result = get_os_name()
    assert isinstance(result, str)


def test_get_os_version() -> None:
    result = get_os_version()
    assert isinstance(result, str)


def test_get_timezone() -> None:
    result = get_timezone()
    assert isinstance(result, str)
    assert len(result) > 0
