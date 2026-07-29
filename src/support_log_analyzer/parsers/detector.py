"""Content-aware input format detection and parser dispatch."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from support_log_analyzer.exceptions import InputFileError
from support_log_analyzer.models import InputFormat, ParseResult
from support_log_analyzer.parsers.common import FIELD_ALIASES
from support_log_analyzer.parsers.csv_log import parse_csv
from support_log_analyzer.parsers.jsonl import parse_jsonl
from support_log_analyzer.parsers.text import parse_text


def _read_sample(path: Path) -> str:
    if not path.exists():
        msg = f"input file does not exist: {path}"
        raise InputFileError(msg)
    if not path.is_file():
        msg = f"input path is not a file: {path}"
        raise InputFileError(msg)
    try:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:16_384]
    except OSError as error:
        msg = f"cannot read input file: {path}"
        raise InputFileError(msg) from error
    if not sample.strip():
        msg = f"input file is empty: {path}"
        raise InputFileError(msg)
    return sample


def _looks_like_csv(sample: str) -> bool:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        reader = csv.reader(io.StringIO(sample), dialect)
        header = next(reader)
    except (csv.Error, StopIteration):
        return False
    names = {column.strip().lower() for column in header}
    message_aliases = set(FIELD_ALIASES["message"])
    return bool(names & message_aliases) and len(header) >= 2


def detect_format(path: Path) -> InputFormat:
    """Detect JSON Lines, CSV, or plain text from content with extension hints."""
    sample = _read_sample(path)
    first_line = next(line for line in sample.splitlines() if line.strip())
    try:
        value = json.loads(first_line)
        if isinstance(value, dict):
            return InputFormat.JSONL
    except json.JSONDecodeError:
        pass
    if _looks_like_csv(sample):
        return InputFormat.CSV
    return InputFormat.TEXT


def parse_file(path: Path) -> ParseResult:
    """Detect and parse a log file."""
    detected = detect_format(path)
    if detected is InputFormat.JSONL:
        return parse_jsonl(path)
    if detected is InputFormat.CSV:
        return parse_csv(path)
    return parse_text(path)
