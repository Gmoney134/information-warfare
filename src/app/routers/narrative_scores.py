from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.analyzer import AnalyzerError, analyze_article
from app.database import get_score_by_url, insert_score
from app.domains import extract_domain, is_known_disinfo_domain
from app.models import MatchedNarrative, NarrativeScore, NarrativeScoreRequest
from app.scraper import ScraperError, scrape_article

router = APIRouter(prefix="/narrative-scores", tags=["narrative-scores"])


@router.post("", response_model=NarrativeScore, status_code=201)
def submit_article(request: NarrativeScoreRequest) -> NarrativeScore:
    domain = extract_domain(request.url)

    if is_known_disinfo_domain(request.url):
        score = NarrativeScore(
            id=uuid4(),
            url=request.url,
            domain=domain,
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
        insert_score(score)
        return score

    try:
        article = scrape_article(request.url)
    except ScraperError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        narrative_score, matched_narratives = analyze_article(article.text)
    except AnalyzerError as e:
        raise HTTPException(status_code=502, detail=str(e))

    score = NarrativeScore(
        id=uuid4(),
        url=request.url,
        domain=domain,
        narrative_score=narrative_score,
        domain_flagged=False,
        matched_narratives=matched_narratives,
        created_at=datetime.now(timezone.utc),
    )
    insert_score(score)
    return score


@router.get("", response_model=NarrativeScore)
def get_article_score(url: str) -> NarrativeScore:
    result = get_score_by_url(url)
    if result is None:
        raise HTTPException(status_code=404, detail="No score found for the given URL")
    return result
