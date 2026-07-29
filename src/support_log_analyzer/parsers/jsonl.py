"""Parser for newline-delimited JSON logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from support_log_analyzer.models import InputFormat, LogEntry, ParseIssue, ParseResult
from support_log_analyzer.parsers.common import mapping_to_entry


def parse_jsonl(path: Path) -> ParseResult:
    """Parse JSON objects independently so one damaged line does not abort a file."""
    entries: list[LogEntry] = []
    issues: list[ParseIssue] = []
    total_lines = 0
    with path.open(encoding="utf-8-sig", errors="replace") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            total_lines = line_number
            if not raw_line.strip():
                continue
            try:
                value: Any = json.loads(raw_line)
                if not isinstance(value, dict):
                    msg = "JSON line must contain an object"
                    raise ValueError(msg)
                entries.append(mapping_to_entry(value, line_number))
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                issues.append(ParseIssue(line_number=line_number, reason=str(error)))
    return ParseResult(
        input_format=InputFormat.JSONL,
        total_lines=total_lines,
        entries=entries,
        issues=issues,
    )
