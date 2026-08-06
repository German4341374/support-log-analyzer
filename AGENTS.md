# Repository guidance

- Keep source code, tests, documentation, fixtures, and commit messages in English.
- Preserve the parser, analyzer, masking, report, and CLI module boundaries.
- Keep processing deterministic and avoid global mutable state.
- Never place real personal data, credentials, tokens, or customer logs in fixtures or reports.
- Add regression tests for format detection, damaged input, grouping, masking, and export changes.
- Run Ruff formatting and linting, mypy, Pytest, package build, and CLI smoke tests before push.
- Document privacy or compatibility trade-offs when changing parsing and redaction behavior.
