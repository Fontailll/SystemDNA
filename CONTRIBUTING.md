# Contributing to SystemDNA

Thank you for your interest in contributing. This document covers the practical steps for setting up a development environment, running tests, and submitting changes.

## Code of Conduct

This project is governed by the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). By participating you agree to uphold its terms.

## Setting Up a Development Environment

```bash
git clone https://github.com/Fontailll/SystemDNA.git
cd systemdna
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the package in editable mode along with test and lint dependencies.

## Running Tests

```bash
pytest          # run all tests with verbose output
pytest -x       # stop on first failure
pytest --cov    # run with coverage report
```

Tests live in the `tests/` directory and use pytest.

## Code Style

- **Ruff** for linting and formatting: `ruff check . && ruff format --check .`
- **mypy** for static type checking: `mypy src/`
- Line length: 88 characters
- Target Python version: 3.13

Configuration for both tools is in `pyproject.toml`.

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Make your changes, keeping commits small and focused.
3. Run `ruff check . && ruff format --check . && mypy src/ && pytest` and fix any issues.
4. Open a pull request with a clear title and description of the change.
5. Keep the PR scoped to a single concern. Multiple unrelated changes belong in separate PRs.

## Commit Message Conventions

Follow conventional commits:

```
feat: add network interface speed collector
fix: handle missing /etc/os-release gracefully
docs: document snapshot schema versioning
chore: bump dependencies
refactor: extract diff comparison logic
test: add tests for package collector
```

## Project Structure

```
src/
  systemdna/
    app.py                  # CLI entry point (typer)
    cli/                    # typer command definitions
    collectors/             # system information collectors
      base.py               # Collector ABC
      registry.py           # CollectorRegistry
      runner.py             # concurrent execution
      *_collector.py        # individual collectors
    core/                   # configuration, exceptions, logging
    diff/                   # snapshot comparison engine
    doctor/                 # analysis rules and engine
    export/                 # JSON, Markdown, HTML export
    history/                # snapshot history management
    models/                 # Pydantic data models
    platform/
      linux/                # Linux-specific collector implementations
    plugins/                # plugin discovery and loading
    schemas/                # snapshot schema validation
    snapshot/               # snapshot creation and persistence
    storage/                # filesystem storage management
    utils/                  # hashing, system, time utilities
tests/                      # pytest test suite
```
## Design Principles

SystemDNA follows a few core principles:

- Linux-first
- Distribution-agnostic
- Init-system agnostic
- Offline by default
- No telemetry
- No background daemons
- Graceful degradation when subsystems are unavailable
- Read standard Linux interfaces whenever possible (/proc, /sys, /etc, /run)

Contributors should preserve these principles when proposing new features.
