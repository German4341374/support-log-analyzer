import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from support_log_analyzer.exceptions import UnsupportedFormatError
from support_log_analyzer.models import AnalysisReport, ErrorGroup, InputFormat
from support_log_analyzer.reports import write_report


@pytest.fixture
def report() -> AnalysisReport:
    return AnalysisReport(
        input_file=Path("sample.log"),
        input_format=InputFormat.TEXT,
        generated_at=datetime(2026, 7, 29, tzinfo=UTC),
        total_lines=4,
        skipped_lines=0,
        message_count=4,
        error_count=2,
        detected_issues={"timeout": 2},
        top_errors=[
            ErrorGroup(
                normalized="timeout for <email>",
                example="timeout for <EMAIL>",
                count=2,
                services=["api"],
                issue_types=["timeout"],
            )
        ],
        services_by_error={"api": 2},
        first_timestamp=datetime(2026, 7, 29, 9, tzinfo=UTC),
        last_timestamp=datetime(2026, 7, 29, 10, tzinfo=UTC),
        hourly_errors={"2026-07-29T09:00:00Z": 2},
    )


def test_writes_json_report(tmp_path: Path, report: AnalysisReport) -> None:
    output = tmp_path / "report.json"
    write_report(report, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["error_count"] == 2
    assert payload["detected_issues"]["timeout"] == 2


def test_writes_csv_report(tmp_path: Path, report: AnalysisReport) -> None:
    output = tmp_path / "report.csv"
    write_report(report, output)

    with output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert any(row["section"] == "top_error" for row in rows)


def test_writes_markdown_report(tmp_path: Path, report: AnalysisReport) -> None:
    output = tmp_path / "report.md"
    write_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "# Support Log Analysis" in content
    assert "## Hourly Error Distribution" in content


def test_writes_standalone_html_report(tmp_path: Path, report: AnalysisReport) -> None:
    output = tmp_path / "report.html"
    write_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "<!doctype html>" in content
    assert "Most Frequent Errors" in content
    assert "<EMAIL>" not in content
    assert "&lt;EMAIL&gt;" in content


def test_rejects_unsupported_report_extension(tmp_path: Path, report: AnalysisReport) -> None:
    with pytest.raises(UnsupportedFormatError, match="output extension"):
        write_report(report, tmp_path / "report.xml")
