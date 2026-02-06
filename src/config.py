"""Configuration module for loading and validating settings."""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Beacon."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        # Load environment variables from .env file
        load_dotenv()

        # Load YAML configuration
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

        # Replace environment variable placeholders
        self._substitute_env_vars(self.config)

        # Validate configuration
        self._validate()

        logger.info(f"Configuration loaded from {self.config_path}")

    def _substitute_env_vars(self, obj: Any) -> None:
        """Recursively substitute ${VAR} with environment variables.

        Args:
            obj: Dictionary or value to process
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]  # Extract VAR from ${VAR}
                    obj[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                self._substitute_env_vars(item)

    def _validate(self) -> None:
        """Validate required configuration fields."""
        required_sections = ["news_sources", "github_models", "discord", "database", "filtering"]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate Discord webhook URL
        webhook_url = self.config["discord"].get("webhook_url", "")
        if not webhook_url or webhook_url.startswith("${"):
            logger.warning("Discord webhook URL not set. Set DISCORD_WEBHOOK_URL in .env file")

        # Validate news sources
        if not self.config["news_sources"]:
            raise ValueError("No news sources configured")

        for source in self.config["news_sources"]:
            if "url" not in source or "selectors" not in source:
                raise ValueError(f"Invalid news source configuration: {source}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can use dot notation: "ollama.model")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_news_sources(self) -> list:
        """Get list of news sources to scrape.

        Returns:
            List of news source configurations
        """
        return self.config.get("news_sources", [])

    def get_github_models_config(self) -> Dict[str, Any]:
        """Get GitHub Models configuration.

        Returns:
            GitHub Models configuration dictionary
        """
        return self.config.get("github_models", {})

    def get_discord_webhook(self) -> str:
        """Get Discord webhook URL.

        Returns:
            Discord webhook URL
        """
        return self.config.get("discord", {}).get("webhook_url", "")

    def get_database_path(self) -> str:
        """Get database file path.

        Returns:
            Path to SQLite database file
        """
        return self.config.get("database", {}).get("path", "./data/seen_articles.db")

    def get_preferences_file(self) -> str:
        """Get path to preferences file.

        Returns:
            Path to preferences markdown file
        """
        return self.config.get("filtering", {}).get("preferences_file", "./preferences.md")

    def get_min_relevance_score(self) -> int:
        """Get minimum relevance score threshold.

        Returns:
            Minimum score (1-10) for notifying about articles
        """
        return self.config.get("filtering", {}).get("min_relevance_score", 7)
