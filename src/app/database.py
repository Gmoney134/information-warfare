import json
import os
import sqlite3
from datetime import datetime, timezone
from uuid import UUID

from app.models import MatchedNarrative, NarrativeScore


def _get_db_path() -> str:
    return os.getenv("DB_PATH", "./iwa.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS narrative_scores (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                domain TEXT NOT NULL,
                narrative_score INTEGER NOT NULL,
                domain_flagged INTEGER NOT NULL,
                matched_narratives TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def insert_score(score: NarrativeScore) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO narrative_scores
                (id, url, domain, narrative_score, domain_flagged, matched_narratives, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(score.id),
                score.url,
                score.domain,
                score.narrative_score,
                int(score.domain_flagged),
                json.dumps([n.model_dump() for n in score.matched_narratives]),
                score.created_at.isoformat(),
            ),
        )


def get_score_by_url(url: str) -> NarrativeScore | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM narrative_scores WHERE url = ?", (url,)
        ).fetchone()

    if row is None:
        return None

    return NarrativeScore(
        id=UUID(row["id"]),
        url=row["url"],
        domain=row["domain"],
        narrative_score=row["narrative_score"],
        domain_flagged=bool(row["domain_flagged"]),
        matched_narratives=[
            MatchedNarrative(**n) for n in json.loads(row["matched_narratives"])
        ],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
