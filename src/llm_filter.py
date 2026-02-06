"""LLM-based article filtering using GitHub Models API."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMFilter:
    """Filter articles using GitHub Models API (OpenAI-compatible)."""

    def __init__(
        self,
        api_token: str,
        model: str,
        timeout: int = 60,
    ):
        """Initialize the LLM filter.

        Args:
            api_token: GitHub Personal Access Token with models:read permission
            model: Model name to use (e.g., "openai/gpt-4o-mini")
            timeout: Request timeout in seconds
        """
        self.model = model
        self.timeout = timeout
        self.preferences = ""

        # Initialize OpenAI client pointed at GitHub Models endpoint
        # Note: OpenAI client will append /chat/completions automatically
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_token,
        )

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

            # Call GitHub Models API using OpenAI client
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict news filter that outputs JSON responses.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Consistent scoring
                timeout=self.timeout,
            )

            # Parse JSON response
            score, reason = self._parse_json_response(response.choices[0].message.content)

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

        prompt = f"""You are a news filter. Analyze if this article matches the user's interests.

USER INTERESTS:
{preferences}

ARTICLE:
Title: {title}
Category: {category}
Content: {content}

CRITICAL RULES:
1. Check if the article directly matches ANY of the user's HIGH or MEDIUM priority topics
2. Restaurant openings, food festivals, and culinary events ARE relevant (Food & Culinary section)
3. Technology, health alerts, price changes, and weather emergencies are also relevant
4. Check if the article is in the "Topics to Ignore" list - if so, score 1-2
5. When in doubt about relevance, score conservatively but fairly

ANALYSIS PROCESS:
1. First, check if the article matches a HIGH priority topic (score 8-10)
2. Then check if it matches a MEDIUM priority topic (score 6-7)
3. If it's in "Topics to Ignore", score 1-2
4. Otherwise score based on relevance and local impact

Respond with ONLY valid JSON in this exact format:
{{
  "score": <number from 1-10>,
  "reason": "<brief explanation of which topic it matches, or why it doesn't match>"
}}
"""
        return prompt

    def _parse_json_response(self, response: str) -> Tuple[int, str]:
        """Parse LLM JSON response to extract score and reasoning.

        Args:
            response: JSON response from LLM

        Returns:
            Tuple of (score, reason)
        """
        try:
            # Parse JSON response
            data = json.loads(response)

            # Extract score
            score = data.get("score")
            if score is None:
                logger.warning(f"No 'score' field in JSON response: {response[:200]}")
                score = 1  # Default to low score on error
            else:
                # Ensure score is an integer and clamp to 1-10 range
                score = int(score)
                score = max(1, min(10, score))

            # Extract reason
            reason = data.get("reason", "No reason provided")
            if not reason or not isinstance(reason, str):
                reason = "No reason provided"

            return score, reason

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            # Return low score on parse error
            return 1, f"JSON parse error: {str(e)}"
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid score value in response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return 1, f"Invalid response format: {str(e)}"

    def test_connection(self) -> bool:
        """Test connection to GitHub Models API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to make a simple test request
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10,
            )
            logger.info(f"Successfully connected to GitHub Models API (model: {self.model})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to GitHub Models API: {e}")
            return False
