"""Unit tests for LLM filter module."""

from unittest.mock import patch

import pytest

from src.llm_filter import LLMFilter


@pytest.fixture
def llm_filter():
    """Create an LLMFilter instance for testing."""
    return LLMFilter(base_url="http://localhost:11434", model="llama3.2:1b")


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


def test_llm_filter_initialization(llm_filter):
    """Test that LLM filter initializes correctly."""
    assert llm_filter.base_url == "http://localhost:11434"
    assert llm_filter.model == "llama3.2:1b"
    assert llm_filter.timeout == 60
    assert llm_filter.preferences == ""


def test_load_preferences(llm_filter, mock_preferences):
    """Test loading preferences from file."""
    llm_filter.load_preferences(mock_preferences)

    assert len(llm_filter.preferences) > 0
    assert "Technology news" in llm_filter.preferences


def test_load_preferences_file_not_found(llm_filter):
    """Test that loading missing preferences file raises error."""
    with pytest.raises(FileNotFoundError):
        llm_filter.load_preferences("nonexistent.md")


@patch("src.llm_filter.ollama.generate")
def test_analyze_article(mock_generate, llm_filter, sample_article):
    """Test analyzing article with LLM."""
    # Mock Ollama response
    mock_generate.return_value = {
        "response": "SCORE: 8\nREASON: This article is highly relevant to technology interests."
    }

    score, reason = llm_filter.analyze_article(sample_article, "I like technology news")

    assert score == 8
    assert "highly relevant" in reason.lower()
    mock_generate.assert_called_once()


@patch("src.llm_filter.ollama.generate")
def test_analyze_article_uses_loaded_preferences(
    mock_generate, llm_filter, sample_article, mock_preferences
):
    """Test that analyze_article uses loaded preferences if not provided."""
    llm_filter.load_preferences(mock_preferences)

    mock_generate.return_value = {"response": "SCORE: 7\nREASON: Somewhat relevant"}

    score, reason = llm_filter.analyze_article(sample_article)

    assert score == 7
    # Verify preferences were used in prompt
    call_args = mock_generate.call_args
    assert "Technology news" in call_args.kwargs["prompt"]


@patch("src.llm_filter.ollama.generate")
def test_analyze_article_handles_errors(mock_generate, llm_filter, sample_article):
    """Test that LLM errors are handled gracefully."""
    mock_generate.side_effect = Exception("Connection error")

    score, reason = llm_filter.analyze_article(sample_article, "I like tech")

    assert score == 1  # Error returns low score
    assert "Error" in reason


def test_construct_prompt(llm_filter, sample_article):
    """Test prompt construction."""
    preferences = "I like technology"
    prompt = llm_filter._construct_prompt(sample_article, preferences)

    assert "I like technology" in prompt
    assert sample_article["title"] in prompt
    assert sample_article["content"] in prompt
    assert "SCORE:" in prompt
    assert "REASON:" in prompt


def test_construct_prompt_truncates_long_content(llm_filter):
    """Test that very long content is truncated."""
    long_article = {
        "title": "Test",
        "content": "x" * 10000,  # Very long content
        "category": "Test",
    }

    prompt = llm_filter._construct_prompt(long_article, "test")

    # Content should be truncated
    assert len(prompt) < 10000
    assert "..." in prompt


def test_parse_response_with_valid_format(llm_filter):
    """Test parsing valid LLM response."""
    response = "SCORE: 9\nREASON: This is highly relevant to user interests."

    score, reason = llm_filter._parse_response(response)

    assert score == 9
    assert reason == "This is highly relevant to user interests."


def test_parse_response_with_case_insensitive_keywords(llm_filter):
    """Test parsing with different case."""
    response = "score: 7\nreason: Somewhat interesting article."

    score, reason = llm_filter._parse_response(response)

    assert score == 7
    assert "Somewhat interesting" in reason


def test_parse_response_clamps_score_to_range(llm_filter):
    """Test that scores are clamped to 1-10."""
    # Score too high
    response1 = "SCORE: 15\nREASON: test"
    score1, _ = llm_filter._parse_response(response1)
    assert score1 == 10

    # Score too low
    response2 = "SCORE: -5\nREASON: test"
    score2, _ = llm_filter._parse_response(response2)
    assert score2 == 1


def test_parse_response_handles_malformed_response(llm_filter):
    """Test parsing malformed LLM response."""
    response = "This article seems relevant but I forgot to format my response."

    score, reason = llm_filter._parse_response(response)

    # Should return defaults
    assert score == 5  # Default middle score
    assert "No reason provided" in reason


def test_parse_response_extracts_multiline_reason(llm_filter):
    """Test parsing reason that spans multiple lines."""
    response = """SCORE: 8
REASON: This is relevant because it covers technology.
Some additional text here."""

    score, reason = llm_filter._parse_response(response)

    assert score == 8
    assert "This is relevant" in reason


@patch("src.llm_filter.ollama.list")
def test_test_connection_success(mock_list, llm_filter):
    """Test successful connection to Ollama."""
    mock_list.return_value = {"models": []}

    result = llm_filter.test_connection()

    assert result is True


@patch("src.llm_filter.ollama.list")
def test_test_connection_failure(mock_list, llm_filter):
    """Test failed connection to Ollama."""
    mock_list.side_effect = Exception("Connection refused")

    result = llm_filter.test_connection()

    assert result is False
