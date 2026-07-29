from datetime import UTC, datetime
from pathlib import Path

import pytest

from support_log_analyzer.demo import generate_demo, infer_demo_format
from support_log_analyzer.exceptions import UnsupportedFormatError
from support_log_analyzer.models import InputFormat
from support_log_analyzer.parsers import parse_file


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("demo.log", InputFormat.TEXT),
        ("demo.jsonl", InputFormat.JSONL),
        ("demo.csv", InputFormat.CSV),
    ],
)
def test_generates_parseable_demo_formats(tmp_path: Path, name: str, expected: InputFormat) -> None:
    output = tmp_path / name
    generated = generate_demo(
        output,
        lines=25,
        seed=7,
        start=datetime(2026, 7, 29, tzinfo=UTC),
    )

    parsed = parse_file(output)
    assert generated is expected
    assert parsed.input_format is expected
    assert len(parsed.entries) == 25


def test_demo_generation_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    start = datetime(2026, 7, 29, tzinfo=UTC)

    generate_demo(first, lines=10, seed=99, start=start)
    generate_demo(second, lines=10, seed=99, start=start)

    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_rejects_zero_demo_lines(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        generate_demo(tmp_path / "demo.log", lines=0)


def test_rejects_unknown_demo_extension(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedFormatError, match="extension"):
        infer_demo_format(tmp_path / "demo.yaml")
