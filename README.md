# Beacon - AI-Powered News Aggregator

Scrapes local news websites, filters articles using a local LLM (Ollama), and delivers personalized news to Discord.

## Features

- **Automated scraping** from configurable news sources
- **LLM-based filtering** using GitHub Models API (analyzes full article content)
- **Personalized relevance** based on your interests (preferences.md)
- **Discord notifications** for relevant articles only
- **Duplicate prevention** via SQLite database
- **Raspberry Pi 5 optimized** (no local LLM required!)

## Quick Start

### Prerequisites
- Raspberry Pi 5 or Linux system
- GitHub account (free)
- Discord webhook URL

### Setup

```bash
# 1. Create GitHub Personal Access Token
# Visit: https://github.com/settings/personal-access-tokens/new?name=GitHub+Models+token&user_models=read
# Select "Fine-grained tokens" → Resource owner: your account → Permissions: Models (Read)
# Copy the generated token

# 2. Create environment file
cat > .env << EOF
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
GITHUB_MODELS_TOKEN=github_pat_YOUR_TOKEN_HERE
EOF

# 3. Customize preferences
# Edit preferences.md with your interests

# 4. Configure news sources
# Edit config/config.yaml with your local news site(s)

# 5. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 6. Test the setup
uv run python src/main.py --test-llm
uv run python src/main.py --dry-run
```

## Configuration

### preferences.md
Define your interests, topics to follow, and keywords. The LLM uses this to score article relevance (1-10).

### config/config.yaml
```yaml
github_models:
  model: "gpt-4o-mini"  # Recommended: best balance
  # Alternatives: "Meta-Llama-3.1-8B-Instruct", "Mistral-Nemo"

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
- GitHub Models already uses GPT-4o-mini which has excellent reasoning

### Missing relevant articles?
- Lower `min_relevance_score` in config.yaml (e.g., 8 → 7)
- Add more keywords to preferences.md
- Check LLM reasoning in logs

### Rate Limits?
- Free tier: 150 requests/day for low-tier models (10 req/min)
- If you hit limits, reduce `max_articles_per_run` in config.yaml
- Or space out runs more (every 4 hours instead of 2)

## Model Recommendations

GitHub Models provides free API access to powerful models:

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| gpt-4o-mini | Fast | Excellent | **Recommended** - Best reasoning |
| Meta-Llama-3.1-8B-Instruct | Fast | Good | Open source option |
| Mistral-Nemo | Fast | Good | Alternative option |
| gpt-4o | Slower | Best | For complex analysis |

```bash
# Switch models - Edit config/config.yaml:
# model: "gpt-4o-mini"
```

**No local installation required!** All models run in the cloud via GitHub's API.

**Available models**: Run `uv run python -c "import requests, os; r=requests.get('https://models.inference.ai.azure.com/models', headers={'Authorization': f'Bearer {os.getenv(\"GITHUB_MODELS_TOKEN\")}'}).json(); print('\n'.join([m['name'] for m in r if m['task']=='chat-completion']))"` to see all available chat models.

## Technology Stack

- **Python 3.14** + uv (package manager)
- **GitHub Models API** (cloud LLM inference - no local GPU needed!)
- **OpenAI SDK** (API client)
- **SQLite** (article tracking)
- **BeautifulSoup** (HTML parsing)
- **pytest + ruff** (testing + linting)

## License

MIT License
