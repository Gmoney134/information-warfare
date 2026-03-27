from datetime import datetime, timezone
from uuid import uuid4

import pytest

import app.database as db_module
from app.database import get_score_by_url, init_db, insert_score
from app.models import MatchedNarrative, NarrativeScore


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()


def _make_score(**kwargs) -> NarrativeScore:
    defaults = dict(
        id=uuid4(),
        url="https://example.com/article",
        domain="example.com",
        narrative_score=2,
        domain_flagged=False,
        matched_narratives=[],
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return NarrativeScore(**defaults)


def test_insert_and_retrieve():
    score = _make_score()
    insert_score(score)
    result = get_score_by_url(score.url)
    assert result is not None
    assert result.id == score.id
    assert result.url == score.url
    assert result.narrative_score == score.narrative_score
    assert result.domain_flagged is False


def test_get_score_by_url_not_found():
    result = get_score_by_url("https://nothere.com/article")
    assert result is None


def test_insert_score_with_matched_narratives():
    score = _make_score(
        narrative_score=4,
        matched_narratives=[
            MatchedNarrative(
                narrative_title="Test Narrative",
                similarity_score=0.9,
                explanation="Strong match.",
            )
        ],
    )
    insert_score(score)
    result = get_score_by_url(score.url)
    assert len(result.matched_narratives) == 1
    assert result.matched_narratives[0].narrative_title == "Test Narrative"
    assert result.matched_narratives[0].similarity_score == 0.9


def test_insert_score_domain_flagged():
    score = _make_score(
        url="https://baddomain.com/article",
        domain="baddomain.com",
        narrative_score=5,
        domain_flagged=True,
        matched_narratives=[
            MatchedNarrative(
                narrative_title="Known disinfo domain",
                similarity_score=1.0,
                explanation="Domain matched known information warfare domain list",
            )
        ],
    )
    insert_score(score)
    result = get_score_by_url(score.url)
    assert result.domain_flagged is True
    assert result.narrative_score == 5
