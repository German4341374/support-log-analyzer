"""Filtering, grouping, and operational metric calculation."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from support_log_analyzer.analyzers.patterns import detect_key_problems, normalize_message
from support_log_analyzer.masking import mask_sensitive_data
from support_log_analyzer.models import (
    AnalysisFilters,
    AnalysisReport,
    ErrorGroup,
    LogEntry,
    LogLevel,
    ParseResult,
)

_ERROR_LEVELS = frozenset({LogLevel.ERROR, LogLevel.CRITICAL})


def _matches(entry: LogEntry, filters: AnalysisFilters) -> bool:
    if filters.levels is not None and entry.level not in filters.levels:
        return False
    if filters.service is not None and entry.service.casefold() != filters.service.casefold():
        return False
    if filters.text is not None and filters.text.casefold() not in entry.message.casefold():
        return False
    if filters.start is not None and (entry.timestamp is None or entry.timestamp < filters.start):
        return False
    return not (
        filters.end is not None and (entry.timestamp is None or entry.timestamp > filters.end)
    )


def _group_errors(entries: list[LogEntry], limit: int) -> list[ErrorGroup]:
    grouped: dict[str, list[LogEntry]] = defaultdict(list)
    for entry in entries:
        if entry.level in _ERROR_LEVELS:
            grouped[normalize_message(entry.message)].append(entry)

    ranked = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:limit]
    return [
        ErrorGroup(
            normalized=normalized,
            example=mask_sensitive_data(group[0].message),
            count=len(group),
            services=sorted({entry.service for entry in group}, key=str.casefold),
            issue_types=sorted(
                {issue for entry in group for issue in detect_key_problems(entry.message)},
                key=str.casefold,
            ),
        )
        for normalized, group in ranked
    ]


def analyze_logs(
    input_file: Path,
    parsed: ParseResult,
    filters: AnalysisFilters | None = None,
    *,
    top: int = 10,
) -> AnalysisReport:
    """Apply filters and calculate privacy-safe support metrics."""
    active_filters = filters or AnalysisFilters()
    entries = [entry for entry in parsed.entries if _matches(entry, active_filters)]
    error_entries = [entry for entry in entries if entry.level in _ERROR_LEVELS]

    issue_counter: Counter[str] = Counter()
    service_counter: Counter[str] = Counter()
    hourly_counter: Counter[str] = Counter()
    for entry in entries:
        issue_counter.update(detect_key_problems(entry.message))
    for entry in error_entries:
        service_counter[entry.service] += 1
        if entry.timestamp is not None:
            bucket = entry.timestamp.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
            hourly_counter[bucket.isoformat().replace("+00:00", "Z")] += 1

    timestamps = sorted(entry.timestamp for entry in entries if entry.timestamp is not None)
    return AnalysisReport(
        input_file=input_file,
        input_format=parsed.input_format,
        generated_at=datetime.now(tz=UTC),
        total_lines=parsed.total_lines,
        skipped_lines=parsed.skipped_lines,
        message_count=len(entries),
        error_count=len(error_entries),
        detected_issues=dict(issue_counter.most_common()),
        top_errors=_group_errors(entries, max(top, 1)),
        services_by_error=dict(service_counter.most_common()),
        first_timestamp=timestamps[0] if timestamps else None,
        last_timestamp=timestamps[-1] if timestamps else None,
        hourly_errors=dict(sorted(hourly_counter.items())),
    )
