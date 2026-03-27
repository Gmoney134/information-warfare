# Implementation Plan — Information Warfare Analyzer

## Overview

A FastAPI service that accepts article URLs from a Chrome extension, checks the domain against a known disinfo domain list, and (if not flagged) uses OpenAI's Responses API with web search to score the article's similarity to known information warfare narratives sourced from [EUvsDisinfo](https://euvsdisinfo.eu/disinformation-cases/).

---

## Scoring Scale

| Score | Meaning |
|-------|---------|
| 1 | Very little or no similarity to known IW narratives |
| 2 | Low similarity |
| 3 | Medium similarity |
| 4 | High similarity |
| 5 | **Domain match only** — article domain found in `disinfodomains.csv` |

Domain check always runs first. A score of 5 short-circuits the pipeline — no article scraping or OpenAI call is made.

---

## Issues & Implementation Order

Dependencies drive the order. Issues with no blockers are implemented first.

### Phase 1 — Foundation (no dependencies)

#### #8 — Narrative Score Domain Model
- Define a `NarrativeScore` Pydantic model used by both endpoints and SQLite
- Fields: `id` (UUID), `url`, `domain`, `narrative_score` (1–5), `domain_flagged` (bool), `matched_narratives` (list), `created_at`
- `matched_narratives` items: `narrative_title`, `similarity_score` (float 0–1), `explanation`
- For score-5 (domain-flagged) results, `matched_narratives` contains a single entry: `{ "narrative_title": "Known disinfo domain", "similarity_score": 1.0, "explanation": "Domain matched known information warfare domain list" }`
- File: `src/app/models.py`

#### #6 — Known Domains CSV Integration
- Load `disinfodomains.csv` at startup from a configurable path (`DOMAINS_CSV_PATH` env var, default `./disinfodomains.csv`)
- Single `Domain` column, exact match (case-insensitive) against the submitted URL's domain
- File: `src/app/domains.py`

#### #10 — SQLite Persistence Layer
- DB file path configurable via `DB_PATH` env var (default `./iwa.db`)
- Single `narrative_scores` table, schema derived from `NarrativeScore` model
- `matched_narratives` stored as JSON text column
- `created_at` set automatically on insert
- Create table on startup if it doesn't exist (no migration framework for MVP)
- File: `src/app/database.py`

---

### Phase 2 — Integration Layer

#### #11 — Article Scraping
- Use `trafilatura` as the primary extraction library (best accuracy on news articles)
- Fetch URL, extract article text and title
- Return extracted text + title
- Raise clear errors for: non-200 responses, no extractable text, non-English content
- File: `src/app/scraper.py`

#### #9 — OpenAI Integration (Option A — Web Search)
- Use OpenAI **Responses API** with the `web_search_preview` tool
- Model configurable via `OPENAI_MODEL` env var (default `gpt-4o`)
- API key via `OPENAI_API_KEY` env var
- Prompt instructs the model to:
  1. Search euvsdisinfo.eu for current known IW narratives
  2. Compare the provided article text against those narratives
  3. Use its own judgement to assign an overall score (1–4)
  4. Return structured JSON: overall score, matched narratives with similarity scores and explanations
- Response requested as structured JSON via `response_format` (structured outputs)
- Response parsed into `matched_narratives` list and overall `narrative_score`
- Handle: rate limits, timeouts, API errors — return 502 with clear message
- File: `src/app/analyzer.py`

---

### Phase 3 — API Endpoints

#### #2 — HTTP API Layer
- Register routers on the existing FastAPI app in `main.py`
- Keep `/health` endpoint

#### #4 — `POST /narrative-scores`
Pipeline:
1. Parse `{ "url": "..." }` from request body
2. Extract domain from URL
3. Check domain against `disinfodomains.csv`
   - Match → score 5, `domain_flagged=True`, skip to step 6
4. Scrape article text from URL (#11)
5. Analyze with OpenAI (#9) → score 1–4 + matched narratives
6. Persist result to SQLite (#10)
7. Return `NarrativeScore` JSON response

#### #5 — `GET /narrative-scores?url=https://example.com/article`
- Look up a previously stored result by exact URL match
- Returns a single `NarrativeScore` object if found, or 404 if not yet analyzed
- Allows the Chrome extension to retrieve a cached result without re-triggering analysis
- Domain is only used internally (for the domain-match check in the POST pipeline), not as a query parameter

---

### Phase 4 — Containerization

#### #3 — Dockerfile
- Python 3.11 slim base image
- Install poetry, install production deps only
- Expose port 8000
- `CMD ["poetry", "run", "start"]`
- `.dockerignore` to exclude tests, venv, etc.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAINS_CSV_PATH` | `./disinfodomains.csv` | Path to known disinfo domains CSV |
| `DB_PATH` | `./iwa.db` | SQLite database file path |
| `OPENAI_API_KEY` | — | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |

---

## File Layout (target state)

```
src/app/
  __init__.py
  main.py          — FastAPI app, router registration, startup hooks
  models.py        — Pydantic models (NarrativeScore, MatchedNarrative, etc.)
  domains.py       — CSV loader + domain lookup
  database.py      — SQLite setup, insert, query
  scraper.py       — Article URL fetching + text extraction
  analyzer.py      — OpenAI Responses API integration
  routers/
    narrative_scores.py  — POST and GET /narrative-scores

tests/
  conftest.py
  test_health.py
  test_domains.py
  test_scraper.py
  test_analyzer.py
  test_narrative_scores.py  — integration tests for both endpoints
```

---

## New Dependencies to Add

| Package | Purpose |
|---------|---------|
| `trafilatura` | Article text extraction |
| `openai` | OpenAI Responses API client |
| `pydantic` | Already bundled with FastAPI, used for models |

---

## Resolved Decisions

1. **OpenAI prompt structure** — Structured JSON output via `response_format`. More reliable and no parsing required.
2. **Scoring thresholds** — LLM assigns the overall 1–4 score based on its own judgement.
3. **`matched_narratives` on a score-5 result** — Single entry: `{ "narrative_title": "Known disinfo domain", "similarity_score": 1.0, "explanation": "Domain matched known information warfare domain list" }`.
4. **`GET /narrative-scores`** — Query by exact URL, returns a single result or 404. Domain is only used internally for the domain-match check, not as a query parameter.
