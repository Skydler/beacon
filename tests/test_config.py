"""Unit tests for configuration module."""

import os

import pytest

from src.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary configuration file for testing."""
    config_content = """
news_sources:
  - name: "Test News"
    url: "https://test.com"
    selectors:
      article_list: ".article"
      title: "h1"

ollama:
  base_url: "http://localhost:11434"
  model: "llama3.2:1b"
  timeout: 60

discord:
  webhook_url: "${DISCORD_WEBHOOK_URL}"

database:
  path: "./data/test.db"

filtering:
  preferences_file: "./preferences.md"
  min_relevance_score: 7
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)


def test_config_loads_successfully(temp_config):
    """Test that configuration loads without errors."""
    # Set environment variable for test
    os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test/token"

    config = Config(temp_config)

    assert config.config is not None
    assert "news_sources" in config.config


def test_config_validates_required_sections(tmp_path):
    """Test that missing sections raise validation errors."""
    incomplete_config = tmp_path / "incomplete.yaml"
    incomplete_config.write_text("news_sources: []")

    with pytest.raises(ValueError, match="Missing required configuration section"):
        Config(str(incomplete_config))


def test_config_get_with_dot_notation(temp_config):
    """Test getting nested configuration values with dot notation."""
    config = Config(temp_config)

    assert config.get("ollama.model") == "llama3.2:1b"
    assert config.get("ollama.base_url") == "http://localhost:11434"
    assert config.get("nonexistent.key", "default") == "default"


def test_config_get_news_sources(temp_config):
    """Test getting news sources."""
    config = Config(temp_config)

    sources = config.get_news_sources()

    assert len(sources) == 1
    assert sources[0]["name"] == "Test News"
    assert sources[0]["url"] == "https://test.com"


def test_config_environment_variable_substitution(temp_config):
    """Test that environment variables are substituted."""
    test_webhook = "https://discord.com/webhooks/12345/abcdef"
    os.environ["DISCORD_WEBHOOK_URL"] = test_webhook

    config = Config(temp_config)

    assert config.get_discord_webhook() == test_webhook


def test_config_file_not_found():
    """Test that missing config file raises error."""
    with pytest.raises(FileNotFoundError):
        Config("nonexistent.yaml")


def test_config_helper_methods(temp_config):
    """Test convenience getter methods."""
    config = Config(temp_config)

    assert config.get_database_path() == "./data/test.db"
    assert config.get_preferences_file() == "./preferences.md"
    assert config.get_min_relevance_score() == 7


def test_config_invalid_news_source(tmp_path):
    """Test that invalid news source configuration is rejected."""
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("""
news_sources:
  - name: "Bad Source"
    # Missing url and selectors
ollama:
  base_url: "http://localhost:11434"
discord:
  webhook_url: "test"
database:
  path: "./data/test.db"
filtering:
  preferences_file: "./preferences.md"
  min_relevance_score: 7
""")

    with pytest.raises(ValueError, match="Invalid news source"):
        Config(str(bad_config))
