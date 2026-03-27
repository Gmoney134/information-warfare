import os

from openai import OpenAI
from pydantic import BaseModel

from app.models import MatchedNarrative


EUVSDISINFO_URL = "https://euvsdisinfo.eu/disinformation-cases/"

SYSTEM_PROMPT = """\
You are an information warfare analyst. Your job is to evaluate news articles \
against known disinformation narratives tracked by EUvsDisinfo.

You have access to web search. Search euvsdisinfo.eu to find current known \
information warfare narratives. Each narrative on that site has a title, summary, \
and response.

Compare the provided article text against the narratives you find. Then:
1. Identify any narratives the article aligns with, however loosely.
2. For each match, provide the narrative title, a similarity score (0.0 to 1.0), \
and a brief explanation of why they align.
3. Assign an overall narrative_score from 1 to 4:
   - 1: Very little or no similarity to known IW narratives
   - 2: Low similarity
   - 3: Medium similarity
   - 4: High similarity
Base the overall score on your holistic judgement across all matches found.
"""


class _MatchedNarrativeSchema(BaseModel):
    narrative_title: str
    similarity_score: float
    explanation: str


class _AnalysisResult(BaseModel):
    narrative_score: int
    matched_narratives: list[_MatchedNarrativeSchema]


class AnalyzerError(Exception):
    pass


def analyze_article(text: str) -> tuple[int, list[MatchedNarrative]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AnalyzerError("OPENAI_API_KEY environment variable is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.parse(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this article:\n\n{text}"},
            ],
            text_format=_AnalysisResult,
        )
    except Exception as e:
        raise AnalyzerError(f"OpenAI API error: {e}") from e

    result: _AnalysisResult = response.output_parsed

    matched = [
        MatchedNarrative(
            narrative_title=n.narrative_title,
            similarity_score=n.similarity_score,
            explanation=n.explanation,
        )
        for n in result.matched_narratives
    ]

    return result.narrative_score, matched
