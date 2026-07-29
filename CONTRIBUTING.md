# Contributing

Use Python 3.12 or newer and create a virtual environment before installing the project.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type pre-push
```

Before opening a pull request, run:

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov
```

Use Conventional Commits such as `feat: add syslog parser` or
`fix(masking): handle quoted API keys`. Tests and fixtures must use synthetic data, reserved
domains, and documentation-only IP ranges.

