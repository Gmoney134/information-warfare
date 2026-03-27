from dataclasses import dataclass

import trafilatura


class ScraperError(Exception):
    pass


@dataclass
class ArticleContent:
    url: str
    title: str
    text: str


def scrape_article(url: str) -> ArticleContent:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        raise ScraperError(f"Failed to fetch URL: {url}")

    result = trafilatura.extract(
        downloaded,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        favor_precision=True,
    )

    if result is None:
        raise ScraperError(f"No article content could be extracted from: {url}")

    import json
    data = json.loads(result)

    text = data.get("text", "").strip()
    if not text:
        raise ScraperError(f"Extracted article has no text content: {url}")

    title = data.get("title") or ""

    return ArticleContent(url=url, title=title, text=text)
