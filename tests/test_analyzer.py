from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from support_log_analyzer.analyzers.patterns import detect_key_problems, normalize_message
from support_log_analyzer.analyzers.summary import analyze_logs
from support_log_analyzer.models import (
    AnalysisFilters,
    InputFormat,
    LogEntry,
    LogLevel,
    ParseResult,
)


def entry(
    message: str,
    *,
    level: LogLevel = LogLevel.ERROR,
    service: str = "api",
    hour: int = 9,
) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2026, 7, 29, hour, 15, tzinfo=UTC),
        level=level,
        service=service,
        message=message,
        source_line=1,
    )


def parsed(*entries: LogEntry) -> ParseResult:
    return ParseResult(
        input_format=InputFormat.TEXT,
        total_lines=len(entries),
        entries=list(entries),
    )


@pytest.mark.parametrize(
    ("message", "problem"),
    [
        ("upstream timeout", "timeout"),
        ("connection refused by worker", "connection refused"),
        ("permission denied", "access denied"),
        ("database error occurred", "database error"),
        ("DNS failure", "DNS failure"),
        ("authentication failed", "authentication failed"),
        ("process ran out of memory", "out of memory"),
    ],
)
def test_detects_key_problem_patterns(message: str, problem: str) -> None:
    assert problem in detect_key_problems(message)


def test_groups_messages_while_ignoring_volatile_values() -> None:
    first = "Connection refused from 192.0.2.1 request 1001"
    second = "Connection refused from 198.51.100.2 request 9009"

    assert normalize_message(first) == normalize_message(second)


def test_groups_messages_while_ignoring_uuid() -> None:
    first = "Failed job 123e4567-e89b-12d3-a456-426614174000"
    second = "Failed job 123e4567-e89b-12d3-a456-426614174999"

    assert normalize_message(first) == normalize_message(second)


def test_calculates_counts_and_recurring_errors() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(
            entry("Database error for ticket 10"),
            entry("Database error for ticket 20"),
            entry("Request complete", level=LogLevel.INFO),
        ),
    )

    assert result.message_count == 3
    assert result.error_count == 2
    assert result.top_errors[0].count == 2
    assert result.detected_issues == {"database error": 2}


def test_counts_errors_by_service() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(
            entry("timeout", service="api"),
            entry("out of memory", level=LogLevel.CRITICAL, service="worker"),
            entry("connection refused", service="api"),
        ),
    )

    assert result.services_by_error == {"api": 2, "worker": 1}


def test_builds_hourly_error_distribution() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(
            entry("timeout", hour=9), entry("access denied", hour=9), entry("DNS failure", hour=10)
        ),
    )

    assert result.hourly_errors["2026-07-29T09:00:00Z"] == 2
    assert result.hourly_errors["2026-07-29T10:00:00Z"] == 1


def test_reports_first_and_last_timestamp() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(entry("first", hour=8), entry("last", hour=17)),
    )

    assert result.first_timestamp == datetime(2026, 7, 29, 8, 15, tzinfo=UTC)
    assert result.last_timestamp == datetime(2026, 7, 29, 17, 15, tzinfo=UTC)


def test_filters_by_exact_levels() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(
            entry("debug", level=LogLevel.DEBUG),
            entry("error", level=LogLevel.ERROR),
        ),
        AnalysisFilters(levels=frozenset({LogLevel.DEBUG})),
    )

    assert result.message_count == 1
    assert result.error_count == 0


def test_filters_by_service_case_insensitively() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(entry("one", service="API"), entry("two", service="worker")),
        AnalysisFilters(service="api"),
    )

    assert result.message_count == 1


def test_filters_by_message_text() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(entry("Database connection timeout"), entry("Authentication failed")),
        AnalysisFilters(text="CONNECTION"),
    )

    assert result.message_count == 1


def test_filters_by_inclusive_time_range() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(entry("early", hour=8), entry("included", hour=10), entry("late", hour=18)),
        AnalysisFilters(
            start=datetime(2026, 7, 29, 9, tzinfo=UTC),
            end=datetime(2026, 7, 29, 12, tzinfo=UTC),
        ),
    )

    assert result.message_count == 1


def test_rejects_reversed_time_range() -> None:
    with pytest.raises(ValidationError, match="start timestamp"):
        AnalysisFilters(
            start=datetime(2026, 7, 30, tzinfo=UTC),
            end=datetime(2026, 7, 29, tzinfo=UTC),
        )


def test_masks_error_examples() -> None:
    result = analyze_logs(
        Path("app.log"),
        parsed(entry("Authentication failed for engineer@example.test from 192.0.2.5")),
    )

    assert "<EMAIL>" in result.top_errors[0].example
    assert "<IPV4>" in result.top_errors[0].example
    assert "engineer@" not in result.top_errors[0].example
