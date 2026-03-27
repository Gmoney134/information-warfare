from datetime import datetime, timezone
from uuid import uuid4

from app.models import MatchedNarrative, NarrativeScore, NarrativeScoreRequest


def test_matched_narrative_fields():
    n = MatchedNarrative(
        narrative_title="Test Narrative",
        similarity_score=0.85,
        explanation="Article closely mirrors this narrative.",
    )
    assert n.narrative_title == "Test Narrative"
    assert n.similarity_score == 0.85


def test_narrative_score_fields():
    score = NarrativeScore(
        id=uuid4(),
        url="https://example.com/article",
        domain="example.com",
        narrative_score=3,
        domain_flagged=False,
        matched_narratives=[],
        created_at=datetime.now(timezone.utc),
    )
    assert score.narrative_score == 3
    assert score.domain_flagged is False


def test_narrative_score_domain_flagged():
    score = NarrativeScore(
        id=uuid4(),
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
        created_at=datetime.now(timezone.utc),
    )
    assert score.narrative_score == 5
    assert score.domain_flagged is True
    assert len(score.matched_narratives) == 1


def test_narrative_score_request():
    req = NarrativeScoreRequest(url="https://example.com/article")
    assert req.url == "https://example.com/article"
