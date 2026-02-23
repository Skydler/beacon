# Beacon — Agent Guidelines

## Project Overview

Beacon is an AI-powered local news aggregator. It scrapes configured news sites, filters
articles through an LLM (GitHub Models API / GPT-4o-mini), stores results in SQLite, sends
relevant articles to Discord, and exposes a read-only web dashboard (FastAPI + Jinja2).

---

## Build & Dependency Management

The project uses [uv](https://github.com/astral-sh/uv) exclusively. Do not use `pip` directly.

```bash
# Install all dependencies (including dev extras)
uv sync --all-extras

# Add a new runtime dependency
uv add <package>

# Add a new dev-only dependency
uv add --dev <package>
```

---

## Running the Application

```bash
# Full pipeline run
uv run python src/main.py

# Useful flags
uv run python src/main.py --dry-run      # skip Discord notifications
uv run python src/main.py --test-scraper
uv run python src/main.py --test-llm
uv run python src/main.py --test-discord
uv run python src/main.py --verbose

# Web dashboard (development)
uv run uvicorn src.web:app --host 0.0.0.0 --port 3012 --reload
```

---

## Testing

```bash
# Run full test suite
uv run pytest

# Run a single test file
uv run pytest tests/test_database.py

# Run a single test by name
uv run pytest tests/test_database.py::test_mark_article_seen

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run only web or database tests
uv run pytest tests/test_web.py tests/test_database.py
```

Tests use `pytest`. The `tests/` directory mirrors `src/` with one file per module.
All tests are self-contained — the database tests use an in-memory SQLite instance (`:memory:`),
and the web tests patch `src.web._cfg` and `src.web._db` directly.

---

## Lint & Format

```bash
# Format all code (must pass before committing)
uv run ruff format .

# Lint (active rules: E, F, I, N, W)
uv run ruff check .

# Lint and auto-fix where possible
uv run ruff check . --fix
```

Active ruff rule sets: **E** (pycodestyle errors), **F** (pyflakes), **I** (isort),
**N** (pep8-naming), **W** (pycodestyle warnings). Rules outside these sets are not enforced.

---

## Code Style

### General

- **Line length:** 100 characters maximum.
- **Indentation:** 4 spaces. No tabs.
- **Quotes:** Double quotes for strings (`"like this"`).
- **Trailing commas:** Not required but allowed in multi-line structures.
- **Python version:** 3.14+. Use modern syntax freely (e.g. `match`, `X | Y` unions).

### Imports

Follow isort ordering (enforced by ruff `I`):

1. Standard library
2. Third-party packages
3. Local `src.*` imports

Each group separated by a blank line. No wildcard imports (`from x import *`).
Imports at the top of the file; avoid imports inside functions unless there is a clear
reason (e.g. avoiding a circular dependency).

```python
# Good
import logging
from typing import Optional

import yaml
from sqlalchemy.orm import Session

from src.config import Config
from src.database import Database
```

### Type Annotations

- Annotate all function parameters and return types.
- Use `Optional[X]` for nullable parameters (or `X | None` — both are acceptable given 3.14).
- Use `List`, `Dict` from `typing` for compatibility with the existing codebase, or the
  built-in `list[...]` / `dict[...]` — be consistent within a file.
- `any` as a type hint (lowercase) is incorrect; use `Any` from `typing`.

### Naming

- **Modules/packages:** `snake_case` (e.g. `llm_filter.py`)
- **Classes:** `PascalCase` (e.g. `BeaconApp`, `Database`)
- **Functions/methods/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private helpers:** prefix with `_` (e.g. `_get_session`, `_migrate`)
- Test functions: `test_<what_it_tests>` (e.g. `test_mark_article_seen`)

### Docstrings

Every public class and method must have a docstring. Use the Google style:

```python
def mark_article_seen(self, url: str, title: str, relevance_score: Optional[int] = None) -> None:
    """Mark an article as seen and store in database.

    Args:
        url: Article URL.
        title: Article title.
        relevance_score: Optional relevance score from LLM (1-10).
    """
```

One-liner docstrings are acceptable for trivial methods.

### Error Handling

- Catch specific exceptions, not bare `except Exception` unless you are at a top-level
  boundary (e.g. the main pipeline loop where a source failure must not abort other sources).
- Always log errors before re-raising or swallowing:
  ```python
  except Exception as e:
      logger.error(f"Failed to mark article as seen: {e}")
      raise
  ```
- For database operations: rollback the session in the `except` block, close it in `finally`.
- Never silently swallow exceptions unless the intent is explicitly documented in a comment.

### Logging

- Use the module-level logger: `logger = logging.getLogger(__name__)`
- `logger.info` for normal pipeline events.
- `logger.debug` for per-article detail (visible only with `--verbose`).
- `logger.warning` for recoverable issues (e.g. missing config values with defaults).
- `logger.error` for failures. Include the exception: `logger.error(f"...: {e}")`.
- Do not use `print()` in `src/` — only in standalone scripts under `scripts/`.

---

## Architecture Notes

- **`src/config.py`** — YAML + env-var loader. All configuration access goes through `Config`.
- **`src/database.py`** — SQLAlchemy ORM over SQLite. The `Database` class is the only
  layer that touches the DB. Web and pipeline both instantiate it independently.
- **`src/main.py`** — Pipeline orchestrator (`BeaconApp`). CLI entry point.
- **`src/web.py`** — FastAPI read-only dashboard. Instantiates `Config` and `Database` at
  module load time. No write operations.
- **`src/templates/index.html`** — Jinja2 template for the dashboard.
- **`scripts/`** — One-off operational scripts (e.g. DB migrations). Not imported by `src/`.

The pipeline and web service share the SQLite file via the `beacon-data` Docker volume.
The web service mounts it read-only. Do not add write operations to `src/web.py`.

---

## Database Migrations

There is no migration framework. Schema changes require:

1. Update the ORM model in `src/database.py`.
2. Write a standalone migration script in `scripts/` using plain `sqlite3`:
   ```bash
   uv run python scripts/migrate_add_columns.py
   ```
3. The script must be idempotent (safe to run twice) and check for existing columns via
   `PRAGMA table_info`.

Do **not** add auto-migration logic to `Database.__init__`.

---

## Docker

```bash
# Run the one-shot pipeline
docker compose run --rm beacon

# Start the web dashboard
docker compose up beacon-web

# Rebuild after dependency changes
docker compose build
```

The `beacon` service has no restart policy (cron-triggered). The `beacon-web` service uses
`restart: unless-stopped`.
