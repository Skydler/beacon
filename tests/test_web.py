"""Smoke tests for the Beacon web dashboard."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MOCK_SOURCES = [
    {
        "name": "La Nacion",
        "url": "https://www.lanacion.com.ar",
        "selectors": {},
    },
    {
        "name": "Info Quilmes",
        "url": "https://www.infoquilmes.com.ar/",
        "selectors": {},
    },
]

MOCK_ARTICLES = [
    {
        "url": "https://www.lanacion.com.ar/article1",
        "title": "Relevant Article",
        "scraped_at": datetime(2026, 2, 20, 10, 0, 0),
        "relevance_score": 8,
        "notified": True,
        "reason": "Matches local news interest",
        "source_name": "La Nacion",
    },
    {
        "url": "https://www.lanacion.com.ar/article2",
        "title": "Filtered Article",
        "scraped_at": datetime(2026, 2, 20, 9, 0, 0),
        "relevance_score": 3,
        "notified": True,
        "reason": "Too general",
        "source_name": "La Nacion",
    },
    {
        "url": "https://www.infoquilmes.com.ar/article3",
        "title": "Quilmes Article",
        "scraped_at": datetime(2026, 2, 19, 15, 0, 0),
        "relevance_score": None,
        "notified": False,
        "reason": None,
        "source_name": "Info Quilmes",
    },
]


@pytest.fixture()
def client():
    """TestClient with Config and Database patched to avoid filesystem access."""
    mock_cfg = MagicMock()
    mock_cfg.get_news_sources.return_value = MOCK_SOURCES
    mock_cfg.get_min_relevance_score.return_value = 7
    mock_cfg.get_database_path.return_value = ":memory:"

    mock_db = MagicMock()
    mock_db.get_recent_articles.return_value = MOCK_ARTICLES

    with (
        patch("src.web._cfg", mock_cfg),
        patch("src.web._db", mock_db),
    ):
        from src.web import app

        yield TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_index_returns_200(client):
    """GET / should return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_index_is_html(client):
    """Response should be HTML."""
    response = client.get("/")
    assert "text/html" in response.headers["content-type"]


def test_index_contains_source_names(client):
    """Page should display each configured source name."""
    response = client.get("/")
    assert "La Nacion" in response.text
    assert "Info Quilmes" in response.text


def test_index_contains_article_titles(client):
    """Page should display article titles."""
    response = client.get("/")
    assert "Relevant Article" in response.text
    assert "Filtered Article" in response.text
    assert "Quilmes Article" in response.text


def test_index_shows_accepted_badge(client):
    """Articles above threshold should show Accepted badge."""
    response = client.get("/")
    assert "Accepted" in response.text


def test_index_shows_rejected_badge(client):
    """Articles below threshold should show Rejected badge."""
    response = client.get("/")
    assert "Rejected" in response.text


def test_index_shows_pending_badge(client):
    """Articles without a score should show Pending badge."""
    response = client.get("/")
    assert "Pending" in response.text


def test_index_shows_reasons(client):
    """LLM reasons should appear in the page."""
    response = client.get("/")
    assert "Matches local news interest" in response.text
    assert "Too general" in response.text
