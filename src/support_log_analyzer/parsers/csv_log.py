"""Parser for CSV logs with alias-aware headers."""

from __future__ import annotations

import csv
from pathlib import Path

from support_log_analyzer.models import InputFormat, LogEntry, ParseIssue, ParseResult
from support_log_analyzer.parsers.common import mapping_to_entry


def parse_csv(path: Path) -> ParseResult:
    """Parse CSV rows while reporting malformed records."""
    entries: list[LogEntry] = []
    issues: list[ParseIssue] = []
    total_lines = 0
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream)
        total_lines = 1 if reader.fieldnames else 0
        if not reader.fieldnames:
            return ParseResult(
                input_format=InputFormat.CSV,
                total_lines=total_lines,
                entries=[],
                issues=[ParseIssue(line_number=1, reason="CSV header is missing")],
            )
        for line_number, row in enumerate(reader, start=2):
            total_lines = line_number
            try:
                entries.append(mapping_to_entry(row, line_number))
            except (TypeError, ValueError) as error:
                issues.append(ParseIssue(line_number=line_number, reason=str(error)))
    return ParseResult(
        input_format=InputFormat.CSV,
        total_lines=total_lines,
        entries=entries,
        issues=issues,
    )
