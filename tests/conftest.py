from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def txt_log(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.log"


@pytest.fixture
def jsonl_log(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.jsonl"


@pytest.fixture
def csv_log(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.csv"
