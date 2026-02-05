"""Discord webhook notification module."""

import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Send notifications to Discord via webhooks."""

    def __init__(self, webhook_url: str, timeout: int = 30):
        """Initialize the Discord notifier.

        Args:
            webhook_url: Discord webhook URL
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_article(
        self,
        article: Dict[str, str],
        relevance_score: int,
        reason: str,
    ) -> bool:
        """Send article notification to Discord.

        Args:
            article: Article dictionary with title, url, category, etc.
            relevance_score: Relevance score (1-10)
            reason: Reasoning for the score

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            embed = self._create_embed(article, relevance_score, reason)
            payload = {"embeds": [embed]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Sent notification for article: {article.get('title', 'Unknown')[:50]}...")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord notification: {e}")
            return False

    def send_summary(
        self,
        total_articles: int,
        new_articles: int,
        sent_notifications: int,
    ) -> bool:
        """Send summary notification to Discord.

        Args:
            total_articles: Total articles scraped
            new_articles: Number of new articles
            sent_notifications: Number of notifications sent

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            embed = {
                "title": "📰 Beacon Run Summary",
                "color": 0x5865F2,  # Discord blurple
                "fields": [
                    {
                        "name": "Articles Scraped",
                        "value": str(total_articles),
                        "inline": True,
                    },
                    {
                        "name": "New Articles",
                        "value": str(new_articles),
                        "inline": True,
                    },
                    {
                        "name": "Notifications Sent",
                        "value": str(sent_notifications),
                        "inline": True,
                    },
                ],
            }

            payload = {"embeds": [embed]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info("Sent summary notification")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord summary: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord summary: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to Discord webhook.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Send a simple test message
            payload = {
                "content": "✅ Beacon Discord connection test successful",
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info("Discord webhook connection test successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord webhook connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Discord connection: {e}")
            return False

    def _create_embed(
        self,
        article: Dict[str, str],
        relevance_score: int,
        reason: str,
    ) -> Dict:
        """Create Discord embed for article.

        Args:
            article: Article data
            relevance_score: Relevance score (1-10)
            reason: Reasoning for the score

        Returns:
            Discord embed dictionary
        """
        title = article.get("title", "Unknown Title")
        url = article.get("url", "")
        category = article.get("category", "Unknown")
        description = article.get("description", "")

        # Truncate description if too long
        max_desc_length = 300
        if description and len(description) > max_desc_length:
            description = description[:max_desc_length] + "..."

        # Choose color based on relevance score
        if relevance_score >= 8:
            color = 0x57F287  # Green
        elif relevance_score >= 6:
            color = 0xFEE75C  # Yellow
        else:
            color = 0xED4245  # Red

        embed = {
            "title": title,
            "url": url,
            "description": description,
            "color": color,
            "fields": [
                {
                    "name": "Category",
                    "value": category,
                    "inline": True,
                },
                {
                    "name": "Relevance Score",
                    "value": f"{relevance_score}/10",
                    "inline": True,
                },
                {
                    "name": "Why this article?",
                    "value": reason,
                    "inline": False,
                },
            ],
        }

        return embed
