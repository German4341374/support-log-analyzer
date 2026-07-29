"""Problem detection and similarity normalization."""

from __future__ import annotations

import re

from support_log_analyzer.masking import mask_sensitive_data

KEY_PROBLEM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("timeout", re.compile(r"\b(?:timeout|timed?\s+out)\b", re.IGNORECASE)),
    ("connection refused", re.compile(r"\bconnection\s+refused\b", re.IGNORECASE)),
    ("access denied", re.compile(r"\b(?:access|permission)\s+denied\b", re.IGNORECASE)),
    (
        "database error",
        re.compile(r"\b(?:database|db)\s+error\b|\bsql\s+exception\b", re.IGNORECASE),
    ),
    (
        "DNS failure",
        re.compile(
            r"\bDNS\s+failure\b|\bname\s+resolution\s+failed\b|"
            r"\btemporary\s+failure\s+in\s+name\s+resolution\b",
            re.IGNORECASE,
        ),
    ),
    (
        "authentication failed",
        re.compile(r"\bauth(?:entication)?\s+fail(?:ed|ure)\b", re.IGNORECASE),
    ),
    ("out of memory", re.compile(r"\bout\s+of\s+memory\b|\boom(?:killed)?\b", re.IGNORECASE)),
)

_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_IPV4 = re.compile(
    r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])"
)
_TIMESTAMP = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?\b",
    re.IGNORECASE,
)
_NAMED_ID = re.compile(
    r"\b(?:id|request|ticket|job|order|user)(?:[_ -]?id)?\s*[:=#/-]?\s*\d+\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b\d+\b")
_WHITESPACE = re.compile(r"\s+")


def detect_key_problems(message: str) -> list[str]:
    """Return stable names for known operational failure patterns."""
    return [name for name, pattern in KEY_PROBLEM_PATTERNS if pattern.search(message)]


def normalize_message(message: str) -> str:
    """Normalize volatile values so semantically similar failures group together."""
    normalized = _TIMESTAMP.sub("<timestamp>", message)
    normalized = _UUID.sub("<uuid>", normalized)
    normalized = _IPV4.sub("<ipv4>", normalized)
    normalized = _NAMED_ID.sub("id=<id>", normalized)
    normalized = _NUMBER.sub("<id>", normalized)
    normalized = mask_sensitive_data(normalized)
    return _WHITESPACE.sub(" ", normalized).strip().casefold()
