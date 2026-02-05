# Technical Requirements

## System Requirements

### Hardware
- **Platform**: Raspberry Pi 5 (ARM64) or compatible Linux system
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space (for Ollama model, Python env, and database)
- **Network**: Stable internet connection for scraping and Discord

### Operating System
- Raspberry Pi OS (Debian-based) or Ubuntu 22.04+ ARM64

## Software Dependencies

### Core Dependencies

#### Python 3.10+
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Ollama
Install on Raspberry Pi:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull the model:
```bash
# Option 1: Lightweight (recommended for Pi 5 with 4GB RAM)
ollama pull llama3.2:1b

# Option 2: Better accuracy (requires 8GB RAM)
ollama pull llama3.2:3b
```

### Python Packages

Create `requirements.txt`:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
ollama>=0.1.0
pyyaml>=6.0
sqlalchemy>=2.0.0
discord-webhook>=1.3.0
schedule>=1.2.0
python-dotenv>=1.0.0
```

Install:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Python Library Purposes

- **requests**: HTTP requests for web scraping and API calls
- **beautifulsoup4 + lxml**: HTML parsing for news article extraction
- **ollama**: Python client for Ollama API
- **pyyaml**: Configuration file parsing
- **sqlalchemy**: Database ORM for article tracking
- **discord-webhook**: Discord webhook integration
- **schedule**: Task scheduling within Python
- **python-dotenv**: Environment variable management

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
  base_url: "http://localhost:11434"
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
```

### Environment Variables (.env)
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

## Scheduling

### Option 1: Systemd Timer (Recommended)

Create `/etc/systemd/system/beacon.service`:
```ini
[Unit]
Description=Beacon News Aggregator
After=network.target

[Service]
Type=oneshot
User=leonel
WorkingDirectory=/home/leonel/projects/beacon
ExecStart=/home/leonel/projects/beacon/venv/bin/python /home/leonel/projects/beacon/src/main.py
Environment=PATH=/home/leonel/projects/beacon/venv/bin:/usr/local/bin:/usr/bin
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

### Option 2: Cron
```bash
crontab -e
# Add: Run every 2 hours
0 */2 * * * cd /home/leonel/projects/beacon && /home/leonel/projects/beacon/venv/bin/python src/main.py >> logs/beacon.log 2>&1
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

### Expected Resource Usage
- **Memory**: 1.5-2GB with llama3.2:1b running
- **CPU**: Spikes during LLM inference, idle between runs
- **Network**: Minimal (article scraping + webhook POST)

## Testing Ollama Installation

```bash
# Test Ollama is running
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Test: Is this relevant to technology news? Article: New smartphone released with advanced AI features.",
  "stream": false
}'
```

## Security Considerations

- Keep Discord webhook URL in `.env` file (never commit to git)
- Add `.env` to `.gitignore`
- Run scraper with minimal user privileges
- Validate and sanitize all scraped content before processing
- Rate-limit scraping to be respectful to news websites
