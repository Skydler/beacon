"""Unit tests for scraper module."""

from unittest.mock import Mock, patch

import pytest

from src.scraper import NewsScraper

# Mock HTML for testing
MOCK_HTML = """
<html>
<body>
    <nav>Navigation Menu</nav>
    <div class="container">
        <a href="noticias/123-first-article">
            <div class="article-container">
                <h4><a href="noticias/123-first-article">First Article Title</a></h4>
                <span class="volanta">Technology</span>
                <span class="copete">This is a description of the first article.</span>
            </div>
        </a>
        <a href="noticias/456-second-article">
            <div class="article-container">
                <h4><a href="noticias/456-second-article">Second Article Title</a></h4>
                <span class="volanta">Politics</span>
            </div>
        </a>
        <a href="noticias/789-third-article">
            <h5><a href="noticias/789-third-article">Third Article Title</a></h5>
        </a>
    </div>
    <footer>Footer content</footer>
</body>
</html>
"""

MOCK_ARTICLE_HTML = """
<html>
<body>
    <nav>Navigation</nav>
    <article>
        <h1>Article Title</h1>
        <p>This is the first paragraph of the article content.</p>
        <p>This is the second paragraph with more details.</p>
        <p>And here is the conclusion of the article.</p>
    </article>
    <aside>Advertisement</aside>
    <footer>Footer</footer>
</body>
</html>
"""


@pytest.fixture
def scraper():
    """Create a NewsScraper instance for testing."""
    return NewsScraper(user_agent="TestBot/1.0")


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.text = MOCK_HTML
    response.status_code = 200
    response.raise_for_status = Mock()
    return response


def test_scraper_initialization(scraper):
    """Test that scraper initializes correctly."""
    assert scraper.user_agent == "TestBot/1.0"
    assert scraper.session.headers["User-Agent"] == "TestBot/1.0"


@patch("src.scraper.time.sleep")  # Mock sleep to speed up tests
@patch("requests.Session.get")
def test_scrape_news_site(mock_get, mock_sleep, scraper, mock_response):
    """Test scraping articles from a news site."""
    mock_get.return_value = mock_response

    selectors = {
        "article_list": "a[href^='noticias/']",
        "title": "h4 a, h5 a",
        "category": "span.volanta",
        "description": "span.copete",
    }

    articles = scraper.scrape_news_site("https://example.com", selectors)

    assert len(articles) > 0
    assert articles[0]["title"] == "First Article Title"
    assert articles[0]["url"].endswith("noticias/123-first-article")
    assert articles[0].get("category") == "Technology"
    assert "description" in articles[0]


@patch("src.scraper.time.sleep")
@patch("requests.Session.get")
def test_scrape_news_site_with_max_articles(mock_get, mock_sleep, scraper, mock_response):
    """Test that max_articles limit is respected."""
    mock_get.return_value = mock_response

    selectors = {"article_list": "a[href^='noticias/']", "title": "h4 a, h5 a"}

    articles = scraper.scrape_news_site("https://example.com", selectors, max_articles=2)

    assert len(articles) <= 2


@patch("src.scraper.time.sleep")
@patch("requests.Session.get")
def test_scrape_news_site_handles_errors(mock_get, mock_sleep, scraper):
    """Test that scraper handles HTTP errors gracefully."""
    mock_get.side_effect = Exception("Network error")

    selectors = {"article_list": "a"}
    articles = scraper.scrape_news_site("https://example.com", selectors)

    assert articles == []


@patch("src.scraper.time.sleep")
@patch("requests.Session.get")
def test_extract_article_content(mock_get, mock_sleep, scraper):
    """Test extracting full article content."""
    mock_response = Mock()
    mock_response.text = MOCK_ARTICLE_HTML
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    content = scraper.extract_article_content("https://example.com/article")

    assert content is not None
    assert "first paragraph" in content
    assert "second paragraph" in content
    assert "conclusion" in content
    # Check that nav and footer were removed
    assert "Navigation" not in content
    assert "Advertisement" not in content


@patch("src.scraper.time.sleep")
@patch("requests.Session.get")
def test_extract_article_content_returns_none_on_error(mock_get, mock_sleep, scraper):
    """Test that content extraction returns None on error."""
    mock_get.side_effect = Exception("Network error")

    content = scraper.extract_article_content("https://example.com/article")

    assert content is None


def test_parse_articles_removes_duplicates(scraper):
    """Test that duplicate URLs are filtered out."""
    html_with_duplicates = """
    <html>
    <body>
        <a href="noticias/123-article">Article 1</a>
        <a href="noticias/123-article">Article 1 Again</a>
        <a href="noticias/456-article">Article 2</a>
    </body>
    </html>
    """

    selectors = {"article_list": "a[href^='noticias/']"}
    articles = scraper._parse_articles(html_with_duplicates, "https://example.com", selectors)

    # Should only have 2 unique articles
    assert len(articles) == 2
    urls = [a["url"] for a in articles]
    assert len(set(urls)) == 2


def test_is_valid_url(scraper):
    """Test URL validation."""
    assert scraper.is_valid_url("https://example.com/article") is True
    assert scraper.is_valid_url("http://example.com") is True
    assert scraper.is_valid_url("invalid-url") is False
    assert scraper.is_valid_url("") is False


def test_extract_article_data_handles_relative_urls(scraper):
    """Test that relative URLs are converted to absolute."""
    from bs4 import BeautifulSoup

    html = '<a href="/noticias/123">Test Article</a>'
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("a")

    selectors = {}
    article = scraper._extract_article_data(element, "https://example.com", selectors)

    assert article is not None
    assert article["url"] == "https://example.com/noticias/123"


def test_extract_article_data_returns_none_for_invalid(scraper):
    """Test that invalid elements return None."""
    from bs4 import BeautifulSoup

    html = "<div>No link here</div>"
    soup = BeautifulSoup(html, "lxml")
    element = soup.find("div")

    selectors = {}
    article = scraper._extract_article_data(element, "https://example.com", selectors)

    assert article is None


@patch("src.scraper.time.sleep")
def test_fetch_html_implements_rate_limiting(mock_sleep, scraper):
    """Test that rate limiting is implemented."""
    with patch("requests.Session.get") as mock_get:
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper._fetch_html("https://example.com")

        # Verify sleep was called (rate limiting)
        mock_sleep.assert_called_once_with(1)
