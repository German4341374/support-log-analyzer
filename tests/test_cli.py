from pathlib import Path

from typer.testing import CliRunner

from support_log_analyzer.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "support-log-analyzer 0.1.0" in result.stdout


def test_generate_demo_command(tmp_path: Path) -> None:
    output = tmp_path / "demo.log"

    result = runner.invoke(app, ["generate-demo", str(output), "--lines", "20", "--seed", "3"])

    assert result.exit_code == 0
    assert output.exists()
    assert len(output.read_text(encoding="utf-8").splitlines()) == 20


def test_analyze_command_prints_summary(txt_log: Path) -> None:
    result = runner.invoke(app, ["analyze", str(txt_log), "--level", "ERROR"])

    assert result.exit_code == 0
    assert "Log analysis" in result.stdout
    assert "Most frequent errors" in result.stdout


def test_analyze_command_exports_html(txt_log: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.html"

    result = runner.invoke(
        app,
        ["analyze", str(txt_log), "--service", "api", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "Report written to" in result.stdout


def test_analyze_missing_file_returns_controlled_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["analyze", str(tmp_path / "missing.log")])

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_analyze_rejects_invalid_time(txt_log: Path) -> None:
    result = runner.invoke(app, ["analyze", str(txt_log), "--from", "tomorrowish"])

    assert result.exit_code == 2
    assert "ISO-8601" in result.stderr
