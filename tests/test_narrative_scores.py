from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.domains as domains_module
from app.database import init_db
from app.models import MatchedNarrative
from app.scraper import ArticleContent, ScraperError
from app.analyzer import AnalyzerError


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    domains_module._known_domains.clear()
    init_db()
    yield
    domains_module._known_domains.clear()


@pytest.fixture()
def client():
    from app.main import app
    return TestClient(app)


# --- POST /narrative-scores ---

def test_post_domain_flagged(client):
    domains_module._known_domains.add("baddomain.com")

    response = client.post("/narrative-scores", json={"url": "https://baddomain.com/article"})

    assert response.status_code == 201
    body = response.json()
    assert body["narrative_score"] == 5
    assert body["domain_flagged"] is True
    assert body["domain"] == "baddomain.com"
    assert len(body["matched_narratives"]) == 1
    assert body["matched_narratives"][0]["narrative_title"] == "Known disinfo domain"


def test_post_clean_article(client):
    article = ArticleContent(url="https://legit.com/article", title="Title", text="Some text.")
    narratives = [MatchedNarrative(narrative_title="N1", similarity_score=0.4, explanation="Weak match.")]

    with patch("app.routers.narrative_scores.scrape_article", return_value=article), \
         patch("app.routers.narrative_scores.analyze_article", return_value=(2, narratives)):
        response = client.post("/narrative-scores", json={"url": "https://legit.com/article"})

    assert response.status_code == 201
    body = response.json()
    assert body["narrative_score"] == 2
    assert body["domain_flagged"] is False
    assert body["domain"] == "legit.com"
    assert len(body["matched_narratives"]) == 1


def test_post_scraper_error_returns_422(client):
    with patch("app.routers.narrative_scores.scrape_article", side_effect=ScraperError("Failed to fetch URL")):
        response = client.post("/narrative-scores", json={"url": "https://legit.com/article"})

    assert response.status_code == 422
    assert "Failed to fetch URL" in response.json()["detail"]


def test_post_analyzer_error_returns_502(client):
    article = ArticleContent(url="https://legit.com/article", title="Title", text="Some text.")

    with patch("app.routers.narrative_scores.scrape_article", return_value=article), \
         patch("app.routers.narrative_scores.analyze_article", side_effect=AnalyzerError("OpenAI API error")):
        response = client.post("/narrative-scores", json={"url": "https://legit.com/article"})

    assert response.status_code == 502
    assert "OpenAI API error" in response.json()["detail"]


def test_post_persists_result(client):
    article = ArticleContent(url="https://legit.com/article", title="Title", text="Some text.")

    with patch("app.routers.narrative_scores.scrape_article", return_value=article), \
         patch("app.routers.narrative_scores.analyze_article", return_value=(1, [])):
        client.post("/narrative-scores", json={"url": "https://legit.com/article"})

    response = client.get("/narrative-scores", params={"url": "https://legit.com/article"})
    assert response.status_code == 200
    assert response.json()["narrative_score"] == 1


# --- GET /narrative-scores ---

def test_get_returns_stored_result(client):
    article = ArticleContent(url="https://example.com/story", title="Story", text="Text.")

    with patch("app.routers.narrative_scores.scrape_article", return_value=article), \
         patch("app.routers.narrative_scores.analyze_article", return_value=(3, [])):
        client.post("/narrative-scores", json={"url": "https://example.com/story"})

    response = client.get("/narrative-scores", params={"url": "https://example.com/story"})
    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com/story"
    assert response.json()["narrative_score"] == 3


def test_get_not_found(client):
    response = client.get("/narrative-scores", params={"url": "https://notanalyzed.com/article"})
    assert response.status_code == 404
