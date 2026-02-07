"""LLM-based article filtering using GitHub Models API."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMFilter:
    """Filter articles using GitHub Models API (OpenAI-compatible)."""

    def __init__(
        self,
        api_token: str,
        model: str,
        timeout: int = 60,
        batch_size: int = 5,
    ):
        """Initialize the LLM filter.

        Args:
            api_token: GitHub Personal Access Token with models:read permission
            model: Model name to use (e.g., "openai/gpt-4o-mini")
            timeout: Request timeout in seconds
            batch_size: Number of articles to analyze per LLM call (1-10)
        """
        self.model = model
        self.timeout = timeout
        self.batch_size = max(1, min(10, batch_size))
        self.preferences = ""

        # Initialize OpenAI client pointed at GitHub Models endpoint
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
        """Analyze a single article's relevance using LLM.

        Convenience wrapper around analyze_articles_batch for single articles.

        Args:
            article: Dictionary with keys: title, url, content, category (optional)
            preferences: User preferences (uses loaded preferences if not provided)

        Returns:
            Tuple of (relevance_score, reasoning)
        """
        results = self.analyze_articles_batch([article], preferences)
        return results[0]

    def analyze_articles_batch(
        self,
        articles: List[Dict[str, str]],
        preferences: Optional[str] = None,
    ) -> List[Tuple[int, str]]:
        """Analyze a batch of articles' relevance in a single LLM call.

        Args:
            articles: List of article dictionaries with keys: title, url, content, category
            preferences: User preferences (uses loaded preferences if not provided)

        Returns:
            List of (relevance_score, reasoning) tuples, one per article
        """
        if not articles:
            return []

        prefs = preferences or self.preferences
        if not prefs:
            logger.warning("No preferences loaded, using empty preferences")

        # Single article: use the simpler single-article prompt for best accuracy
        if len(articles) == 1:
            return [self._analyze_single(articles[0], prefs)]

        # Multiple articles: use batch prompt
        prompt = self._construct_batch_prompt(articles, prefs)

        try:
            titles_preview = ", ".join(a.get("title", "Unknown")[:30] for a in articles[:3])
            logger.debug(f"Batch analyzing {len(articles)} articles: {titles_preview}...")

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
                temperature=0.3,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content or ""
            results = self._parse_batch_response(content, len(articles))

            for i, (score, _reason) in enumerate(results):
                title = articles[i].get("title", "Unknown")[:50]
                logger.info(f"Article scored {score}/10: {title}...")

            return results

        except Exception as e:
            logger.error(f"Batch LLM call failed: {e}")
            logger.info("Falling back to individual article analysis for this batch")
            # Fallback: analyze each article individually
            return [self._analyze_single(article, prefs) for article in articles]

    def _analyze_single(self, article: Dict[str, str], preferences: str) -> Tuple[int, str]:
        """Analyze a single article with its own LLM call.

        Args:
            article: Article data
            preferences: User preferences

        Returns:
            Tuple of (score, reason)
        """
        prompt = self._construct_single_prompt(article, preferences)

        try:
            logger.debug(f"Analyzing article: {article.get('title', 'Unknown')[:50]}...")

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
                temperature=0.3,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content or ""
            score, reason = self._parse_single_response(content)
            logger.info(f"Article scored {score}/10: {article.get('title', 'Unknown')[:50]}...")
            return score, reason

        except Exception as e:
            logger.error(f"Failed to analyze article with LLM: {e}")
            return 1, f"Error analyzing article: {str(e)}"

    # ── Prompt construction ───────────────────────────────────────────

    def _construct_single_prompt(self, article: Dict[str, str], preferences: str) -> str:
        """Construct prompt for single-article LLM analysis.

        Args:
            article: Article data
            preferences: User preferences

        Returns:
            Formatted prompt string
        """
        title = article.get("title", "Unknown")
        content = article.get("content", article.get("description", ""))
        category = article.get("category", "Unknown")

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

    def _construct_batch_prompt(self, articles: List[Dict[str, str]], preferences: str) -> str:
        """Construct prompt for batch article analysis.

        Args:
            articles: List of article dictionaries
            preferences: User preferences

        Returns:
            Formatted prompt string
        """
        # Build numbered article entries
        article_entries = []
        max_content_length = 4000
        for i, article in enumerate(articles):
            title = article.get("title", "Unknown")
            content = article.get("content", article.get("description", ""))
            category = article.get("category", "Unknown")

            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."

            article_entries.append(
                f"--- ARTICLE {i} ---\nTitle: {title}\nCategory: {category}\nContent: {content}"
            )

        articles_block = "\n\n".join(article_entries)
        num_articles = len(articles)

        prompt = f"""You are a news filter. Analyze if each of the following {num_articles} articles matches the user's interests.

USER INTERESTS:
{preferences}

{articles_block}

CRITICAL RULES:
1. Check if each article directly matches ANY of the user's HIGH or MEDIUM priority topics
2. Restaurant openings, food festivals, and culinary events ARE relevant (Food & Culinary section)
3. Technology, health alerts, price changes, and weather emergencies are also relevant
4. Check if each article is in the "Topics to Ignore" list - if so, score 1-2
5. When in doubt about relevance, score conservatively but fairly

ANALYSIS PROCESS (apply to EACH article independently):
1. First, check if the article matches a HIGH priority topic (score 8-10)
2. Then check if it matches a MEDIUM priority topic (score 6-7)
3. If it's in "Topics to Ignore", score 1-2
4. Otherwise score based on relevance and local impact

Respond with ONLY valid JSON in this exact format (an object with a "results" array containing exactly {num_articles} entries, one per article in order):
{{
  "results": [
    {{"article_index": 0, "score": <number from 1-10>, "reason": "<brief explanation>"}},
    {{"article_index": 1, "score": <number from 1-10>, "reason": "<brief explanation>"}},
    ...
  ]
}}

IMPORTANT: You MUST return exactly {num_articles} results, one for each article, in order from article 0 to article {num_articles - 1}.
"""
        return prompt

    # Keep backward-compatible alias
    def _construct_prompt(self, article: Dict[str, str], preferences: str) -> str:
        """Backward-compatible alias for _construct_single_prompt."""
        return self._construct_single_prompt(article, preferences)

    # ── Response parsing ──────────────────────────────────────────────

    def _parse_single_response(self, response: str) -> Tuple[int, str]:
        """Parse single-article LLM JSON response.

        Args:
            response: JSON response from LLM

        Returns:
            Tuple of (score, reason)
        """
        try:
            data = json.loads(response)

            score = data.get("score")
            if score is None:
                logger.warning(f"No 'score' field in JSON response: {response[:200]}")
                score = 1
            else:
                score = int(score)
                score = max(1, min(10, score))

            reason = data.get("reason", "No reason provided")
            if not reason or not isinstance(reason, str):
                reason = "No reason provided"

            return score, reason

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return 1, f"JSON parse error: {str(e)}"
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid score value in response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return 1, f"Invalid response format: {str(e)}"

    # Keep backward-compatible alias
    def _parse_json_response(self, response: str) -> Tuple[int, str]:
        """Backward-compatible alias for _parse_single_response."""
        return self._parse_single_response(response)

    def _parse_batch_response(self, response: str, expected_count: int) -> List[Tuple[int, str]]:
        """Parse batch LLM JSON response.

        Args:
            response: JSON response string from LLM
            expected_count: Number of articles we expect results for

        Returns:
            List of (score, reason) tuples
        """
        default_results = [(1, "Failed to parse batch response")] * expected_count

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse batch JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return default_results

        # Extract the results array
        results_list = data.get("results")
        if not isinstance(results_list, list):
            logger.error(f"Expected 'results' array in response, got: {type(results_list)}")
            return default_results

        # Build results indexed by article_index for resilience against ordering issues
        indexed_results: Dict[int, Tuple[int, str]] = {}
        for item in results_list:
            if not isinstance(item, dict):
                continue

            idx = item.get("article_index")
            if idx is None:
                continue

            try:
                idx = int(idx)
            except (ValueError, TypeError):
                continue

            score = item.get("score")
            if score is None:
                score = 1
            else:
                try:
                    score = int(score)
                    score = max(1, min(10, score))
                except (ValueError, TypeError):
                    score = 1

            reason = item.get("reason", "No reason provided")
            if not reason or not isinstance(reason, str):
                reason = "No reason provided"

            indexed_results[idx] = (score, reason)

        # Assemble final list in order, filling gaps with defaults
        final_results = []
        for i in range(expected_count):
            if i in indexed_results:
                final_results.append(indexed_results[i])
            else:
                logger.warning(f"Missing result for article index {i} in batch response")
                final_results.append((1, "Missing from batch response"))

        return final_results

    def test_connection(self) -> bool:
        """Test connection to GitHub Models API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
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
