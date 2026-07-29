"""Deterministic, privacy-safe demonstration log generation."""

from __future__ import annotations

import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from support_log_analyzer.exceptions import UnsupportedFormatError
from support_log_analyzer.models import InputFormat

_SERVICES = ("api", "worker", "database", "gateway", "auth")
_MESSAGES_BY_LEVEL: dict[str, tuple[str, ...]] = {
    "DEBUG": ("Cache lookup completed in 12 ms", "Worker heartbeat accepted"),
    "INFO": ("Request completed successfully", "Scheduled health check passed"),
    "WARNING": ("Retrying downstream request after timeout", "Queue depth is above warning limit"),
    "ERROR": (
        "Connection refused by upstream 192.0.2.10 for request 10042",
        "Database error while loading ticket 10043",
        "Authentication failed for engineer@example.test",
        "DNS failure while resolving api.internal.test",
        "Access denied for job ID 10044",
    ),
    "CRITICAL": (
        "Out of memory while processing job 10045",
        "Gateway timeout; Authorization: Bearer demo-token-value-0001",
        "API key=demo_api_key_0001 rejected",
    ),
}
_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_LEVEL_WEIGHTS = (8, 50, 17, 20, 5)


def infer_demo_format(path: Path) -> InputFormat:
    """Infer demo format from a familiar file extension."""
    suffix = path.suffix.lower()
    if suffix in {".log", ".txt"}:
        return InputFormat.TEXT
    if suffix in {".jsonl", ".ndjson"}:
        return InputFormat.JSONL
    if suffix == ".csv":
        return InputFormat.CSV
    msg = "demo file extension must be .log, .txt, .jsonl, .ndjson, or .csv"
    raise UnsupportedFormatError(msg)


def generate_demo(
    output: Path,
    *,
    lines: int,
    seed: int = 42,
    start: datetime | None = None,
) -> InputFormat:
    """Generate safe sample events without real credentials or personal data."""
    if lines < 1:
        msg = "lines must be at least 1"
        raise ValueError(msg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output_format = infer_demo_format(output)
    rng = random.Random(seed)
    current = start or datetime.now(tz=UTC).replace(microsecond=0)
    records: list[dict[str, str]] = []
    for _ in range(lines):
        current += timedelta(seconds=rng.randint(2, 90))
        level = rng.choices(_LEVELS, weights=_LEVEL_WEIGHTS, k=1)[0]
        records.append(
            {
                "timestamp": current.isoformat().replace("+00:00", "Z"),
                "level": level,
                "service": rng.choice(_SERVICES),
                "message": rng.choice(_MESSAGES_BY_LEVEL[level]),
            }
        )

    if output_format is InputFormat.JSONL:
        content = "\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n"
        output.write_text(content, encoding="utf-8")
    elif output_format is InputFormat.CSV:
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["timestamp", "level", "service", "message"])
            writer.writeheader()
            writer.writerows(records)
    else:
        content = "\n".join(
            f"{record['timestamp']} {record['level']} [{record['service']}] {record['message']}"
            for record in records
        )
        output.write_text(content + "\n", encoding="utf-8")
    return output_format
