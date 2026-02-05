# Technical Requirements

## System Requirements

### Hardware
- **Platform**: Raspberry Pi 5 (ARM64) or compatible Linux system
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 15GB free space (for Docker images, Ollama model, and database)
- **Network**: Stable internet connection for scraping and Discord

### Operating System
- Raspberry Pi OS (Debian-based) or Ubuntu 22.04+ ARM64
- **Docker**: Version 20.10+ with docker-compose v2

## Software Dependencies

### Core Dependencies

#### Docker and Docker Compose
Install Docker on Raspberry Pi:
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install docker-compose (if not included)
sudo apt update
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### uv (Python Package Manager)
Install uv for local development (optional, not needed for Docker deployment):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Project Dependencies (pyproject.toml)

Create `pyproject.toml` in project root:
```toml
[project]
name = "beacon"
version = "0.1.0"
description = "AI-powered news aggregator for personalized local news"
requires-python = ">=3.14"
dependencies = [
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "ollama>=0.1.0",
    "pyyaml>=6.0",
    "sqlalchemy>=2.0.0",
    "discord-webhook>=1.3.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
]

[tool.ruff]
line-length = 100
target-version = "py314"
select = ["E", "F", "I", "N", "W"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

Local development installation (optional):
```bash
# Create virtual environment and install dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras
```

## Python Library Purposes

- **requests**: HTTP requests for web scraping and API calls
- **beautifulsoup4 + lxml**: HTML parsing for news article extraction
- **ollama**: Python client for Ollama API
- **pyyaml**: Configuration file parsing
- **sqlalchemy**: Database ORM for article tracking
- **discord-webhook**: Discord webhook integration
- **python-dotenv**: Environment variable management

## Development Tools

- **uv**: Fast Python package installer and resolver, manages virtual environments and Python versions
- **ruff**: Fast Python linter and formatter (replaces flake8, black, isort, and more)
- **pytest**: Testing framework with excellent plugin ecosystem
- **Docker**: Container runtime for isolated, reproducible deployments
- **docker-compose**: Multi-container orchestration

## Docker Configuration

### Dockerfile
Create `Dockerfile` in project root:
```dockerfile
FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
COPY preferences.md ./

# Install dependencies
RUN uv sync --no-dev

# Create data directory
RUN mkdir -p /app/data

# Run the application (logs to stdout)
CMD ["uv", "run", "python", "src/main.py"]
```

### docker-compose.yml
Create `docker-compose.yml` in project root:
```yaml
version: '3.8'

services:
  beacon:
    build: .
    container_name: beacon-aggregator
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
    volumes:
      - ./data:/app/data
      - ./config/config.yaml:/app/config/config.yaml:ro
      - ./preferences.md:/app/preferences.md:ro
    restart: "no"  # Use systemd timer for scheduling
    # Use host network to access Ollama on host
    network_mode: host
    # Alternative: use extra_hosts if not using host network
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"
```

**Note**: Ollama is assumed to be running on the host system or accessible via network. The container uses `host.docker.internal` to connect to services on the host, or you can set a custom `OLLAMA_BASE_URL` environment variable.

## External Services

### Discord Webhook
1. In your Discord server, go to Server Settings → Integrations → Webhooks
2. Create a new webhook for your news channel
3. Copy the webhook URL (format: `https://discord.com/api/webhooks/ID/TOKEN`)

## Configuration Structure

### config.yaml
```yaml
news_sources:
  - name: "Local News Site"
    url: "https://example-local-news.com"
    selectors:
      article_list: "article.news-item"
      title: "h2.title"
      link: "a.read-more"
      description: "p.excerpt"

ollama:
  # Ollama is assumed to be running externally (host system or remote server)
  base_url: "http://localhost:11434"  # Localhost when using host network in Docker
  # base_url: "http://host.docker.internal:11434"  # Alternative for bridge network
  # base_url: "${OLLAMA_BASE_URL}"  # Load from environment variable
  model: "llama3.2:1b"
  timeout: 60

discord:
  webhook_url: "${DISCORD_WEBHOOK_URL}"  # Load from environment

database:
  path: "./data/seen_articles.db"

scraping:
  check_interval: 7200  # seconds (2 hours)
  max_articles_per_run: 20
  user_agent: "Mozilla/5.0 (compatible; BeaconBot/1.0)"

filtering:
  preferences_file: "./preferences.md"
  min_relevance_score: 7  # 1-10 scale

logging:
  level: "INFO"
  # Logs are sent to stdout (captured by Docker/systemd)
```

### Environment Variables (.env)
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
OLLAMA_BASE_URL=http://localhost:11434  # Optional: Override Ollama URL
```

## Scheduling

### Option 1: Systemd Timer with Docker (Recommended)

Create `/etc/systemd/system/beacon.service`:
```ini
[Unit]
Description=Beacon News Aggregator (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=leonel
WorkingDirectory=/home/leonel/projects/beacon
ExecStart=/usr/bin/docker compose run --rm beacon
StandardOutput=append:/home/leonel/projects/beacon/logs/beacon.log
StandardError=append:/home/leonel/projects/beacon/logs/beacon.log
```

Create `/etc/systemd/system/beacon.timer`:
```ini
[Unit]
Description=Run Beacon every 2 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable beacon.timer
sudo systemctl start beacon.timer
```

### Option 2: Cron with Docker
```bash
crontab -e
# Add: Run every 2 hours
0 */2 * * * cd /home/leonel/projects/beacon && /usr/bin/docker compose run --rm beacon >> logs/beacon.log 2>&1
```

### Option 3: Host Cron with uv (without Docker)
For local development without containers:
```bash
crontab -e
# Add: Run every 2 hours
0 */2 * * * cd /home/leonel/projects/beacon && /home/leonel/.local/bin/uv run python src/main.py >> logs/beacon.log 2>&1
```

## Database Schema

### seen_articles table (SQLite)
```sql
CREATE TABLE seen_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relevance_score INTEGER,
    notified BOOLEAN DEFAULT 0
);
```

## Performance Considerations

### Raspberry Pi 5 Optimization
- Use llama3.2:1b for fastest processing (~5-10s per article)
- Limit concurrent article processing to avoid memory issues
- Consider batch processing for multiple articles
- Use connection pooling for Ollama API
- Docker adds ~50-100MB overhead per container

### Expected Resource Usage
- **Memory**:
  - Ollama container: 1.5-2GB with llama3.2:1b loaded
  - Beacon container: ~100-200MB during execution
  - Total: ~2GB peak usage
- **CPU**: Spikes during LLM inference, idle between runs
- **Network**: Minimal (article scraping + webhook POST)
- **Storage**:
  - Docker images: ~2GB
  - Ollama model: ~1.3GB (1b) or ~2GB (3b)
  - Database: grows slowly (~1MB per 1000 articles)

## Testing Installation

### Test Ollama Container
```bash
# Check if Ollama is running
docker compose ps

# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Test: Is this relevant to technology news? Article: New smartphone released with advanced AI features.",
  "stream": false
}'
```

### Test Beacon Container
```bash
# Manual test run
docker compose run --rm beacon

# Check logs
docker compose logs beacon
docker compose logs ollama
```

## Security Considerations

- Keep Discord webhook URL in `.env` file (never commit to git)
- Add `.env` to `.gitignore`
- Use Docker's user namespace remapping for additional isolation
- Don't run containers as root in production
- Validate and sanitize all scraped content before processing
- Rate-limit scraping to be respectful to news websites
- Regularly update Docker images for security patches

### Recommended .gitignore
```
# Environment variables
.env

# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Testing
.pytest_cache/
.coverage
htmlcov/

# Ruff
.ruff_cache/

# uv
uv.lock

# Data
data/
*.db
*.db-journal

# IDE
.vscode/
.idea/
*.swp
```
