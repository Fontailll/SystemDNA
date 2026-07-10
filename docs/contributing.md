# Contributing (Extended)

## Coding Standards

- **Type annotations**: All function signatures must have type annotations. Use `from __future__ import annotations` at the top of every file.
- **Line length**: 88 characters, enforced by Ruff formatter.
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups. Use Ruff's I rule to auto-sort.
- **Naming**: `snake_case` for functions, methods, variables; `PascalCase` for classes; `UPPER_CASE` for constants.
- **Error handling**: Raise `SystemDNAError` subclasses (`SnapshotError`, `CollectorError`, etc.) for domain errors. Always include the original exception via the `original` parameter when wrapping.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=systemdna --cov-report=term-missing

# Run a specific test file
pytest tests/test_snapshot.py
```

## Linting and Type Checking

```bash
# Lint
ruff check src/ tests/

# Format
ruff format --check src/ tests/

# Type check
mypy src/
```

Run all three before submitting a pull request. CI will enforce them.

## Pull Request Checklist

- [ ] Tests pass (`pytest` returns 0)
- [ ] Ruff linting passes (`ruff check .`)
- [ ] Ruff formatting passes (`ruff format --check .`)
- [ ] mypy passes (`mypy src/`)
- [ ] Changes are scoped to a single logical concern
- [ ] Commit messages follow conventional commits format
- [ ] New features include tests
- [ ] Documentation is updated if behaviour changed

## Commit Message Format

```
<type>: <short summary>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.

## Project Structure

```
src/systemdna/
├── app.py                 # typer CLI entry point
├── cli/                   # command implementations using typer
├── collectors/            # collector ABC, registry, runner, built-in collectors
├── core/                  # base classes, config, exceptions, logging
├── diff/                  # snapshot comparison engine
├── doctor/                # analysis rules and engine
├── export/                # JSON, Markdown, HTML exporters
├── history/               # snapshot history engine
├── models/                # Pydantic data models
├── platform/              # OS-specific implementations
│   └── linux/             # Linux collector implementations
├── plugins/               # plugin discovery, loading, management
├── schemas/               # snapshot schema validation
├── snapshot/              # snapshot creation and persistence
├── storage/               # filesystem storage layer
└── utils/                 # hashing, system, time helpers
```
