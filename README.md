# Beacon - AI-Powered News Aggregator

An intelligent news aggregator that scrapes local news websites, analyzes articles using a local LLM (Ollama), and delivers personalized, relevant news to your Discord via webhooks.

## Overview

Beacon is designed to run on a Raspberry Pi 5 using Docker containers, periodically checking news sources and filtering articles based on your personal interests. Only relevant news reaches your phone through Discord notifications.

## Key Features

- **Automated News Scraping**: Fetches articles from configurable local news websites
- **AI-Powered Filtering**: Uses Ollama (llama3.2:1b or 3b) to analyze full article content
- **Personalized Relevance**: Filters based on your interests defined in markdown
- **Discord Integration**: Sends filtered news directly to your Discord server via webhook
- **Duplicate Prevention**: Tracks seen articles in a local database
- **Scheduled Execution**: Runs periodically via systemd timer with Docker
- **Containerized Deployment**: Isolated, reproducible environment using Docker Compose
- **Modern Python Tooling**: Uses uv for dependencies, ruff for linting, pytest for testing
- **Raspberry Pi Optimized**: Lightweight and efficient for ARM architecture

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              Host System (Raspberry Pi)              │
│                                                      │
│  ┌────────────────────┐    ┌──────────────────────┐ │
│  │  Ollama Service    │    │  Beacon Container    │ │
│  │  (llama3.2:1b)     │◄───│  (Python 3.14 + uv)  │ │
│  └────────────────────┘    │                      │ │
│                            │  Article Scraper     │ │
│                            │  LLM Filter          │ │
│                            │  Discord Notifier    │ │
│                            │                      │ │
│                            │  SQLite Database     │ │
│                            └──────┬───────────────┘ │
└───────────────────────────────────┼──────────────────┘
                                    │
            ┌───────────────────────┼─────────────────┐
            │                       │                 │
            ▼                       ▼                 ▼
    ┌───────────────┐      ┌──────────────┐  ┌──────────────┐
    │  News Sites   │      │ Preferences  │  │   Discord    │
    │  (scraping)   │      │  (markdown)  │  │   Webhook    │
    └───────────────┘      └──────────────┘  └──────────────┘
```

**Note**: Ollama runs directly on the host system, not in a container. Beacon runs in Docker with host networking to access Ollama.

## Project Structure

```
beacon/
├── README.md                 # This file
├── REQUIREMENTS.md           # Technical requirements and dependencies
├── IMPLEMENTATION.md         # Detailed implementation guide
├── preferences.md            # Your personal interest profile
├── pyproject.toml            # Python project dependencies and configuration
├── Dockerfile                # Container image definition
├── docker-compose.yml        # Container orchestration
├── .env                      # Environment variables (not in git)
├── .gitignore                # Git ignore rules
├── src/
│   ├── __init__.py
│   ├── scraper.py           # News website scraping logic
│   ├── llm_filter.py        # Ollama integration for filtering
│   ├── discord_notifier.py  # Discord webhook integration
│   ├── database.py          # Article tracking database
│   ├── config.py            # Configuration management
│   └── main.py              # Main orchestration script (logs to stdout)
├── tests/                    # pytest test suite
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_scraper.py
│   ├── test_llm_filter.py
│   └── test_discord.py
├── config/
│   └── config.yaml          # Configuration (URLs, webhook, schedule)
└── data/                     # Volume mount for persistence
    └── seen_articles.db     # SQLite database for tracking
```

## Quick Start

### Prerequisites
- Raspberry Pi 5 (or compatible Linux system)
- Docker and Docker Compose installed
- **Ollama installed and running** with llama3.2:1b model
- Discord webhook URL

### Setup (5 minutes)

```bash
# 1. Clone or create project directory
cd /home/leonel/projects/beacon

# 2. Verify Ollama is running
curl http://localhost:11434/api/tags

# 3. Create environment file
echo "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN" > .env

# 4. Customize your preferences
# Edit preferences.md with your interests

# 5. Configure news sources
# Edit config/config.yaml with your local news website(s)

# 6. Build container
docker compose build

# 7. Test run (logs to stdout)
docker compose run --rm beacon

# 8. Setup scheduled execution (see IMPLEMENTATION.md)
```

### Development

For local development without Docker:

```bash
# Ensure Ollama is running on localhost
curl http://localhost:11434/api/tags

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format and lint
uv run ruff format . && uv run ruff check .

# Run application (logs to stdout)
uv run python src/main.py
```

## Configuration Files

- **preferences.md**: Define your interests, topics to follow, and keywords to prioritize
- **config/config.yaml**: Set news sources, Discord webhook URL, and scraping intervals
- **.env**: Store Discord webhook URL (never commit to git)
- **pyproject.toml**: Python dependencies and tool configuration

## Hardware Requirements

- **Raspberry Pi 5** (or similar ARM64 device)
- **Minimum 4GB RAM** (8GB recommended for llama3.2:3b)
- **10GB storage** for Docker image, Ollama (host), model, and database

## Model Recommendations

- **llama3.2:1b**: Fastest, lowest memory (1.3GB), good for basic filtering
- **llama3.2:3b**: Better reasoning (2GB RAM), recommended for more accurate relevance detection

## Technology Stack

- **Python 3.14**: Application runtime
- **uv**: Fast Python package manager
- **ruff**: Code formatting and linting
- **pytest**: Testing framework
- **Docker**: Containerization (Beacon only)
- **Ollama**: Local LLM inference (runs on host)
- **SQLAlchemy**: Database ORM
- **BeautifulSoup**: HTML parsing

## Documentation

- [REQUIREMENTS.md](./REQUIREMENTS.md) - Dependencies, Docker setup, configuration
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Step-by-step implementation guide
- [preferences.md](./preferences.md) - Template for your interest profile

## License

MIT License - See LICENSE file for details
