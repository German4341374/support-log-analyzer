"""Typer command-line interface."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console

from support_log_analyzer import __version__
from support_log_analyzer.analyzers import analyze_logs
from support_log_analyzer.demo import generate_demo
from support_log_analyzer.exceptions import LogAnalyzerError
from support_log_analyzer.models import AnalysisFilters, LogLevel
from support_log_analyzer.parsers import parse_file
from support_log_analyzer.parsers.common import parse_timestamp
from support_log_analyzer.reports import render_console_report, write_report

app = typer.Typer(
    name="support-log-analyzer",
    help="Analyze support logs, group recurring failures, and mask sensitive values.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()
error_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"support-log-analyzer {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """Analyze application logs for support and incident-response workflows."""


def _optional_timestamp(value: str | None, option_name: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = parse_timestamp(value)
    except (OverflowError, OSError, ValueError) as error:
        raise typer.BadParameter(
            "expected an ISO-8601 timestamp", param_hint=option_name
        ) from error
    if parsed is None:
        raise typer.BadParameter("timestamp cannot be empty", param_hint=option_name)
    return parsed


@app.command()
def analyze(
    input_file: Annotated[Path, typer.Argument(help="TXT, LOG, JSONL, or CSV input file.")],
    level: Annotated[
        list[LogLevel] | None,
        typer.Option("--level", "-l", help="Exact level to include. Repeat for multiple levels."),
    ] = None,
    service: Annotated[
        str | None, typer.Option("--service", "-s", help="Service name, case-insensitive.")
    ] = None,
    text: Annotated[
        str | None, typer.Option("--text", "-q", help="Case-insensitive message substring.")
    ] = None,
    start: Annotated[
        str | None, typer.Option("--from", help="Inclusive ISO-8601 start timestamp.")
    ] = None,
    end: Annotated[
        str | None, typer.Option("--to", help="Inclusive ISO-8601 end timestamp.")
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Export to .json, .csv, .md, or .html."),
    ] = None,
    top: Annotated[
        int, typer.Option(min=1, max=100, help="Maximum recurring errors to show.")
    ] = 10,
) -> None:
    """Analyze one log file and print a privacy-safe operational summary."""
    try:
        parsed = parse_file(input_file)
        filters = AnalysisFilters(
            levels=None if level is None else frozenset(level),
            service=service,
            text=text,
            start=_optional_timestamp(start, "--from"),
            end=_optional_timestamp(end, "--to"),
        )
        report = analyze_logs(input_file, parsed, filters, top=top)
        render_console_report(report, console)
        if output is not None:
            write_report(report, output)
            console.print(f"[green]Report written to[/green] {output}")
    except (LogAnalyzerError, ValidationError, ValueError) as error:
        error_console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=2) from error


@app.command("generate-demo")
def generate_demo_command(
    output: Annotated[Path, typer.Argument(help="Output .log, .txt, .jsonl, or .csv file.")],
    lines: Annotated[int, typer.Option(min=1, max=1_000_000, help="Number of events.")] = 1000,
    seed: Annotated[int, typer.Option(help="Deterministic random seed.")] = 42,
) -> None:
    """Generate safe demonstration logs with recurring operational problems."""
    try:
        output_format = generate_demo(output, lines=lines, seed=seed)
        console.print(f"[green]Generated[/green] {lines} {output_format.value} events in {output}")
    except (LogAnalyzerError, OSError, ValueError) as error:
        error_console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=2) from error
