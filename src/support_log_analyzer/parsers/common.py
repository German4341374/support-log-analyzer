"""Shared field recognition and normalization for structured parsers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from support_log_analyzer.models import LogEntry, LogLevel

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "timestamp": ("timestamp", "time", "datetime", "date", "@timestamp", "created_at"),
    "level": ("level", "severity", "log_level", "loglevel"),
    "service": ("service", "app", "application", "component", "logger", "source"),
    "message": ("message", "msg", "event", "text", "detail", "description"),
}

LEVEL_ALIASES: dict[str, LogLevel] = {
    "TRACE": LogLevel.DEBUG,
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "NOTICE": LogLevel.INFO,
    "WARN": LogLevel.WARNING,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
    "ERR": LogLevel.ERROR,
    "FATAL": LogLevel.CRITICAL,
    "CRITICAL": LogLevel.CRITICAL,
}


def parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 or Unix timestamp into an aware UTC datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC)
    text = str(value).strip()
    if text.isdigit():
        return datetime.fromtimestamp(float(text), tz=UTC)
    candidate = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_level(value: object) -> LogLevel:
    """Normalize common severity aliases."""
    if value is None or str(value).strip() == "":
        return LogLevel.INFO
    normalized = str(value).strip().upper()
    try:
        return LEVEL_ALIASES[normalized]
    except KeyError as error:
        msg = f"unsupported log level: {value}"
        raise ValueError(msg) from error


def _find_value(record: Mapping[str, Any], field: str) -> object:
    normalized = {str(key).strip().lower(): value for key, value in record.items()}
    for alias in FIELD_ALIASES[field]:
        if alias in normalized:
            return normalized[alias]
    return None


def mapping_to_entry(record: Mapping[str, Any], line_number: int) -> LogEntry:
    """Convert a JSON/CSV mapping with common aliases to a canonical entry."""
    raw_message = _find_value(record, "message")
    if raw_message is None:
        msg = "missing message field"
        raise ValueError(msg)
    if isinstance(raw_message, (dict, list)):
        message = json.dumps(raw_message, ensure_ascii=False, sort_keys=True)
    else:
        message = str(raw_message)
    if not message.strip():
        msg = "message field is empty"
        raise ValueError(msg)

    raw_service = _find_value(record, "service")
    return LogEntry(
        timestamp=parse_timestamp(_find_value(record, "timestamp")),
        level=parse_level(_find_value(record, "level")),
        service="unknown" if raw_service is None else str(raw_service),
        message=message,
        source_line=line_number,
    )
