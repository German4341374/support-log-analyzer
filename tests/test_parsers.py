from datetime import UTC, datetime
from pathlib import Path

import pytest

from support_log_analyzer.exceptions import InputFileError
from support_log_analyzer.models import InputFormat, LogLevel
from support_log_analyzer.parsers import detect_format, parse_file
from support_log_analyzer.parsers.common import parse_level, parse_timestamp


@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    [
        ("sample.log", InputFormat.TEXT),
        ("sample.jsonl", InputFormat.JSONL),
        ("sample.csv", InputFormat.CSV),
    ],
)
def test_detects_supported_formats(
    fixtures_dir: Path, fixture_name: str, expected: InputFormat
) -> None:
    assert detect_format(fixtures_dir / fixture_name) is expected


def test_text_parser_recognizes_common_fields(txt_log: Path) -> None:
    result = parse_file(txt_log)

    assert len(result.entries) == 5
    assert result.entries[0].level is LogLevel.ERROR
    assert result.entries[0].service == "api"
    assert result.entries[0].timestamp == datetime(2026, 7, 29, 9, tzinfo=UTC)


def test_text_parser_handles_bracketed_level_and_service(txt_log: Path) -> None:
    result = parse_file(txt_log)

    warning = result.entries[2]
    assert warning.level is LogLevel.WARNING
    assert warning.service == "worker"


def test_text_parser_keeps_unstructured_lines(txt_log: Path) -> None:
    result = parse_file(txt_log)

    unstructured = result.entries[-1]
    assert unstructured.level is LogLevel.INFO
    assert unstructured.service == "unknown"
    assert unstructured.message == "An unstructured diagnostic line"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("trace", LogLevel.DEBUG),
        ("NOTICE", LogLevel.INFO),
        ("warn", LogLevel.WARNING),
        ("fatal", LogLevel.CRITICAL),
    ],
)
def test_normalizes_level_aliases(raw: str, expected: LogLevel) -> None:
    assert parse_level(raw) is expected


def test_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="unsupported log level"):
        parse_level("emergency")


def test_jsonl_parser_recognizes_field_aliases(jsonl_log: Path) -> None:
    result = parse_file(jsonl_log)

    assert len(result.entries) == 3
    assert result.entries[1].level is LogLevel.WARNING
    assert result.entries[1].service == "worker"
    assert result.entries[2].message.startswith("DNS failure")


def test_jsonl_parser_skips_damaged_lines(jsonl_log: Path) -> None:
    result = parse_file(jsonl_log)

    assert result.skipped_lines == 2
    assert {issue.line_number for issue in result.issues} == {4, 5}


def test_csv_parser_reads_rows(csv_log: Path) -> None:
    result = parse_file(csv_log)

    assert len(result.entries) == 3
    assert result.entries[2].level is LogLevel.CRITICAL
    assert result.entries[2].service == "database"


def test_csv_parser_reports_empty_message(csv_log: Path) -> None:
    result = parse_file(csv_log)

    assert result.skipped_lines == 1
    assert "empty" in result.issues[0].reason


def test_content_detection_wins_over_file_extension(tmp_path: Path) -> None:
    misleading = tmp_path / "events.log"
    misleading.write_text('{"level":"ERROR","message":"timeout"}\n', encoding="utf-8")

    assert detect_format(misleading) is InputFormat.JSONL


def test_missing_file_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(InputFileError, match="does not exist"):
        parse_file(tmp_path / "missing.log")


def test_empty_file_has_clear_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")

    with pytest.raises(InputFileError, match="empty"):
        parse_file(empty)


def test_parses_zulu_timestamp() -> None:
    assert parse_timestamp("2026-07-29T12:30:00Z") == datetime(2026, 7, 29, 12, 30, tzinfo=UTC)


def test_assumes_utc_for_naive_timestamp() -> None:
    assert parse_timestamp("2026-07-29 12:30:00") == datetime(2026, 7, 29, 12, 30, tzinfo=UTC)


def test_parses_unix_timestamp() -> None:
    assert parse_timestamp(0) == datetime(1970, 1, 1, tzinfo=UTC)
