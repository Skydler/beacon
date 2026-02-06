# Beacon - AI-Powered News Aggregator

Scrapes local news websites, filters articles using a local LLM (Ollama), and delivers personalized news to Discord.

## Features

- **Automated scraping** from configurable news sources
- **LLM-based filtering** using Ollama (analyzes full article content)
- **Personalized relevance** based on your interests (preferences.md)
- **Discord notifications** for relevant articles only
- **Duplicate prevention** via SQLite database
- **Raspberry Pi 5 optimized** (lightweight, runs in Docker)

## Quick Start

### Prerequisites
- Raspberry Pi 5 or Linux system
- Docker and Docker Compose
- Ollama installed with llama3.2:1b model
- Discord webhook URL

### Setup

```bash
# 1. Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b  # Recommended: Better reasoning than 1b

# 2. Create environment file
echo "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN" > .env

# 3. Customize preferences
# Edit preferences.md with your interests

# 4. Configure news sources
# Edit config/config.yaml with your local news site(s)

# 5. Build and test
docker compose build
docker compose run --rm beacon

# 6. Setup scheduled execution (every 2 hours)
sudo cp systemd/beacon.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now beacon.timer
```

## Configuration

### preferences.md
Define your interests, topics to follow, and keywords. The LLM uses this to score article relevance (1-10).

### config/config.yaml
```yaml
ollama:
  model: "llama3.2:3b"  # Upgrade from 1b for better accuracy

filtering:
  min_relevance_score: 8  # Only send articles scored 8+/10
```

### News Source Selectors
Update `config/config.yaml` with CSS selectors for your news site:
```yaml
news_sources:
  - name: "Info Quilmes"
    url: "https://www.infoquilmes.com.ar/"
    selectors:
      article_list: "a[href^='noticias/']"
      title: "H4 a, H5 a, H6 a"
      category: "span.volanta"
```

Use browser DevTools (F12) to find the right selectors for your site.

## Project Structure

```
beacon/
├── src/
│   ├── main.py              # Main orchestrator
│   ├── scraper.py           # Web scraping
│   ├── llm_filter.py        # Ollama LLM filtering
│   ├── discord_notifier.py  # Discord webhook
│   ├── database.py          # SQLite article tracking
│   └── config.py            # Configuration loader
├── tests/                    # pytest test suite
├── config/
│   └── config.yaml          # News sources, settings
├── preferences.md           # Your interest profile (LLM context)
├── .env                     # Discord webhook URL (not in git)
├── data/                    # SQLite database (persisted)
├── docker-compose.yml       # Container orchestration
└── pyproject.toml          # Python dependencies
```

## Development

```bash
# Install dependencies (local development)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras

# Run tests
uv run pytest

# Lint and format
uv run ruff format . && uv run ruff check .

# Run locally (without Docker)
uv run python src/main.py
```

## Monitoring

```bash
# Check timer status
systemctl status beacon.timer
systemctl list-timers beacon.timer

# View logs
journalctl -u beacon.service -f

# Check database
sqlite3 data/seen_articles.db "SELECT COUNT(*) FROM seen_articles;"

# Manual run
docker compose run --rm beacon
```

## Tuning

### Too many false positives?
- Increase `min_relevance_score` in config.yaml (e.g., 7 → 8)
- Refine preferences.md with more specific interests
- Upgrade to llama3.2:3b for better reasoning

### Missing relevant articles?
- Lower `min_relevance_score` in config.yaml (e.g., 8 → 7)
- Add more keywords to preferences.md
- Check LLM reasoning in logs: `journalctl -u beacon.service | grep "scored"`

### Too slow?
- Use llama3.2:1b (faster, less accurate)
- Reduce `max_articles_per_run` in config.yaml

## Model Recommendations

| Model | RAM | Speed | Accuracy | Use Case |
|-------|-----|-------|----------|----------|
| llama3.2:1b | ~2GB | Fast | Basic | Quick testing |
| llama3.2:3b | ~4GB | Medium | Good | **Recommended** |
| qwen2.5:3b | ~4GB | Medium | Good | Alternative |
| phi3:mini | ~3GB | Medium | Better | If 3b too slow |

```bash
# Switch models
ollama pull llama3.2:3b
# Update config.yaml: model: "llama3.2:3b"
docker compose run --rm beacon  # Test
```

## Technology Stack

- **Python 3.14** + uv (package manager)
- **Ollama** (local LLM inference)
- **Docker** (containerization)
- **SQLite** (article tracking)
- **BeautifulSoup** (HTML parsing)
- **pytest + ruff** (testing + linting)

## License

MIT License
