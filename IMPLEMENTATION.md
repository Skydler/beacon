# Implementation Guide for Beacon

This document provides detailed instructions for implementing the Beacon news aggregator. Follow these steps sequentially.

## Phase 1: Project Setup

### 1.1 Initialize Project Structure
```bash
cd /home/leonel/projects/beacon
mkdir -p src config data logs
touch src/__init__.py
```

### 1.2 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Create requirements.txt
See REQUIREMENTS.md for the full list. Create and install:
```bash
pip install requests beautifulsoup4 lxml ollama pyyaml sqlalchemy discord-webhook schedule python-dotenv
pip freeze > requirements.txt
```

### 1.4 Setup Environment Variables
```bash
# Create .env file
cat > .env << 'EOF'
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
EOF

# Add to .gitignore
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "data/" >> .gitignore
echo "logs/" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### 1.5 Install and Configure Ollama
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama

# Pull the model
ollama pull llama3.2:1b
```

## Phase 2: Core Components

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
- Log all errors to logs/beacon.log
- Don't let one failed article stop processing
- Send error summary to Discord if critical failure

## Phase 3: Configuration Files

### 3.1 Create config.yaml
```bash
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
  base_url: "http://localhost:11434"
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
  file: "./logs/beacon.log"
EOF
```

### 3.2 Create preferences.md Template
See the separate preferences.md file for the complete template.

## Phase 4: Testing

### 4.1 Unit Tests
Create `tests/` directory with:
- `test_database.py`: Test article tracking
- `test_scraper.py`: Test HTML parsing (use mock HTML)
- `test_llm_filter.py`: Test prompt construction
- `test_discord.py`: Test message formatting

### 4.2 Integration Testing
```bash
# Test individual components
python src/main.py --test-scraper
python src/main.py --test-llm
python src/main.py --test-discord

# Dry run (scrape and filter but don't send to Discord)
python src/main.py --dry-run
```

### 4.3 Manual Testing Checklist
- [ ] Ollama responds to API calls
- [ ] Scraper extracts articles correctly
- [ ] Database creates and tracks articles
- [ ] LLM returns relevance scores
- [ ] Discord webhook receives messages
- [ ] Duplicate articles are filtered
- [ ] Config loads correctly
- [ ] Logging works properly

## Phase 5: Deployment

### 5.1 Setup Logging
```bash
mkdir -p logs
touch logs/beacon.log
```

### 5.2 Create Systemd Timer
```bash
sudo cp systemd/beacon.service /etc/systemd/system/
sudo cp systemd/beacon.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable beacon.timer
sudo systemctl start beacon.timer
```

### 5.3 Verify Scheduled Execution
```bash
# Check timer status
systemctl status beacon.timer

# Check service logs
journalctl -u beacon.service -f

# Check application logs
tail -f logs/beacon.log
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
- **If too many false positives**: Increase min_relevance_score
- **If missing relevant articles**: Lower min_relevance_score
- **If too slow**: Consider using headlines-only mode
- **If inaccurate**: Try llama3.2:3b instead of 1b

### 6.3 Adjusting Scraping Frequency
Edit beacon.timer:
```ini
# Every hour
OnUnitActiveSec=1h

# Every 4 hours
OnUnitActiveSec=4h

# Daily at 8am (use OnCalendar instead)
OnCalendar=*-*-* 08:00:00
```

## Phase 7: Monitoring and Maintenance

### 7.1 Monitoring
- Check Discord channel for notifications
- Review logs weekly: `tail -100 logs/beacon.log`
- Monitor database size: `ls -lh data/seen_articles.db`
- Check Raspberry Pi resources: `htop`

### 7.2 Maintenance Tasks
- **Weekly**: Review false positives/negatives, adjust preferences.md
- **Monthly**: Clean old articles from database (keep last 90 days)
- **As needed**: Update news source selectors if website changes
- **As needed**: Retrain expectations by reviewing LLM reasoning

### 7.3 Troubleshooting

**No articles appearing**:
- Check if scraper is finding articles: `python src/main.py --test-scraper`
- Verify CSS selectors match current website HTML
- Check network connectivity

**All articles marked as irrelevant**:
- Review preferences.md - might be too narrow
- Lower min_relevance_score temporarily
- Test LLM with sample article: `python src/main.py --test-llm`

**Discord not receiving messages**:
- Verify webhook URL in .env
- Test webhook manually: `curl -X POST $DISCORD_WEBHOOK_URL -H "Content-Type: application/json" -d '{"content": "Test"}'`
- Check Discord server permissions

**High memory usage**:
- Confirm using llama3.2:1b not larger model
- Reduce max_articles_per_run in config
- Process articles sequentially not in parallel

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
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

### Scraping Ethics
- Respect robots.txt
- Implement rate limiting
- Use appropriate User-Agent
- Consider RSS feeds when available
- Don't overwhelm small websites
