import json
from unittest.mock import patch

import pytest

from app.scraper import ArticleContent, ScraperError, scrape_article


def _make_trafilatura_json(text="Article body text.", title="Article Title"):
    return json.dumps({"text": text, "title": title})


def test_scrape_article_success():
    with patch("trafilatura.fetch_url", return_value="<html>...</html>") as mock_fetch, \
         patch("trafilatura.extract", return_value=_make_trafilatura_json()) as mock_extract:
        result = scrape_article("https://example.com/article")

    assert isinstance(result, ArticleContent)
    assert result.url == "https://example.com/article"
    assert result.title == "Article Title"
    assert result.text == "Article body text."
    mock_fetch.assert_called_once_with("https://example.com/article")


def test_scrape_article_fetch_fails():
    with patch("trafilatura.fetch_url", return_value=None):
        with pytest.raises(ScraperError, match="Failed to fetch URL"):
            scrape_article("https://unreachable.example.com/article")


def test_scrape_article_no_content_extracted():
    with patch("trafilatura.fetch_url", return_value="<html>...</html>"), \
         patch("trafilatura.extract", return_value=None):
        with pytest.raises(ScraperError, match="No article content could be extracted"):
            scrape_article("https://example.com/not-an-article")


def test_scrape_article_empty_text():
    with patch("trafilatura.fetch_url", return_value="<html>...</html>"), \
         patch("trafilatura.extract", return_value=_make_trafilatura_json(text="   ")):
        with pytest.raises(ScraperError, match="no text content"):
            scrape_article("https://example.com/empty")


def test_scrape_article_missing_title():
    payload = json.dumps({"text": "Some article text.", "title": None})
    with patch("trafilatura.fetch_url", return_value="<html>...</html>"), \
         patch("trafilatura.extract", return_value=payload):
        result = scrape_article("https://example.com/article")
    assert result.title == ""
    assert result.text == "Some article text."
