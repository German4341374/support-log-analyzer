"""Report rendering and export facade."""

from support_log_analyzer.reports.console import render_console_report
from support_log_analyzer.reports.export import write_report

__all__ = ["render_console_report", "write_report"]
