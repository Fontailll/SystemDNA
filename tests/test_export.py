from __future__ import annotations

import json
from pathlib import Path

from systemdna.export.engine import ExportEngine
from systemdna.models.snapshot import Snapshot


def _check_has_metadata(content: str) -> None:
    assert "Snapshot ID" in content
    assert "abc12345" in content
    assert "test-host" in content


def test_json_export_valid_json(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_json(sample_snapshot_data)
    parsed = json.loads(result)
    assert parsed["metadata"]["snapshot_id"] == "abc12345"
    assert parsed["system"]["kernel"] == "5.15.0-100-generic"


def test_json_export_includes_metadata(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_json(sample_snapshot_data)
    parsed = json.loads(result)
    assert "metadata" in parsed
    assert parsed["metadata"]["hostname"] == "test-host"
    assert parsed["metadata"]["platform"] == "linux"


def test_json_export_writes_file(sample_snapshot_data: Snapshot, tmp_path: Path) -> None:
    engine = ExportEngine()
    out = tmp_path / "export.json"
    engine.export_json(sample_snapshot_data, path=out)
    assert out.exists()
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["metadata"]["snapshot_id"] == "abc12345"


def test_markdown_export_well_formed(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_markdown(sample_snapshot_data)
    assert result.startswith("#")
    assert "SystemDNA Snapshot Report" in result
    assert "|" in result
    assert "---" in result


def test_markdown_export_has_sections(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_markdown(sample_snapshot_data)
    assert "## Snapshot Information" in result
    assert "## System Information" in result
    assert "## Hardware Information" in result


def test_markdown_export_includes_metadata(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_markdown(sample_snapshot_data)
    _check_has_metadata(result)


def test_markdown_export_writes_file(sample_snapshot_data: Snapshot, tmp_path: Path) -> None:
    engine = ExportEngine()
    out = tmp_path / "export.md"
    engine.export_markdown(sample_snapshot_data, path=out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Snapshot ID" in content


def test_html_export_well_formed(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_html(sample_snapshot_data)
    assert "<!DOCTYPE html>" in result
    assert "<html" in result
    assert "</html>" in result


def test_html_export_has_basic_structure(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_html(sample_snapshot_data)
    assert "<head>" in result
    assert "<body>" in result
    assert "<style>" in result
    assert "<h1>" in result
    assert "<table>" in result


def test_html_export_includes_metadata(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_html(sample_snapshot_data)
    assert "Snapshot ID" in result
    assert "abc12345" in result


def test_html_export_writes_file(sample_snapshot_data: Snapshot, tmp_path: Path) -> None:
    engine = ExportEngine()
    out = tmp_path / "export.html"
    engine.export_html(sample_snapshot_data, path=out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


def test_all_exports_have_metadata(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    json_out = engine.export_json(sample_snapshot_data)
    md_out = engine.export_markdown(sample_snapshot_data)
    html_out = engine.export_html(sample_snapshot_data)
    assert "abc12345" in json_out
    assert "abc12345" in md_out
    assert "abc12345" in html_out


def test_json_export_contains_system_info(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_json(sample_snapshot_data)
    parsed = json.loads(result)
    assert parsed["system"]["os_name"] == "Linux"
    assert parsed["system"]["architecture"] == "x86_64"


def test_markdown_export_contains_tables(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_markdown(sample_snapshot_data)
    assert result.count("|") >= 10
    assert result.count("---") >= 1


def test_html_export_title(sample_snapshot_data: Snapshot) -> None:
    engine = ExportEngine()
    result = engine.export_html(sample_snapshot_data)
    assert "<title>" in result
    assert "test-host" in result
