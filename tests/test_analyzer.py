from unittest.mock import MagicMock, patch

import pytest

from app.analyzer import AnalyzerError, analyze_article
from app.models import MatchedNarrative


def _make_mock_response(narrative_score: int, matched_narratives: list[dict]):
    from app.analyzer import _AnalysisResult, _MatchedNarrativeSchema

    parsed = _AnalysisResult(
        narrative_score=narrative_score,
        matched_narratives=[_MatchedNarrativeSchema(**n) for n in matched_narratives],
    )
    mock_response = MagicMock()
    mock_response.output_parsed = parsed
    return mock_response


@pytest.fixture()
def mock_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_client = MagicMock()
    with patch("app.analyzer.OpenAI", return_value=mock_client):
        yield mock_client


def test_analyze_article_returns_score_and_narratives(mock_openai):
    mock_openai.responses.parse.return_value = _make_mock_response(
        narrative_score=3,
        matched_narratives=[
            {
                "narrative_title": "West is responsible for the war in Ukraine",
                "similarity_score": 0.75,
                "explanation": "Article blames NATO expansion for the conflict.",
            }
        ],
    )

    score, narratives = analyze_article("Some article text about NATO and Ukraine.")

    assert score == 3
    assert len(narratives) == 1
    assert isinstance(narratives[0], MatchedNarrative)
    assert narratives[0].narrative_title == "West is responsible for the war in Ukraine"
    assert narratives[0].similarity_score == 0.75


def test_analyze_article_no_matches(mock_openai):
    mock_openai.responses.parse.return_value = _make_mock_response(
        narrative_score=1,
        matched_narratives=[],
    )

    score, narratives = analyze_article("Completely benign article text.")

    assert score == 1
    assert narratives == []


def test_analyze_article_multiple_matches(mock_openai):
    mock_openai.responses.parse.return_value = _make_mock_response(
        narrative_score=4,
        matched_narratives=[
            {
                "narrative_title": "Narrative A",
                "similarity_score": 0.9,
                "explanation": "Strong match.",
            },
            {
                "narrative_title": "Narrative B",
                "similarity_score": 0.7,
                "explanation": "Moderate match.",
            },
        ],
    )

    score, narratives = analyze_article("Article strongly aligned with multiple narratives.")

    assert score == 4
    assert len(narratives) == 2


def test_analyze_article_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AnalyzerError, match="OPENAI_API_KEY"):
        analyze_article("Some text.")


def test_analyze_article_openai_error(mock_openai):
    mock_openai.responses.parse.side_effect = Exception("Rate limit exceeded")
    with pytest.raises(AnalyzerError, match="OpenAI API error"):
        analyze_article("Some text.")
