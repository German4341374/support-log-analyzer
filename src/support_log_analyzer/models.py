"""Typed domain models shared across the application."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class LogLevel(StrEnum):
    """Supported log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class InputFormat(StrEnum):
    """Supported input encodings."""

    TEXT = "text"
    JSONL = "jsonl"
    CSV = "csv"


class LogEntry(BaseModel):
    """Canonical representation of one parsed log event."""

    timestamp: datetime | None = None
    level: LogLevel = LogLevel.INFO
    service: str = "unknown"
    message: str = Field(min_length=1)
    source_line: int = Field(ge=1)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_validator("service")
    @classmethod
    def normalize_service(cls, value: str) -> str:
        cleaned = value.strip()
        return cleaned if cleaned else "unknown"

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return value.strip()


class ParseIssue(BaseModel):
    """A malformed line that was skipped without aborting analysis."""

    line_number: int = Field(ge=1)
    reason: str


class ParseResult(BaseModel):
    """Entries and diagnostics produced by a parser."""

    input_format: InputFormat
    total_lines: int = Field(ge=0)
    entries: list[LogEntry]
    issues: list[ParseIssue] = Field(default_factory=list)

    @property
    def skipped_lines(self) -> int:
        return len(self.issues)


class AnalysisFilters(BaseModel):
    """Optional constraints applied before metrics are computed."""

    levels: frozenset[LogLevel] | None = None
    service: str | None = None
    text: str | None = None
    start: datetime | None = None
    end: datetime | None = None

    @field_validator("start", "end")
    @classmethod
    def normalize_range_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_range(self) -> AnalysisFilters:
        if self.start is not None and self.end is not None and self.start > self.end:
            msg = "start timestamp must not be later than end timestamp"
            raise ValueError(msg)
        return self


class ErrorGroup(BaseModel):
    """A normalized family of similar error messages."""

    normalized: str
    example: str
    count: int = Field(ge=1)
    services: list[str]
    issue_types: list[str]


class AnalysisReport(BaseModel):
    """Serializable metrics returned by the analyzer."""

    input_file: Path
    input_format: InputFormat
    generated_at: datetime
    total_lines: int = Field(ge=0)
    skipped_lines: int = Field(ge=0)
    message_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    detected_issues: dict[str, int]
    top_errors: list[ErrorGroup]
    services_by_error: dict[str, int]
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    hourly_errors: dict[str, int]
