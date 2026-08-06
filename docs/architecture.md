# Architecture

Support Log Analyzer is a local-first command-line pipeline. Parsers stream supported records into
typed models, analyzers aggregate operational signals, the masking layer removes configured
sensitive patterns, and report writers serialize the resulting summary.

The CLI owns orchestration and error-to-exit-code mapping. Domain modules do not depend on terminal
rendering, which keeps analysis reusable and testable. Input data is never uploaded, and exporters
receive masked records only.

## Boundaries

- **Parsers** detect TXT, JSON Lines, and CSV input and isolate damaged rows.
- **Analyzers** normalize recurring messages and compute error, service, and time-window statistics.
- **Masking** redacts email addresses, IPv4 addresses, tokens, API keys, and phone numbers.
- **Reports** produce console, JSON, CSV, Markdown, and HTML output.
- **CLI** validates arguments, connects the modules, and returns stable exit codes.

The application favors bounded memory use, but report detail and similarity-group cardinality still
grow with diverse input. The README documents these limitations and safe handling practices.
