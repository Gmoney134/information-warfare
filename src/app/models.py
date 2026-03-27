from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MatchedNarrative(BaseModel):
    narrative_title: str
    similarity_score: float
    explanation: str


class NarrativeScore(BaseModel):
    id: UUID
    url: str
    domain: str
    narrative_score: int
    domain_flagged: bool
    matched_narratives: list[MatchedNarrative]
    created_at: datetime


class NarrativeScoreRequest(BaseModel):
    url: str
