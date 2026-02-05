# Implementation Guide for Beacon

This document provides detailed instructions for implementing the Beacon news aggregator. Follow these steps sequentially.

## Deployment Options

This guide covers two deployment approaches:
1. **Docker Deployment (Recommended)**: Containerized, isolated, production-ready
2. **Local Development**: Native Python with uv for development and testing

Most users should follow the Docker deployment path. Use local development only if you need to modify and test the code.

## Phase 1: Project Setup

### 1.1 Initialize Project Structure
```bash
cd /home/leonel/projects/beacon
mkdir -p src tests config data
touch src/__init__.py
touch tests/__init__.py
```

### 1.2 Setup Environment Variables
```bash
# Create .env file
cat > .env << 'EOF'
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
EOF
```

### 1.3 Create .gitignore
```bash
cat > .gitignore << 'EOF'
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
EOF
```

### 1.4 Create pyproject.toml
```bash
cat > pyproject.toml << 'EOF'
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
addopts = "-v --strict-markers"
EOF
```

### 1.5 Setup Docker (Recommended Deployment)

#### Create Dockerfile
```bash
cat > Dockerfile << 'EOF'
FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY preferences.md ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --no-dev

# Create data directory
RUN mkdir -p /app/data

# Run the application (logs to stdout)
CMD ["uv", "run", "python", "src/main.py"]
EOF
```

#### Create docker-compose.yml
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  beacon:
    build: .
    container_name: beacon-aggregator
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
    volumes:
      - ./data:/app/data
      - ./config/config.yaml:/app/config/config.yaml:ro
      - ./preferences.md:/app/preferences.md:ro
    restart: "no"  # Use systemd timer for scheduling
    # Use host network to access Ollama on host
    network_mode: host
EOF
```

**Note**: This configuration assumes Ollama is already running on the host system at `localhost:11434`. The container uses `network_mode: host` to access it.

#### Build Container
```bash
# Build the Beacon image
docker compose build

# Test Beacon (one-time run, logs to stdout)
docker compose run --rm beacon
```

### 1.6 Setup Local Development (Optional)

Only follow this if you need to develop and test code locally.

#### Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # Add uv to PATH
```

#### Create Virtual Environment
```bash
# uv automatically creates .venv/
uv sync --all-extras  # Install all dependencies including dev
```

#### Configure for Local Ollama (for development)
Ensure Ollama is running locally:
```bash
# Verify Ollama is accessible
curl http://localhost:11434/api/tags

# Update config.yaml to use localhost:11434
# The default configuration already points to localhost
```

## Phase 2: Core Components

### 2.0 Code Quality Standards

All Python modules should follow these standards:

**Type Hints**: Use type hints for all function parameters and return values
```python
from typing import List, Dict, Optional

def is_article_seen(url: str) -> bool:
    """Check if article URL exists in database."""
    pass

def scrape_articles(url: str) -> List[Dict[str, str]]:
    """Scrape articles from a news site."""
    pass
```

**Code Formatting and Linting**:
```bash
# Format code with ruff (local development)
uv run ruff format src/

# Check for linting issues
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Run both format and check
uv run ruff format src/ && uv run ruff check src/
```

**Docstrings**: Use Google-style docstrings for all public functions
```python
def analyze_article(article: Dict[str, str], preferences: str) -> tuple[int, str]:
    """Analyze article relevance using LLM.

    Args:
        article: Dictionary containing title, content, and URL
        preferences: User's preference markdown content

    Returns:
        Tuple of (relevance_score, reasoning)
    """
    pass
```

### 2.1 Database Module (src/database.py)

**Purpose**: Manage article tracking to prevent duplicate notifications

**Key Functions**:
- `init_db()`: Create database and tables
- `is_article_seen(url)`: Check if article was already processed
- `mark_article_seen(url, title, relevance_score)`: Record processed article
- `get_recent_articles(days=7)`: Retrieve recently seen articles for context

**Implementation Notes**:
- Use SQLAlchemy ORM for database operations
- SQLite database stored in `data/seen_articles.db`
- Include timestamp for all records
- Add index on URL for fast lookups

**Schema**:
```python
class Article(Base):
    __tablename__ = 'seen_articles'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    relevance_score = Column(Integer)
    notified = Column(Boolean, default=False)
```

### 2.2 Web Scraper Module (src/scraper.py)

**Purpose**: Extract news articles from websites

**Key Functions**:
- `scrape_news_site(url, selectors)`: Generic scraping function
- `extract_article_content(article_url)`: Get full article text
- `parse_html(html_content, selectors)`: Parse with BeautifulSoup

**Implementation Notes**:
- Use generic CSS selectors configurable per news site
- Handle pagination if present
- Implement rate limiting (sleep between requests)
- User-Agent string to identify bot politely
- Robust error handling for network issues
- Extract: title, URL, description/excerpt, publication date
- For full article content: strip ads, menus, footers

**Scraping Strategy**:
```python
# Step 1: Get article list from homepage/section
articles = scrape_news_site(base_url, selectors)

# Step 2: For each article, get full content
for article in articles:
    full_content = extract_article_content(article['url'])
    article['content'] = full_content
```

**Error Handling**:
- Timeout after 30 seconds per request
- Retry failed requests (max 3 attempts)
- Log all scraping errors
- Continue processing other articles if one fails

### 2.3 LLM Filter Module (src/llm_filter.py)

**Purpose**: Use Ollama to determine article relevance

**Key Functions**:
- `load_preferences(preferences_file)`: Load user interests from markdown
- `analyze_article(article, preferences)`: Send to LLM for analysis
- `parse_llm_response(response)`: Extract relevance score and reasoning

**Implementation Notes**:
- Load preferences.md into context
- Construct effective prompts for the LLM
- Request structured output (relevance score 1-10 + brief reasoning)
- Handle Ollama API connection errors
- Timeout protection (60s max per article)
- Consider chunking very long articles

**LLM Prompt Template**:
```python
RELEVANCE_PROMPT = """You are a personal news filter. Based on the user's interests below, determine if this article is relevant.

USER INTERESTS:
{preferences}

ARTICLE:
Title: {title}
Content: {content}

TASK:
Rate relevance from 1-10 (10 = highly relevant, 1 = not relevant).
Provide your rating and a one-sentence explanation.

FORMAT YOUR RESPONSE AS:
SCORE: [number]
REASON: [brief explanation]
"""
```

**Ollama Integration**:
- Use `ollama.generate()` or `ollama.chat()` API
- Set `temperature=0.3` for consistent scoring
- Extract score and reason from response
- Log all LLM interactions for debugging

### 2.4 Discord Notifier Module (src/discord_notifier.py)

**Purpose**: Send filtered articles to Discord webhook

**Key Functions**:
- `send_article(article, relevance_score, reason)`: Post to Discord
- `format_discord_embed(article)`: Create rich embed message
- `batch_send(articles)`: Send multiple articles efficiently

**Implementation Notes**:
- Use Discord webhook library or direct HTTP POST
- Create rich embeds with title, link, excerpt
- Include relevance score and LLM reasoning
- Handle rate limits (Discord allows ~5 requests/second)
- Retry failed sends with exponential backoff

**Discord Embed Format**:
```python
{
    "embeds": [{
        "title": article_title,
        "url": article_url,
        "description": article_excerpt[:200],
        "color": 3447003,  # Blue
        "fields": [
            {"name": "Relevance", "value": f"{score}/10", "inline": True},
            {"name": "Why", "value": reason, "inline": False}
        ],
        "timestamp": datetime.utcnow().isoformat()
    }]
}
```

### 2.5 Configuration Module (src/config.py)

**Purpose**: Load and validate configuration

**Key Functions**:
- `load_config()`: Load YAML config and environment variables
- `validate_config(config)`: Check required fields
- `get_news_sources()`: Return list of sources to scrape

**Implementation Notes**:
- Use PyYAML to parse config.yaml
- Load environment variables with python-dotenv
- Validate Discord webhook URL format
- Provide sensible defaults

### 2.6 Main Orchestrator (src/main.py)

**Purpose**: Coordinate all components

**Main Workflow**:
```python
def main():
    # 1. Load configuration and preferences
    config = load_config()
    preferences = load_preferences(config['filtering']['preferences_file'])

    # 2. Initialize database
    init_db(config['database']['path'])

    # 3. For each news source
    for source in config['news_sources']:
        # 4. Scrape articles
        articles = scrape_news_site(source['url'], source['selectors'])

        # 5. Filter out already-seen articles
        new_articles = [a for a in articles if not is_article_seen(a['url'])]

        # 6. Get full content for new articles
        for article in new_articles:
            article['content'] = extract_article_content(article['url'])

            # 7. Analyze with LLM
            score, reason = analyze_article(article, preferences)

            # 8. If relevant enough, send to Discord
            if score >= config['filtering']['min_relevance_score']:
                send_article(article, score, reason)

            # 9. Mark as seen in database
            mark_article_seen(article['url'], article['title'], score)

    # 10. Log completion
    logging.info(f"Beacon run completed at {datetime.now()}")
```

**Error Handling**:
- Wrap entire main() in try/except
- Log all errors to stdout
- Don't let one failed article stop processing
- Send error summary to Discord if critical failure

## Phase 3: Configuration Files

### 3.1 Create config.yaml
```bash
mkdir -p config
cat > config/config.yaml << 'EOF'
news_sources:
  # Template - adjust selectors for your specific news site
  - name: "Example Local News"
    url: "https://example.com/news"
    selectors:
      article_list: "article.news-item"  # CSS selector for article containers
      title: "h2.title"                  # Title within each article
      link: "a.read-more"                # Link to full article
      description: "p.excerpt"           # Short description/excerpt

ollama:
  # Ollama is assumed to be running externally (host system)
  base_url: "http://localhost:11434"  # Localhost when using host network
  model: "llama3.2:1b"
  timeout: 60

discord:
  webhook_url: "${DISCORD_WEBHOOK_URL}"

database:
  path: "./data/seen_articles.db"

scraping:
  check_interval: 7200  # 2 hours
  max_articles_per_run: 20
  user_agent: "Mozilla/5.0 (compatible; BeaconBot/1.0)"

filtering:
  preferences_file: "./preferences.md"
  min_relevance_score: 7

logging:
  level: "INFO"
  # Logs are sent to stdout (captured by Docker/systemd)
EOF
```

### 3.2 Create preferences.md Template
See the separate preferences.md file for the complete template.

## Phase 4: Testing

### 4.1 Unit Tests with pytest

Create test files in `tests/` directory:

**tests/test_database.py** - Test article tracking:
```python
import pytest
from src.database import init_db, is_article_seen, mark_article_seen

def test_article_tracking():
    """Test that articles are tracked correctly."""
    init_db(":memory:")  # Use in-memory DB for tests

    url = "https://example.com/article1"
    assert not is_article_seen(url)

    mark_article_seen(url, "Test Article", 8)
    assert is_article_seen(url)
```

**tests/test_scraper.py** - Test HTML parsing with mock data
**tests/test_llm_filter.py** - Test prompt construction
**tests/test_discord.py** - Test message formatting

**Running Tests**:
```bash
# Local development with uv
uv run pytest                          # Run all tests
uv run pytest -v                       # Verbose output
uv run pytest tests/test_database.py   # Run specific test file
uv run pytest -k "test_article"        # Run tests matching pattern
uv run pytest --cov=src                # Run with coverage
uv run pytest --cov=src --cov-report=html  # HTML coverage report

# In Docker (build test image first)
docker compose run --rm beacon pytest
```

### 4.2 Code Quality Checks

```bash
# Format code
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Pre-commit check (format + lint + test)
uv run ruff format . && uv run ruff check . && uv run pytest
```

### 4.3 Integration Testing

Add CLI flags to src/main.py for testing:
```bash
# Local development
uv run python src/main.py --test-scraper
uv run python src/main.py --test-llm
uv run python src/main.py --test-discord
uv run python src/main.py --dry-run

# Docker
docker compose run --rm beacon python src/main.py --test-scraper
docker compose run --rm beacon python src/main.py --dry-run
```

### 4.4 Manual Testing Checklist

**Docker Deployment**:
- [ ] Ollama container starts and responds to API calls
- [ ] Beacon container builds successfully
- [ ] Beacon can connect to Ollama (check logs)
- [ ] Discord webhook receives test messages
- [ ] Database persists between runs (check data/ volume)
- [ ] Logs are written to logs/ volume
- [ ] Config and preferences are mounted correctly

**Application Logic**:
- [ ] Scraper extracts articles from configured websites
- [ ] Database tracks seen articles
- [ ] LLM returns relevance scores
- [ ] Duplicate articles are filtered out
- [ ] Only relevant articles (score >= threshold) sent to Discord

**Testing Commands**:
```bash
# Check container status
docker compose ps

# View logs
docker compose logs ollama
docker compose logs beacon

# Test Ollama API
curl http://localhost:11434/api/generate -d '{"model": "llama3.2:1b", "prompt": "Test", "stream": false}'

# Manual run
docker compose run --rm beacon

# Check database
sqlite3 data/seen_articles.db "SELECT COUNT(*) FROM seen_articles;"
```

## Phase 5: Deployment

### 5.1 Prepare Directories
```bash
mkdir -p data
chmod 755 data
```

### 5.2 Verify Ollama Accessibility

```bash
# Ensure Ollama is running and accessible
curl http://localhost:11434/api/tags

# Verify the required model is available
curl http://localhost:11434/api/tags | grep llama3.2:1b

# If model is not available, pull it:
# ollama pull llama3.2:1b
```

### 5.3 Test Docker Service

```bash
# Build the Beacon image
docker compose build

# Test Beacon with a manual run (logs to stdout)
docker compose run --rm beacon
```

### 5.4 Setup Scheduled Execution

#### Option A: Systemd Timer (Recommended)

Create `/etc/systemd/system/beacon.service`:
```bash
sudo tee /etc/systemd/system/beacon.service > /dev/null << 'EOF'
[Unit]
Description=Beacon News Aggregator (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=leonel
WorkingDirectory=/home/leonel/projects/beacon
Environment=COMPOSE_FILE=/home/leonel/projects/beacon/docker-compose.yml
ExecStart=/usr/bin/docker compose run --rm beacon
# Logs go to journald (stdout/stderr)
StandardOutput=journal
StandardError=journal
EOF
```

Create `/etc/systemd/system/beacon.timer`:
```bash
sudo tee /etc/systemd/system/beacon.timer > /dev/null << 'EOF'
[Unit]
Description=Run Beacon News Aggregator every 2 hours
Requires=beacon.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

Enable and start the timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable beacon.timer
sudo systemctl start beacon.timer
```

#### Option B: Cron

```bash
crontab -e
# Add this line (logs to syslog):
0 */2 * * * cd /home/leonel/projects/beacon && /usr/bin/docker compose run --rm beacon 2>&1 | logger -t beacon
```

### 5.5 Verify Deployment

```bash
# Check timer status
systemctl status beacon.timer
systemctl list-timers beacon.timer

# Check service logs (systemd captures stdout/stderr)
journalctl -u beacon.service -f

# Check application output from last run
journalctl -u beacon.service -n 100

# Check Docker container status
docker compose ps

# Check database
ls -lh data/seen_articles.db
sqlite3 data/seen_articles.db "SELECT COUNT(*) FROM seen_articles;"

# Manual trigger for testing
sudo systemctl start beacon.service
# Or manually
docker compose run --rm beacon

# View logs with syslog (if using cron with logger)
tail -f /var/log/syslog | grep beacon
```

## Phase 6: Customization

### 6.1 Finding CSS Selectors for Your News Site
1. Open the news website in a browser
2. Open Developer Tools (F12)
3. Use Inspector to identify article containers
4. Note the CSS classes and structure
5. Test selectors in browser console:
   ```javascript
   document.querySelectorAll('article.news-item')
   ```
6. Update config.yaml with correct selectors

### 6.2 Tuning LLM Performance

**If too many false positives** (irrelevant articles sent):
- Increase `min_relevance_score` in config.yaml (e.g., from 7 to 8)
- Refine preferences.md with more specific interests

**If missing relevant articles**:
- Lower `min_relevance_score` in config.yaml (e.g., from 7 to 6)
- Add more keywords to preferences.md

**If too slow**:
- Keep using llama3.2:1b (fastest)
- Reduce `max_articles_per_run` in config
- Process only headlines first, then full content

**If inaccurate filtering**:
- Upgrade to llama3.2:3b for better reasoning
```bash
# Pull model on host Ollama
ollama pull llama3.2:3b
# Update config.yaml model: "llama3.2:3b"
docker compose run --rm beacon  # Test
```

### 6.3 Adjusting Scraping Frequency

**With Systemd Timer** - Edit `/etc/systemd/system/beacon.timer`:
```ini
# Every hour
OnUnitActiveSec=1h

# Every 4 hours
OnUnitActiveSec=4h

# Every 6 hours
OnUnitActiveSec=6h

# Daily at 8am (use OnCalendar instead)
OnCalendar=*-*-* 08:00:00

# Twice daily at 8am and 8pm
OnCalendar=*-*-* 08,20:00:00
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart beacon.timer
```

**With Cron**:
```bash
crontab -e

# Every hour
0 * * * * cd /home/leonel/projects/beacon && docker compose run --rm beacon >> logs/cron.log 2>&1

# Every 4 hours
0 */4 * * * cd /home/leonel/projects/beacon && docker compose run --rm beacon >> logs/cron.log 2>&1

# Daily at 8am
0 8 * * * cd /home/leonel/projects/beacon && docker compose run --rm beacon >> logs/cron.log 2>&1
```

### 6.4 Updating the Application

**Rebuild after code changes**:
```bash
# Rebuild Beacon image
docker compose build beacon

# Restart if running as service
docker compose restart beacon

# Or trigger a new run
docker compose run --rm beacon
```

**Update dependencies**:
```bash
# Edit pyproject.toml, then rebuild
docker compose build --no-cache beacon
```

**Update Ollama model** (on host):
```bash
ollama pull llama3.2:1b
# Or pull a different model
ollama pull llama3.2:3b
# Update config.yaml to reference new model
```

## Phase 7: Monitoring and Maintenance

### 7.1 Monitoring

**Daily**:
- Check Discord channel for notifications
- Verify recent articles are relevant

**Weekly**:
```bash
# Review application logs from journald
journalctl -u beacon.service -n 200

# Or if using cron with logger
grep beacon /var/log/syslog | tail -100

# Check database size and article count
ls -lh data/seen_articles.db
sqlite3 data/seen_articles.db "SELECT COUNT(*) FROM seen_articles;"

# Monitor system resources
docker stats --no-stream
htop  # On host system
```

**Monitoring Checks**:
```bash
# Check container status
docker compose ps

# View systemd timer status
systemctl status beacon.timer
systemctl list-timers

# View recent execution logs
journalctl -u beacon.service --since "1 day ago"

# Check Ollama is running on host
curl http://localhost:11434/api/tags
```

### 7.2 Maintenance Tasks

**Weekly**:
- Review false positives/negatives in Discord
- Adjust preferences.md based on results
- Check for errors in journal: `journalctl -u beacon.service -p err`

**Monthly**:
- Clean old articles from database (optional):
```bash
sqlite3 data/seen_articles.db "DELETE FROM seen_articles WHERE scraped_at < datetime('now', '-90 days');"
sqlite3 data/seen_articles.db "VACUUM;"
```
- Update Docker images:
```bash
docker compose pull ollama
docker compose build --no-cache beacon
docker compose restart ollama
```

**As Needed**:
- Update news source selectors if websites change
- Upgrade Ollama model for better accuracy
- Review and optimize LLM prompts

### 7.3 Troubleshooting

**Container Issues**:
```bash
# Ollama not responding
docker compose restart ollama
docker compose logs ollama

# Beacon container fails to start
docker compose logs beacon
docker compose run --rm beacon  # Test manually

# Network issues between containers
docker compose down && docker compose up -d ollama
docker network ls
docker network inspect beacon_default
```

**No articles appearing**:
```bash
# Test scraper
docker compose run --rm beacon python src/main.py --test-scraper

# Check if scraper found articles
docker compose logs beacon | grep -i "found.*articles"

# Verify CSS selectors (website may have changed)
# Update config.yaml selectors
```

**All articles marked as irrelevant**:
```bash
# Test with lower threshold temporarily
# Edit config.yaml: min_relevance_score: 5
docker compose run --rm beacon

# Test LLM directly
docker compose run --rm beacon python src/main.py --test-llm

# Review LLM responses in recent logs
journalctl -u beacon.service -n 200 | grep "SCORE:"
```

**Discord not receiving messages**:
```bash
# Verify webhook URL
echo $DISCORD_WEBHOOK_URL  # Should be set in .env

# Test webhook manually
curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test from Beacon"}'

# Check Discord server permissions (webhook not deleted)

# Check Beacon logs for Discord errors
docker compose logs beacon | grep -i discord
```

**High memory usage**:
```bash
# Check container resource usage
docker stats

# Verify using small model
docker compose exec ollama ollama list

# Reduce max_articles_per_run in config.yaml
# Restart Ollama to free memory
docker compose restart ollama
```

**Database locked errors**:
```bash
# Check if multiple instances are running
docker compose ps
ps aux | grep beacon

# Stop all instances and clear locks
docker compose down
rm -f data/seen_articles.db-journal
```

### 7.4 Backup and Recovery

**Backup Configuration**:
```bash
# Backup critical files
tar -czf beacon-backup-$(date +%Y%m%d).tar.gz \
  config/ \
  preferences.md \
  .env \
  docker-compose.yml \
  pyproject.toml

# Backup database
cp data/seen_articles.db data/seen_articles.db.backup
```

**Restore from Backup**:
```bash
# Extract configuration
tar -xzf beacon-backup-YYYYMMDD.tar.gz

# Rebuild and restart
docker compose build
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:1b
```

## Additional Features to Consider

### Future Enhancements
1. **Multiple Discord channels**: Route articles by category
2. **Web dashboard**: View article history and statistics
3. **Feedback loop**: React to Discord messages to train preferences
4. **Summary generation**: LLM creates brief summaries
5. **Sentiment analysis**: Tag articles as positive/negative/neutral
6. **Topic clustering**: Group related articles together
7. **Multi-language support**: Detect and translate articles
8. **RSS feed support**: Alternative to web scraping
9. **Mobile app**: Native notification system

### Optimization Ideas
1. **Cache scraped HTML**: Avoid re-scraping during testing
2. **Parallel processing**: Analyze multiple articles simultaneously
3. **Incremental scraping**: Only check for new articles since last run
4. **Smart scheduling**: Scrape more frequently during business hours
5. **Content prioritization**: Process breaking news first

## Resources

### Documentation

**Python Libraries**:
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

**Modern Python Tooling**:
- [uv Documentation](https://docs.astral.sh/uv/) - Fast Python package manager
- [Ruff Documentation](https://docs.astral.sh/ruff/) - Fast Python linter and formatter
- [pytest Documentation](https://docs.pytest.org/) - Testing framework

**Docker**:
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Ollama Docker Hub](https://hub.docker.com/r/ollama/ollama)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Scraping Ethics
- Respect robots.txt
- Implement rate limiting (minimum 1-2 seconds between requests)
- Use appropriate User-Agent identifying your bot
- Consider RSS feeds when available
- Don't overwhelm small websites with requests
- Cache results when possible to reduce load
