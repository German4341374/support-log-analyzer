"""Rich terminal report rendering."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from support_log_analyzer.models import AnalysisReport


def _format_timestamp(value: object) -> str:
    return "n/a" if value is None else str(value)


def render_console_report(report: AnalysisReport, console: Console) -> None:
    """Render a compact report suitable for support triage."""
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold cyan")
    summary.add_column()
    summary.add_row("Messages", str(report.message_count))
    summary.add_row("Errors", str(report.error_count))
    summary.add_row("Skipped lines", str(report.skipped_lines))
    summary.add_row("First timestamp", _format_timestamp(report.first_timestamp))
    summary.add_row("Last timestamp", _format_timestamp(report.last_timestamp))
    console.print(Panel(summary, title=f"Log analysis · {report.input_file.name}", expand=False))

    errors = Table(title="Most frequent errors")
    errors.add_column("Count", justify="right", style="bold red")
    errors.add_column("Services")
    errors.add_column("Example", overflow="fold")
    for group in report.top_errors:
        errors.add_row(str(group.count), ", ".join(group.services), group.example)
    if report.top_errors:
        console.print(errors)

    services = Table(title="Errors by service")
    services.add_column("Service")
    services.add_column("Errors", justify="right")
    for service, count in report.services_by_error.items():
        services.add_row(service, str(count))
    if report.services_by_error:
        console.print(services)

    issues = Table(title="Detected key problems")
    issues.add_column("Problem")
    issues.add_column("Occurrences", justify="right")
    for name, count in report.detected_issues.items():
        issues.add_row(name, str(count))
    if report.detected_issues:
        console.print(issues)
