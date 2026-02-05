"""LLM-based article filtering using Ollama."""

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import ollama

logger = logging.getLogger(__name__)


class LLMFilter:
    """Filter articles using a local LLM (Ollama)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:1b",
        timeout: int = 60,
    ):
        """Initialize the LLM filter.

        Args:
            base_url: Ollama API base URL
            model: Model name to use for filtering
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.preferences = ""

    def load_preferences(self, preferences_file: str) -> None:
        """Load user preferences from markdown file.

        Args:
            preferences_file: Path to preferences markdown file

        Raises:
            FileNotFoundError: If preferences file doesn't exist
        """
        prefs_path = Path(preferences_file)
        if not prefs_path.exists():
            raise FileNotFoundError(f"Preferences file not found: {preferences_file}")

        self.preferences = prefs_path.read_text(encoding="utf-8")
        logger.info(f"Loaded preferences from {preferences_file} ({len(self.preferences)} chars)")

    def analyze_article(
        self, article: Dict[str, str], preferences: Optional[str] = None
    ) -> Tuple[int, str]:
        """Analyze article relevance using LLM.

        Args:
            article: Dictionary with keys: title, url, content, category (optional)
            preferences: User preferences (uses loaded preferences if not provided)

        Returns:
            Tuple of (relevance_score, reasoning)
            - relevance_score: Integer from 1-10
            - reasoning: String explanation of the score
        """
        prefs = preferences or self.preferences
        if not prefs:
            logger.warning("No preferences loaded, using empty preferences")

        # Construct prompt
        prompt = self._construct_prompt(article, prefs)

        try:
            logger.debug(f"Analyzing article: {article.get('title', 'Unknown')[:50]}...")

            # Call Ollama API
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.3},  # Consistent scoring
            )

            # Parse response
            score, reason = self._parse_response(response["response"])

            logger.info(f"Article scored {score}/10: {article.get('title', 'Unknown')[:50]}...")
            return score, reason

        except Exception as e:
            logger.error(f"Failed to analyze article with LLM: {e}")
            # Return low score on error
            return 1, f"Error analyzing article: {str(e)}"

    def _construct_prompt(self, article: Dict[str, str], preferences: str) -> str:
        """Construct prompt for LLM analysis.

        Args:
            article: Article data
            preferences: User preferences

        Returns:
            Formatted prompt string
        """
        title = article.get("title", "Unknown")
        content = article.get("content", article.get("description", ""))
        category = article.get("category", "Unknown")

        # Truncate content if too long (keep within context window)
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        prompt = (
            f"""You are a personal news filter. Based on the user's interests """
            f"""below, determine if this article is relevant.

USER INTERESTS:
{preferences}

ARTICLE:
Title: {title}
Category: {category}
Content: {content}

TASK:
Rate the relevance of this article from 1-10 (10 = highly relevant, 1 = not relevant).
Provide your rating and a brief one-sentence explanation.

FORMAT YOUR RESPONSE EXACTLY AS:
SCORE: [number]
REASON: [brief explanation]
"""
        )
        return prompt

    def _parse_response(self, response: str) -> Tuple[int, str]:
        """Parse LLM response to extract score and reasoning.

        Args:
            response: Raw LLM response text

        Returns:
            Tuple of (score, reason)
        """
        # Look for SCORE: pattern (handles negative numbers)
        score_match = re.search(r"SCORE:\s*(-?\d+)", response, re.IGNORECASE)
        reason_match = re.search(r"REASON:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)

        # Extract score
        if score_match:
            score = int(score_match.group(1))
            # Clamp to 1-10 range
            score = max(1, min(10, score))
        else:
            logger.warning(f"Could not parse score from response: {response[:100]}")
            score = 5  # Default middle score

        # Extract reason
        if reason_match:
            reason = reason_match.group(1).strip()
        else:
            logger.warning("Could not parse reason from response")
            reason = "No reason provided"

        return score, reason

    def test_connection(self) -> bool:
        """Test connection to Ollama API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list models
            ollama.list()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
