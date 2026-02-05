"""Web scraper module for extracting news articles."""

import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsScraper:
    """Scraper for extracting articles from news websites."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (compatible; BeaconBot/1.0)"):
        """Initialize the news scraper.

        Args:
            user_agent: User-Agent string for HTTP requests
        """
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def scrape_news_site(
        self, url: str, selectors: Dict[str, str], max_articles: int = 20
    ) -> List[Dict[str, str]]:
        """Scrape articles from a news website.

        Args:
            url: Base URL of the news site
            selectors: Dictionary of CSS selectors for article elements
            max_articles: Maximum number of articles to extract

        Returns:
            List of article dictionaries with keys: url, title, category, description
        """
        try:
            logger.info(f"Scraping news from {url}")
            html = self._fetch_html(url)
            articles = self._parse_articles(html, url, selectors)

            # Limit number of articles
            articles = articles[:max_articles]

            logger.info(f"Found {len(articles)} articles from {url}")
            return articles

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return []

    def extract_article_content(self, article_url: str) -> Optional[str]:
        """Extract full text content from an article page.

        Args:
            article_url: URL of the article to fetch

        Returns:
            Article text content, or None if extraction fails
        """
        try:
            logger.debug(f"Fetching article content from {article_url}")
            html = self._fetch_html(article_url)
            soup = BeautifulSoup(html, "lxml")

            # Remove unwanted elements
            for element in soup.find_all(["script", "style", "nav", "footer", "aside"]):
                element.decompose()

            # Try to find main content area
            # Common patterns: article, main, div.content, div.article-body
            content = None
            for selector in ["article", "main", "[role='main']", "div.content"]:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator="\n", strip=True)
                    break

            # Fallback: get all text from body
            if not content or len(content) < 100:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)

            if content and len(content) > 50:
                logger.debug(f"Extracted {len(content)} characters from {article_url}")
                return content

            logger.warning(f"Could not extract meaningful content from {article_url}")
            return None

        except Exception as e:
            logger.error(f"Failed to extract content from {article_url}: {e}")
            return None

    def _fetch_html(self, url: str, timeout: int = 30) -> str:
        """Fetch HTML content from a URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content as string

        Raises:
            requests.RequestException: If request fails
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            # Rate limiting: be respectful
            time.sleep(1)

            return response.text

        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            raise

    def _parse_articles(
        self, html: str, base_url: str, selectors: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Parse HTML to extract article information.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links
            selectors: CSS selectors for article elements

        Returns:
            List of article dictionaries
        """
        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # Find all article links
        article_selector = selectors.get("article_list", "a")
        article_elements = soup.select(article_selector)

        logger.debug(f"Found {len(article_elements)} potential articles")

        for element in article_elements:
            try:
                article = self._extract_article_data(element, base_url, selectors)

                # Skip if we couldn't extract a valid article
                if not article or not article.get("url"):
                    continue

                # Skip duplicates
                if article["url"] in seen_urls:
                    continue

                seen_urls.add(article["url"])
                articles.append(article)

            except Exception as e:
                logger.warning(f"Failed to parse article element: {e}")
                continue

        return articles

    def _extract_article_data(
        self, element, base_url: str, selectors: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """Extract data from a single article element.

        Args:
            element: BeautifulSoup element containing article info
            base_url: Base URL for resolving relative links
            selectors: CSS selectors for article parts

        Returns:
            Article dictionary or None if extraction fails
        """
        article = {}

        # Extract URL
        if element.name == "a":
            href = element.get("href")
        else:
            link = element.find("a")
            href = link.get("href") if link else None

        if not href:
            return None

        # Resolve relative URLs
        article["url"] = urljoin(base_url, href)

        # Extract title with multiple fallback strategies
        title = None
        title_selector = selectors.get("title")

        if title_selector:
            # Strategy 1: Look for title in nested elements (H4, H5, H6, div.titulo)
            title_elem = element.select_one(title_selector)
            if title_elem:
                title = title_elem.get_text(strip=True)

        # Strategy 2: Fallback to img alt attribute (common for image-based articles)
        if not title:
            img = element.select_one("img")
            if img and img.get("alt"):
                title = img.get("alt").strip()

        # Strategy 3: Fallback to anchor title attribute
        if not title and element.name == "a":
            title = element.get("title", "").strip()

        # Strategy 4: Use link text
        if not title:
            title = element.get_text(strip=True)

        article["title"] = title if title else "Untitled"

        # Extract category (optional)
        category_selector = selectors.get("category")
        if category_selector:
            parent = element.parent.parent if element.parent else element
            category_elem = parent.select_one(category_selector)
            if category_elem:
                article["category"] = category_elem.get_text(strip=True)

        # Extract description (optional)
        desc_selector = selectors.get("description")
        if desc_selector:
            parent = element.parent.parent.parent if element.parent else element
            desc_elem = parent.select_one(desc_selector)
            if desc_elem:
                article["description"] = desc_elem.get_text(strip=True)

        return article

    def is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and complete.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
