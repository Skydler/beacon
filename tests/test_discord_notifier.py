"""Unit tests for Discord notifier module."""

from unittest.mock import Mock, patch

import pytest

from src.discord_notifier import DiscordNotifier


@pytest.fixture
def notifier():
    """Create a Discord notifier instance for testing."""
    return DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/test")


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return {
        "title": "Breaking: New Technology Advancement",
        "url": "https://example.com/article",
        "category": "Technology",
        "description": "A significant breakthrough in quantum computing has been announced.",
    }


def test_notifier_initialization(notifier):
    """Test that notifier initializes correctly."""
    assert notifier.webhook_url == "https://discord.com/api/webhooks/123/test"
    assert notifier.timeout == 30


@patch("requests.post")
def test_send_article_success(mock_post, notifier, sample_article):
    """Test sending article notification successfully."""
    mock_response = Mock()
    mock_response.status_code = 204
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    result = notifier.send_article(sample_article, relevance_score=8, reason="Relevant")

    assert result is True
    mock_post.assert_called_once()
    # Verify payload structure
    call_args = mock_post.call_args
    assert "embeds" in call_args.kwargs["json"]


@patch("requests.post")
def test_send_article_creates_proper_embed(mock_post, notifier, sample_article):
    """Test that article embed is created correctly."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    notifier.send_article(sample_article, relevance_score=9, reason="Very relevant")

    call_args = mock_post.call_args
    payload = call_args.kwargs["json"]
    embed = payload["embeds"][0]

    assert embed["title"] == sample_article["title"]
    assert embed["url"] == sample_article["url"]
    assert embed["description"] == sample_article["description"]
    # Check fields
    field_names = [f["name"] for f in embed["fields"]]
    assert "Category" in field_names
    assert "Relevance Score" in field_names
    assert "Why this article?" in field_names


@patch("requests.post")
def test_send_article_color_based_on_score(mock_post, notifier, sample_article):
    """Test that embed color changes based on relevance score."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    # High score (8+) should be green
    notifier.send_article(sample_article, relevance_score=9, reason="test")
    embed_high = mock_post.call_args.kwargs["json"]["embeds"][0]
    assert embed_high["color"] == 0x57F287  # Green

    # Medium score (6-7) should be yellow
    notifier.send_article(sample_article, relevance_score=6, reason="test")
    embed_med = mock_post.call_args.kwargs["json"]["embeds"][0]
    assert embed_med["color"] == 0xFEE75C  # Yellow

    # Low score (<6) should be red
    notifier.send_article(sample_article, relevance_score=5, reason="test")
    embed_low = mock_post.call_args.kwargs["json"]["embeds"][0]
    assert embed_low["color"] == 0xED4245  # Red


@patch("requests.post")
def test_send_article_truncates_long_description(mock_post, notifier):
    """Test that long descriptions are truncated."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    long_article = {
        "title": "Test",
        "url": "https://example.com",
        "category": "Test",
        "description": "x" * 500,  # Very long description
    }

    notifier.send_article(long_article, relevance_score=7, reason="test")

    embed = mock_post.call_args.kwargs["json"]["embeds"][0]
    assert len(embed["description"]) <= 303  # 300 + "..."
    assert embed["description"].endswith("...")


@patch("requests.post")
def test_send_article_handles_missing_fields(mock_post, notifier):
    """Test handling of articles with missing fields."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    minimal_article = {
        "url": "https://example.com",
    }

    result = notifier.send_article(minimal_article, relevance_score=5, reason="test")

    assert result is True
    embed = mock_post.call_args.kwargs["json"]["embeds"][0]
    assert embed["title"] == "Unknown Title"
    assert embed["description"] == ""


@patch("requests.post")
def test_send_article_handles_request_error(mock_post, notifier, sample_article):
    """Test handling of network errors."""
    mock_post.side_effect = Exception("Network error")

    result = notifier.send_article(sample_article, relevance_score=8, reason="test")

    assert result is False


@patch("requests.post")
def test_send_summary_success(mock_post, notifier):
    """Test sending summary notification."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    result = notifier.send_summary(
        total_articles=20,
        new_articles=5,
        sent_notifications=3,
    )

    assert result is True
    mock_post.assert_called_once()

    # Verify payload structure
    payload = mock_post.call_args.kwargs["json"]
    embed = payload["embeds"][0]
    assert embed["title"] == "📰 Beacon Run Summary"
    assert len(embed["fields"]) == 3


@patch("requests.post")
def test_send_summary_includes_correct_data(mock_post, notifier):
    """Test that summary includes all data."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    notifier.send_summary(
        total_articles=100,
        new_articles=10,
        sent_notifications=5,
    )

    embed = mock_post.call_args.kwargs["json"]["embeds"][0]
    fields = {f["name"]: f["value"] for f in embed["fields"]}

    assert fields["Articles Scraped"] == "100"
    assert fields["New Articles"] == "10"
    assert fields["Notifications Sent"] == "5"


@patch("requests.post")
def test_send_summary_handles_errors(mock_post, notifier):
    """Test that summary errors are handled gracefully."""
    mock_post.side_effect = Exception("Network error")

    result = notifier.send_summary(10, 5, 2)

    assert result is False


@patch("requests.post")
def test_test_connection_success(mock_post, notifier):
    """Test successful connection test."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    result = notifier.test_connection()

    assert result is True
    mock_post.assert_called_once()

    # Verify test message
    payload = mock_post.call_args.kwargs["json"]
    assert "content" in payload
    assert "test" in payload["content"].lower()


@patch("src.discord_notifier.requests.post")
def test_test_connection_failure(mock_post, notifier):
    """Test failed connection test."""
    mock_post.side_effect = Exception("Connection refused")

    result = notifier.test_connection()

    assert result is False


def test_create_embed(notifier, sample_article):
    """Test embed creation."""
    embed = notifier._create_embed(sample_article, relevance_score=8, reason="Relevant")

    assert embed["title"] == sample_article["title"]
    assert embed["url"] == sample_article["url"]
    assert embed["description"] == sample_article["description"]
    assert embed["color"] == 0x57F287  # Green for score 8
    assert len(embed["fields"]) == 3


def test_create_embed_with_no_description(notifier):
    """Test embed creation with missing description."""
    article = {
        "title": "Test",
        "url": "https://example.com",
        "category": "Tech",
    }

    embed = notifier._create_embed(article, relevance_score=5, reason="test")

    assert embed["description"] == ""
    assert embed["title"] == "Test"
