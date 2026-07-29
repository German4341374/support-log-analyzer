"""JSON, CSV, Markdown, and standalone HTML report exporters."""

from __future__ import annotations

import csv
import html
import json
from collections.abc import Iterable
from pathlib import Path

from support_log_analyzer.exceptions import ReportWriteError, UnsupportedFormatError
from support_log_analyzer.models import AnalysisReport


def _iso(value: object) -> str:
    return "" if value is None else str(value)


def _markdown(report: AnalysisReport) -> str:
    lines = [
        "# Support Log Analysis",
        "",
        f"- **Input:** `{report.input_file}`",
        f"- **Format:** {report.input_format.value}",
        f"- **Messages:** {report.message_count}",
        f"- **Errors:** {report.error_count}",
        f"- **Skipped lines:** {report.skipped_lines}",
        f"- **First timestamp:** {_iso(report.first_timestamp) or 'n/a'}",
        f"- **Last timestamp:** {_iso(report.last_timestamp) or 'n/a'}",
        "",
        "## Most Frequent Errors",
        "",
        "| Count | Services | Example |",
        "| ---: | --- | --- |",
    ]
    for group in report.top_errors:
        example = group.example.replace("|", "\\|")
        lines.append(f"| {group.count} | {', '.join(group.services)} | {example} |")
    lines.extend(["", "## Errors by Service", "", "| Service | Errors |", "| --- | ---: |"])
    lines.extend(f"| {name} | {count} |" for name, count in report.services_by_error.items())
    lines.extend(
        ["", "## Detected Key Problems", "", "| Problem | Occurrences |", "| --- | ---: |"]
    )
    lines.extend(f"| {name} | {count} |" for name, count in report.detected_issues.items())
    lines.extend(
        ["", "## Hourly Error Distribution", "", "| Hour (UTC) | Errors |", "| --- | ---: |"]
    )
    lines.extend(f"| {hour} | {count} |" for hour, count in report.hourly_errors.items())
    return "\n".join(lines) + "\n"


def _table_rows(values: dict[str, int]) -> str:
    return "".join(
        f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>" for name, count in values.items()
    )


def _html(report: AnalysisReport) -> str:
    error_rows = "".join(
        "<tr>"
        f"<td>{group.count}</td>"
        f"<td>{html.escape(', '.join(group.services))}</td>"
        f"<td>{html.escape(group.example)}</td>"
        "</tr>"
        for group in report.top_errors
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Support Log Analysis</title>
  <style>
    body {{ font: 16px system-ui, sans-serif; margin: 0; background: #f4f7fb; color: #172033; }}
    main {{ max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
    .metrics {{
      display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 14px;
    }}
    .card, section {{
      background: white; border: 1px solid #dfe5ee; border-radius: 12px; padding: 18px;
    }}
    .card strong {{ display: block; font-size: 2rem; color: #b42318; }}
    section {{ margin-top: 18px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #e6eaf0; padding: 10px; text-align: left; }}
    th {{ color: #475467; }} code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body><main>
  <h1>Support Log Analysis</h1>
  <p><code>{html.escape(str(report.input_file))}</code> · {report.input_format.value}</p>
  <div class="metrics">
    <div class="card"><strong>{report.message_count}</strong>Messages</div>
    <div class="card"><strong>{report.error_count}</strong>Errors</div>
    <div class="card"><strong>{report.skipped_lines}</strong>Skipped lines</div>
  </div>
  <section><h2>Most Frequent Errors</h2><table>
    <thead><tr><th>Count</th><th>Services</th><th>Example</th></tr></thead>
    <tbody>{error_rows}</tbody>
  </table></section>
  <section><h2>Errors by Service</h2>
    <table><tbody>{_table_rows(report.services_by_error)}</tbody></table>
  </section>
  <section><h2>Detected Key Problems</h2>
    <table><tbody>{_table_rows(report.detected_issues)}</tbody></table>
  </section>
  <section><h2>Hourly Error Distribution</h2>
    <table><tbody>{_table_rows(report.hourly_errors)}</tbody></table>
  </section>
</main></body></html>
"""


def _csv_rows(report: AnalysisReport) -> Iterable[list[str | int]]:
    yield ["summary", "messages", report.message_count, ""]
    yield ["summary", "errors", report.error_count, ""]
    yield ["summary", "skipped_lines", report.skipped_lines, ""]
    for group in report.top_errors:
        yield ["top_error", group.example, group.count, ", ".join(group.services)]
    for name, count in report.services_by_error.items():
        yield ["service", name, count, ""]
    for name, count in report.detected_issues.items():
        yield ["key_problem", name, count, ""]
    for name, count in report.hourly_errors.items():
        yield ["hour", name, count, ""]


def _write_csv(report: AnalysisReport, output: Path) -> None:
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["section", "name", "count", "details"])
        writer.writerows(_csv_rows(report))


def write_report(report: AnalysisReport, output: Path) -> None:
    """Select an exporter from the output extension and write atomically enough for a CLI."""
    suffix = output.suffix.lower()
    if suffix not in {".json", ".csv", ".md", ".markdown", ".html", ".htm"}:
        msg = "output extension must be .json, .csv, .md, or .html"
        raise UnsupportedFormatError(msg)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".json":
            payload = report.model_dump(mode="json")
            output.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        elif suffix == ".csv":
            _write_csv(report, output)
        elif suffix in {".md", ".markdown"}:
            output.write_text(_markdown(report), encoding="utf-8")
        else:
            output.write_text(_html(report), encoding="utf-8")
    except OSError as error:
        msg = f"cannot write report: {output}"
        raise ReportWriteError(msg) from error
