# Beacon - AI-Powered News Aggregator

An intelligent news aggregator that scrapes local news websites, analyzes articles using a local LLM (Ollama), and delivers personalized, relevant news to your Discord via webhooks.

## Overview

Beacon is designed to run on a Raspberry Pi 5, periodically checking news sources and filtering articles based on your personal interests. Only relevant news reaches your phone through Discord notifications.

## Key Features

- **Automated News Scraping**: Fetches articles from configurable local news websites
- **AI-Powered Filtering**: Uses Ollama (llama3.2:1b or 3b) to analyze full article content
- **Personalized Relevance**: Filters based on your interests defined in markdown
- **Discord Integration**: Sends filtered news directly to your Discord server via webhook
- **Duplicate Prevention**: Tracks seen articles in a local database
- **Scheduled Execution**: Runs periodically via cron/systemd timer
- **Raspberry Pi Optimized**: Lightweight and efficient for ARM architecture

## Architecture

```
┌─────────────────┐
│  News Websites  │
└────────┬────────┘
         │ (scraping)
         ▼
┌─────────────────┐
│ Beacon Scraper  │
│   (Python)      │
└────────┬────────┘
         │ (article content)
         ▼
┌─────────────────┐      ┌──────────────┐
│  Ollama LLM     │◄─────│ Preferences  │
│ (llama3.2:1b)   │      │  (markdown)  │
└────────┬────────┘      └──────────────┘
         │ (filtered articles)
         ▼
┌─────────────────┐      ┌──────────────┐
│ Article DB      │      │    Discord   │
│ (SQLite)        │      │   Webhook    │
└─────────────────┘      └──────────────┘
```

## Project Structure

```
beacon/
├── README.md                 # This file
├── REQUIREMENTS.md           # Technical requirements and dependencies
├── IMPLEMENTATION.md         # Detailed implementation guide
├── preferences.md            # Your personal interest profile
├── src/
│   ├── scraper.py           # News website scraping logic
│   ├── llm_filter.py        # Ollama integration for filtering
│   ├── discord_notifier.py  # Discord webhook integration
│   ├── database.py          # Article tracking database
│   └── main.py              # Main orchestration script
├── config/
│   └── config.yaml          # Configuration (URLs, webhook, schedule)
└── data/
    └── seen_articles.db     # SQLite database for tracking
```

## Quick Start

See [IMPLEMENTATION.md](./IMPLEMENTATION.md) for detailed setup instructions.

## Configuration Files

- **preferences.md**: Define your interests, topics to follow, and keywords to prioritize
- **config/config.yaml**: Set news sources, Discord webhook URL, and scraping intervals

## Hardware Requirements

- **Raspberry Pi 5** (or similar ARM device)
- **Minimum 4GB RAM** (8GB recommended for llama3.2:3b)
- **10GB storage** for Ollama model and article database

## Model Recommendations

- **llama3.2:1b**: Fastest, lowest memory (1.3GB), good for basic filtering
- **llama3.2:3b**: Better reasoning (2GB RAM), recommended for more accurate relevance detection

## License

MIT License - See LICENSE file for details
