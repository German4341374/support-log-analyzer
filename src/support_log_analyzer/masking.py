"""Sensitive-data masking with deterministic placeholders."""

from __future__ import annotations

import re

_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_API_KEY_ASSIGNMENT = re.compile(
    r"""(?ix)
    \b(?P<label>api[_ -]?key|apikey|x-api-key)\b
    (?P<separator>\s*[:=]\s*)
    ["']?(?P<secret>[A-Za-z0-9._-]{8,})["']?
    """
)
_API_KEY_PREFIX = re.compile(r"\b(?:sk|pk)_(?:test|live)_[A-Za-z0-9]{8,}\b", re.IGNORECASE)
_EMAIL = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IPV4 = re.compile(
    r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])"
)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{7,}\d)(?!\w)")


def mask_sensitive_data(text: str) -> str:
    """Replace supported sensitive values while keeping diagnostic context."""
    masked = _BEARER.sub("Bearer <BEARER_TOKEN>", text)
    masked = _API_KEY_ASSIGNMENT.sub(
        lambda match: f"{match.group('label')}{match.group('separator')}<API_KEY>",
        masked,
    )
    masked = _API_KEY_PREFIX.sub("<API_KEY>", masked)
    masked = _EMAIL.sub("<EMAIL>", masked)
    masked = _IPV4.sub("<IPV4>", masked)
    return _PHONE.sub("<PHONE>", masked)
