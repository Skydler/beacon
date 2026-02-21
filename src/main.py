"""Main orchestration script for Beacon news aggregator."""

import argparse
import logging
import sys

from src.config import Config
from src.database import Database
from src.discord_notifier import DiscordNotifier
from src.llm_filter import LLMFilter
from src.scraper import NewsScraper

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class BeaconApp:
    """Main application orchestrator for Beacon."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Beacon application.

        Args:
            config_path: Path to configuration file
        """
        logger.info("Initializing Beacon...")

        # Load configuration
        self.config = Config(config_path)

        # Initialize components
        self.db = Database(self.config.get_database_path())

        github_models_config = self.config.get_github_models_config()
        self.llm_filter = LLMFilter(
            api_token=github_models_config["api_token"],
            model=github_models_config["model"],
            timeout=github_models_config["timeout"],
            batch_size=github_models_config.get("batch_size", 5),
        )

        self.scraper = NewsScraper()

        self.discord = DiscordNotifier(self.config.get_discord_webhook())

        # Load preferences
        prefs_file = self.config.get_preferences_file()
        self.llm_filter.load_preferences(prefs_file)

        self.min_relevance_score = self.config.get_min_relevance_score()

        logger.info("Beacon initialized successfully")

    def run(self, dry_run: bool = False) -> None:
        """Run the main aggregation pipeline.

        Args:
            dry_run: If True, don't send notifications
        """
        logger.info("Starting Beacon run...")

        total_articles = 0
        new_articles = 0
        sent_notifications = 0

        # Get news sources
        news_sources = self.config.get_news_sources()
        logger.info(f"Processing {len(news_sources)} news sources")

        for source in news_sources:
            logger.info(f"Scraping {source['name']}...")

            try:
                # Scrape articles
                articles = self.scraper.scrape_news_site(
                    url=source["url"],
                    selectors=source["selectors"],
                    max_articles=self.config.get_max_articles_per_source(),
                )

                total_articles += len(articles)
                logger.info(f"Found {len(articles)} articles from {source['name']}")

                # Filter out already-seen articles
                unseen_articles = []
                for article in articles:
                    if self.db.is_article_seen(article["url"]):
                        logger.info(f"Skipping seen article: {article['title'][:50]}...")
                    else:
                        unseen_articles.append(article)

                new_articles += len(unseen_articles)

                if not unseen_articles:
                    logger.info(f"No new articles from {source['name']}")
                    continue

                # Analyze articles in batches
                batch_size = self.llm_filter.batch_size
                for batch_start in range(0, len(unseen_articles), batch_size):
                    batch = unseen_articles[batch_start : batch_start + batch_size]
                    logger.info(
                        f"Analyzing batch of {len(batch)} articles "
                        f"({batch_start + 1}-{batch_start + len(batch)} "
                        f"of {len(unseen_articles)})"
                    )

                    results = self.llm_filter.analyze_articles_batch(batch)

                    for article, (score, reason) in zip(batch, results):
                        # Mark as seen in database
                        self.db.mark_article_seen(
                            url=article["url"],
                            title=article["title"],
                            relevance_score=score,
                        )

                        # Send notification if relevant
                        if score >= self.min_relevance_score:
                            logger.info(
                                f"Relevant article (score {score}): {article['title'][:50]}..."
                            )

                            if not dry_run:
                                success = self.discord.send_article(article, score, reason)
                                if success:
                                    sent_notifications += 1
                            else:
                                logger.info("[DRY RUN] Would send notification")
                                sent_notifications += 1
                        else:
                            logger.debug(
                                f"Filtered out (score {score}): {article['title'][:50]}..."
                            )

            except Exception as e:
                logger.error(f"Error processing source {source['name']}: {e}")
                continue

        # Send summary
        logger.info(
            f"Run complete: {total_articles} total, {new_articles} new, "
            f"{sent_notifications} notifications"
        )

        # Only send summary if there were notifications
        if sent_notifications > 0:
            if not dry_run:
                self.discord.send_summary(total_articles, new_articles, sent_notifications)
            else:
                logger.info("[DRY RUN] Would send summary")
        else:
            logger.info("No relevant articles found - skipping summary notification")

    def test_scraper(self) -> bool:
        """Test scraper with first news source.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing scraper...")

        try:
            sources = self.config.get_news_sources()
            if not sources:
                logger.error("No news sources configured")
                return False

            source = sources[0]
            logger.info(f"Testing with {source['name']}...")

            articles = self.scraper.scrape_news_site(
                url=source["url"],
                selectors=source["selectors"],
                max_articles=50,
            )

            logger.info(f"✅ Successfully scraped {len(articles)} articles")
            for i, article in enumerate(articles, 1):
                logger.info(f"  {i}. {article['title']}")

            return True

        except Exception as e:
            logger.error(f"❌ Scraper test failed: {e}")
            return False

    def test_llm(self) -> bool:
        """Test LLM filter connection and analysis.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing LLM filter...")

        try:
            # Test connection
            if not self.llm_filter.test_connection():
                logger.error("❌ Failed to connect to GitHub Models API")
                return False

            logger.info("✅ Connected to GitHub Models API")

            # Test analysis
            test_article = {
                "title": "Test Article About Technology",
                "content": "This is a test article about new technology developments.",
                "category": "Technology",
                "url": "https://example.com/test",
            }

            score, reason = self.llm_filter.analyze_article(test_article)
            logger.info(f"✅ LLM analysis successful: score={score}, reason={reason}")

            return True

        except Exception as e:
            logger.error(f"❌ LLM test failed: {e}")
            return False

    def test_discord(self) -> bool:
        """Test Discord webhook connection.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing Discord webhook...")

        try:
            if not self.discord.test_connection():
                logger.error("❌ Failed to connect to Discord webhook")
                return False

            logger.info("✅ Discord webhook test successful")
            return True

        except Exception as e:
            logger.error(f"❌ Discord test failed: {e}")
            return False


def main() -> None:
    """Main entry point for Beacon."""
    parser = argparse.ArgumentParser(description="Beacon - AI-powered news aggregator")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending notifications",
    )
    parser.add_argument(
        "--test-scraper",
        action="store_true",
        help="Test scraper only",
    )
    parser.add_argument(
        "--test-llm",
        action="store_true",
        help="Test LLM filter only",
    )
    parser.add_argument(
        "--test-discord",
        action="store_true",
        help="Test Discord webhook only",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize app
        app = BeaconApp(config_path=args.config)

        # Run tests if requested
        if args.test_scraper:
            success = app.test_scraper()
            sys.exit(0 if success else 1)

        if args.test_llm:
            success = app.test_llm()
            sys.exit(0 if success else 1)

        if args.test_discord:
            success = app.test_discord()
            sys.exit(0 if success else 1)

        # Run main pipeline
        app.run(dry_run=args.dry_run)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
