"""Parser for common single-line text log layouts."""

from __future__ import annotations

import re
from pathlib import Path

from support_log_analyzer.models import InputFormat, LogEntry, LogLevel, ParseResult
from support_log_analyzer.parsers.common import parse_level, parse_timestamp

_TIMESTAMP = r"\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+(?:Z)?"
_LEVEL = r"TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|ERR|FATAL|CRITICAL"
_STRUCTURED_LINE = re.compile(
    rf"^(?P<timestamp>{_TIMESTAMP})\s+"
    rf"(?:\[(?P<bracket_level>{_LEVEL})\]|(?P<level>{_LEVEL}))\s+"
    r"(?:\[(?P<bracket_service>[\w.-]+)\]|(?P<service>[\w.-]+))"
    r"(?:\s*[-:|]\s*|\s+)(?P<message>.+)$",
    re.IGNORECASE,
)
_WITHOUT_SERVICE = re.compile(
    rf"^(?P<timestamp>{_TIMESTAMP})\s+"
    rf"(?:\[(?P<bracket_level>{_LEVEL})\]|(?P<level>{_LEVEL}))"
    r"(?:\s*[-:|]\s*|\s+)(?P<message>.+)$",
    re.IGNORECASE,
)
_LEVEL_ONLY = re.compile(
    rf"^(?:\[(?P<bracket_level>{_LEVEL})\]|(?P<level>{_LEVEL}))"
    r"(?:\s*[-:|]\s*|\s+)(?P<message>.+)$",
    re.IGNORECASE,
)


def _entry_from_match(match: re.Match[str], line_number: int) -> LogEntry:
    groups = match.groupdict()
    raw_level = groups.get("bracket_level") or groups.get("level")
    return LogEntry(
        timestamp=parse_timestamp(groups.get("timestamp")),
        level=parse_level(raw_level),
        service=groups.get("bracket_service") or groups.get("service") or "unknown",
        message=groups["message"],
        source_line=line_number,
    )


def parse_text(path: Path) -> ParseResult:
    """Parse structured text while retaining unstructured messages as INFO."""
    entries: list[LogEntry] = []
    total_lines = 0
    with path.open(encoding="utf-8-sig", errors="replace") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            total_lines = line_number
            line = raw_line.strip()
            if not line:
                continue
            match = (
                _STRUCTURED_LINE.match(line)
                or _WITHOUT_SERVICE.match(line)
                or _LEVEL_ONLY.match(line)
            )
            if match:
                entries.append(_entry_from_match(match, line_number))
            else:
                entries.append(
                    LogEntry(
                        level=LogLevel.INFO,
                        service="unknown",
                        message=line,
                        source_line=line_number,
                    )
                )
    return ParseResult(input_format=InputFormat.TEXT, total_lines=total_lines, entries=entries)
