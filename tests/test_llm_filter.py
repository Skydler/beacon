"""Unit tests for LLM filter module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.llm_filter import LLMFilter


@pytest.fixture
def llm_filter():
    """Create an LLMFilter instance for testing."""
    with patch("src.llm_filter.OpenAI"):
        return LLMFilter(api_token="test-token", model="gpt-4o-mini")


@pytest.fixture
def mock_preferences(tmp_path):
    """Create a temporary preferences file."""
    prefs_file = tmp_path / "preferences.md"
    prefs_content = """# My Preferences

I'm interested in:
- Technology news
- Local events
- Science articles

Not interested in:
- Sports
- Celebrity gossip
"""
    prefs_file.write_text(prefs_content)
    return str(prefs_file)


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return {
        "title": "New AI Technology Breakthrough",
        "url": "https://example.com/article",
        "category": "Technology",
        "content": "Scientists have developed a new artificial intelligence system that can...",
    }


@pytest.fixture
def sample_articles():
    """Create multiple sample articles for batch testing."""
    return [
        {
            "title": "New AI Technology Breakthrough",
            "url": "https://example.com/ai",
            "category": "Technology",
            "content": "Scientists have developed a new AI system.",
        },
        {
            "title": "Local Restaurant Grand Opening",
            "url": "https://example.com/restaurant",
            "category": "Food",
            "content": "A new Italian restaurant opens downtown this weekend.",
        },
        {
            "title": "Football Match Results",
            "url": "https://example.com/sports",
            "category": "Sports",
            "content": "The local team won the championship game yesterday.",
        },
    ]


# ── Initialization tests ──────────────────────────────────────────────


def test_llm_filter_initialization(llm_filter):
    """Test that LLM filter initializes correctly."""
    assert llm_filter.model == "gpt-4o-mini"
    assert llm_filter.timeout == 60
    assert llm_filter.batch_size == 5
    assert llm_filter.preferences == ""


def test_llm_filter_batch_size_clamped():
    """Test that batch_size is clamped to 1-10."""
    with patch("src.llm_filter.OpenAI"):
        f = LLMFilter(api_token="test", model="m", batch_size=0)
        assert f.batch_size == 1

        f = LLMFilter(api_token="test", model="m", batch_size=50)
        assert f.batch_size == 10


# ── Preferences tests ─────────────────────────────────────────────────


def test_load_preferences(llm_filter, mock_preferences):
    """Test loading preferences from file."""
    llm_filter.load_preferences(mock_preferences)
    assert len(llm_filter.preferences) > 0
    assert "Technology news" in llm_filter.preferences


def test_load_preferences_file_not_found(llm_filter):
    """Test that loading missing preferences file raises error."""
    with pytest.raises(FileNotFoundError):
        llm_filter.load_preferences("nonexistent.md")


# ── Single-article prompt construction ────────────────────────────────


def test_construct_single_prompt(llm_filter, sample_article):
    """Test single-article prompt construction."""
    preferences = "I like technology"
    prompt = llm_filter._construct_single_prompt(sample_article, preferences)

    assert "I like technology" in prompt
    assert sample_article["title"] in prompt
    assert sample_article["content"] in prompt
    assert '"score"' in prompt
    assert '"reason"' in prompt


def test_construct_single_prompt_truncates_long_content(llm_filter):
    """Test that very long content is truncated."""
    long_article = {
        "title": "Test",
        "content": "x" * 10000,
        "category": "Test",
    }
    prompt = llm_filter._construct_single_prompt(long_article, "test")
    assert len(prompt) < 10000
    assert "..." in prompt


def test_construct_prompt_backward_compat(llm_filter, sample_article):
    """Test that _construct_prompt alias works."""
    prompt = llm_filter._construct_prompt(sample_article, "prefs")
    assert sample_article["title"] in prompt


# ── Batch prompt construction ─────────────────────────────────────────


def test_construct_batch_prompt(llm_filter, sample_articles):
    """Test batch prompt construction includes all articles."""
    prompt = llm_filter._construct_batch_prompt(sample_articles, "I like tech")

    assert "ARTICLE 0" in prompt
    assert "ARTICLE 1" in prompt
    assert "ARTICLE 2" in prompt
    assert "New AI Technology Breakthrough" in prompt
    assert "Local Restaurant Grand Opening" in prompt
    assert "Football Match Results" in prompt
    assert "exactly 3" in prompt or '"article_index": 0' in prompt


def test_construct_batch_prompt_truncates_long_content(llm_filter):
    """Test that long content in batched articles is truncated."""
    articles = [
        {"title": "Long", "content": "x" * 10000, "category": "Test"},
        {"title": "Short", "content": "brief", "category": "Test"},
    ]
    prompt = llm_filter._construct_batch_prompt(articles, "prefs")
    # Shouldn't exceed reasonable size (2 * 4000 content + overhead)
    assert len(prompt) < 15000


# ── Single-article response parsing ──────────────────────────────────


def test_parse_single_response_valid(llm_filter):
    """Test parsing valid single-article JSON response."""
    response = json.dumps({"score": 8, "reason": "Matches technology interests"})
    score, reason = llm_filter._parse_single_response(response)
    assert score == 8
    assert reason == "Matches technology interests"


def test_parse_single_response_missing_score(llm_filter):
    """Test parsing response with missing score defaults to 1."""
    response = json.dumps({"reason": "Something"})
    score, reason = llm_filter._parse_single_response(response)
    assert score == 1


def test_parse_single_response_clamps_score(llm_filter):
    """Test that scores are clamped to 1-10."""
    response_high = json.dumps({"score": 15, "reason": "test"})
    score, _ = llm_filter._parse_single_response(response_high)
    assert score == 10

    response_low = json.dumps({"score": -5, "reason": "test"})
    score, _ = llm_filter._parse_single_response(response_low)
    assert score == 1


def test_parse_single_response_invalid_json(llm_filter):
    """Test that invalid JSON returns default score."""
    score, reason = llm_filter._parse_single_response("not json at all")
    assert score == 1
    assert "JSON parse error" in reason


def test_parse_json_response_backward_compat(llm_filter):
    """Test that _parse_json_response alias works."""
    response = json.dumps({"score": 7, "reason": "ok"})
    score, reason = llm_filter._parse_json_response(response)
    assert score == 7


# ── Batch response parsing ────────────────────────────────────────────


def test_parse_batch_response_valid(llm_filter):
    """Test parsing valid batch response."""
    response = json.dumps(
        {
            "results": [
                {"article_index": 0, "score": 9, "reason": "Tech match"},
                {"article_index": 1, "score": 7, "reason": "Food match"},
                {"article_index": 2, "score": 2, "reason": "Sports - ignored"},
            ]
        }
    )
    results = llm_filter._parse_batch_response(response, 3)

    assert len(results) == 3
    assert results[0] == (9, "Tech match")
    assert results[1] == (7, "Food match")
    assert results[2] == (2, "Sports - ignored")


def test_parse_batch_response_out_of_order(llm_filter):
    """Test that batch parser handles out-of-order results."""
    response = json.dumps(
        {
            "results": [
                {"article_index": 2, "score": 3, "reason": "Third"},
                {"article_index": 0, "score": 8, "reason": "First"},
                {"article_index": 1, "score": 5, "reason": "Second"},
            ]
        }
    )
    results = llm_filter._parse_batch_response(response, 3)

    assert results[0] == (8, "First")
    assert results[1] == (5, "Second")
    assert results[2] == (3, "Third")


def test_parse_batch_response_missing_article(llm_filter):
    """Test that missing articles get default score of 1."""
    response = json.dumps(
        {
            "results": [
                {"article_index": 0, "score": 8, "reason": "Found"},
                # article_index 1 is missing
                {"article_index": 2, "score": 6, "reason": "Also found"},
            ]
        }
    )
    results = llm_filter._parse_batch_response(response, 3)

    assert len(results) == 3
    assert results[0] == (8, "Found")
    assert results[1] == (1, "Missing from batch response")
    assert results[2] == (6, "Also found")


def test_parse_batch_response_invalid_json(llm_filter):
    """Test that invalid JSON returns all defaults."""
    results = llm_filter._parse_batch_response("not json", 3)
    assert len(results) == 3
    assert all(score == 1 for score, _ in results)


def test_parse_batch_response_missing_results_key(llm_filter):
    """Test that missing 'results' key returns all defaults."""
    response = json.dumps({"data": []})
    results = llm_filter._parse_batch_response(response, 2)
    assert len(results) == 2
    assert all(score == 1 for score, _ in results)


def test_parse_batch_response_clamps_scores(llm_filter):
    """Test that batch parser clamps scores to 1-10."""
    response = json.dumps(
        {
            "results": [
                {"article_index": 0, "score": 15, "reason": "high"},
                {"article_index": 1, "score": -3, "reason": "low"},
            ]
        }
    )
    results = llm_filter._parse_batch_response(response, 2)
    assert results[0][0] == 10
    assert results[1][0] == 1


def test_parse_batch_response_missing_score_in_item(llm_filter):
    """Test that missing score in a batch item defaults to 1."""
    response = json.dumps(
        {
            "results": [
                {"article_index": 0, "reason": "no score here"},
            ]
        }
    )
    results = llm_filter._parse_batch_response(response, 1)
    assert results[0] == (1, "no score here")


def test_parse_batch_response_empty_results(llm_filter):
    """Test batch parser with empty results array."""
    response = json.dumps({"results": []})
    results = llm_filter._parse_batch_response(response, 2)
    assert len(results) == 2
    assert all(score == 1 for score, _ in results)


# ── analyze_article (single) ─────────────────────────────────────────


def test_analyze_article_delegates_to_batch(llm_filter, sample_article):
    """Test that analyze_article wraps analyze_articles_batch."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({"score": 8, "reason": "Tech article"})
    llm_filter.client.chat.completions.create = MagicMock(return_value=mock_response)

    score, reason = llm_filter.analyze_article(sample_article, "I like tech")

    assert score == 8
    assert reason == "Tech article"


def test_analyze_article_handles_errors(llm_filter, sample_article):
    """Test that LLM errors are handled gracefully."""
    llm_filter.client.chat.completions.create = MagicMock(side_effect=Exception("Connection error"))

    score, reason = llm_filter.analyze_article(sample_article, "I like tech")
    assert score == 1
    assert "Error" in reason


# ── analyze_articles_batch ────────────────────────────────────────────


def test_analyze_articles_batch_empty(llm_filter):
    """Test batch analysis with empty list."""
    results = llm_filter.analyze_articles_batch([])
    assert results == []


def test_analyze_articles_batch_single_uses_single_prompt(llm_filter, sample_article):
    """Test that a single-article batch uses the simpler single prompt."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({"score": 9, "reason": "Relevant"})
    llm_filter.client.chat.completions.create = MagicMock(return_value=mock_response)

    results = llm_filter.analyze_articles_batch([sample_article], "prefs")

    assert len(results) == 1
    assert results[0] == (9, "Relevant")

    # Verify the prompt used was the single-article format (no "ARTICLE 0" header)
    call_args = llm_filter.client.chat.completions.create.call_args
    prompt = call_args.kwargs["messages"][1]["content"]
    assert "ARTICLE 0" not in prompt


def test_analyze_articles_batch_multiple(llm_filter, sample_articles):
    """Test batch analysis with multiple articles."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "results": [
                {"article_index": 0, "score": 9, "reason": "Tech"},
                {"article_index": 1, "score": 7, "reason": "Food"},
                {"article_index": 2, "score": 2, "reason": "Sports"},
            ]
        }
    )
    llm_filter.client.chat.completions.create = MagicMock(return_value=mock_response)

    results = llm_filter.analyze_articles_batch(sample_articles, "prefs")

    assert len(results) == 3
    assert results[0] == (9, "Tech")
    assert results[1] == (7, "Food")
    assert results[2] == (2, "Sports")

    # Should have made only 1 API call
    assert llm_filter.client.chat.completions.create.call_count == 1


def test_analyze_articles_batch_falls_back_on_error(llm_filter, sample_articles):
    """Test that batch failure falls back to individual calls."""
    # First call (batch) fails, subsequent calls (individual) succeed
    single_response = MagicMock()
    single_response.choices = [MagicMock()]
    single_response.choices[0].message.content = json.dumps({"score": 5, "reason": "Fallback"})

    llm_filter.client.chat.completions.create = MagicMock(
        side_effect=[
            Exception("Batch failed"),  # batch call fails
            single_response,  # fallback call 1
            single_response,  # fallback call 2
            single_response,  # fallback call 3
        ]
    )

    results = llm_filter.analyze_articles_batch(sample_articles, "prefs")

    assert len(results) == 3
    # All should have gotten fallback results
    assert all(score == 5 for score, _ in results)
    # 1 batch attempt + 3 individual fallbacks = 4 calls
    assert llm_filter.client.chat.completions.create.call_count == 4


# ── Connection test ───────────────────────────────────────────────────


def test_test_connection_success(llm_filter):
    """Test successful connection."""
    llm_filter.client.chat.completions.create = MagicMock(return_value=MagicMock())
    assert llm_filter.test_connection() is True


def test_test_connection_failure(llm_filter):
    """Test failed connection."""
    llm_filter.client.chat.completions.create = MagicMock(
        side_effect=Exception("Connection refused")
    )
    assert llm_filter.test_connection() is False
