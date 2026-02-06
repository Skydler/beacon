FROM python:3.14-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Copy application code
COPY src/ src/
COPY config/ config/
COPY preferences.md .

# Create data directory for SQLite
RUN mkdir -p data

ENTRYPOINT ["uv", "run", "--no-dev", "python", "src/main.py"]
