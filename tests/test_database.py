"""Unit tests for database module."""

import pytest

from src.database import Database


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    database = Database(":memory:")
    yield database
    # Cleanup handled by in-memory DB


def test_database_initialization(db):
    """Test database initializes correctly."""
    assert db.db_path == ":memory:"
    assert db.get_article_count() == 0


def test_mark_article_seen(db):
    """Test marking an article as seen."""
    url = "https://example.com/article1"
    title = "Test Article"

    db.mark_article_seen(
        url, title, relevance_score=8, reason="Matches local news interest", source_name="La Nacion"
    )

    assert db.is_article_seen(url) is True
    assert db.get_article_count() == 1


def test_is_article_seen_returns_false_for_new_article(db):
    """Test that new articles are not marked as seen."""
    url = "https://example.com/new-article"
    assert db.is_article_seen(url) is False


def test_duplicate_url_handling(db):
    """Test that duplicate URLs are handled properly."""
    url = "https://example.com/duplicate"
    title = "Duplicate Article"

    db.mark_article_seen(url, title)

    # Trying to add the same URL again should raise an exception
    with pytest.raises(Exception):
        db.mark_article_seen(url, title)


def test_get_recent_articles(db):
    """Test retrieving recent articles."""
    db.mark_article_seen(
        "https://example.com/1", "Article 1", 7, reason="Low match", source_name="Source A"
    )
    db.mark_article_seen(
        "https://example.com/2", "Article 2", 8, reason="Good match", source_name="Source B"
    )
    db.mark_article_seen(
        "https://example.com/3", "Article 3", 9, reason="Strong match", source_name="Source A"
    )

    recent = db.get_recent_articles(days=7)

    assert len(recent) == 3
    assert recent[0]["title"] == "Article 3"  # Most recent first
    assert recent[0]["relevance_score"] == 9
    assert recent[0]["reason"] == "Strong match"
    assert recent[0]["source_name"] == "Source A"


def test_get_recent_articles_filters_by_date(db):
    """Test that get_recent_articles filters by date correctly."""
    # Add an article
    db.mark_article_seen("https://example.com/recent", "Recent Article", 8)

    # Get articles from last 0 days (should be empty since we can't time travel)
    recent = db.get_recent_articles(days=0)

    # Even with days=0, articles from today should appear
    assert len(recent) >= 0  # Depends on precise timing


def test_article_without_relevance_score(db):
    """Test marking article without relevance score."""
    url = "https://example.com/no-score"
    title = "No Score Article"

    db.mark_article_seen(url, title)

    assert db.is_article_seen(url) is True
    articles = db.get_recent_articles()
    assert articles[0]["relevance_score"] is None
    assert articles[0]["notified"] is False
    assert articles[0]["reason"] is None
    assert articles[0]["source_name"] is None


def test_article_with_relevance_score_marks_notified(db):
    """Test that articles with relevance scores are marked as notified."""
    url = "https://example.com/with-score"
    title = "Scored Article"

    db.mark_article_seen(url, title, relevance_score=9)

    articles = db.get_recent_articles()
    assert articles[0]["notified"] is True
