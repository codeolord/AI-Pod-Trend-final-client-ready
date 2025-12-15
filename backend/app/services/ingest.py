from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable, List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup


def _clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


async def fetch_rss(url: str, *, timeout_s: int = 30) -> feedparser.FeedParserDict:
    async with httpx.AsyncClient(timeout=timeout_s, headers={"User-Agent": "pod-trend-bot/1.0"}) as client:
        r = await client.get(url)
        r.raise_for_status()
        content = r.text
    return feedparser.parse(content)


def normalize_feed_items(feed: feedparser.FeedParserDict, *, source_url: str) -> List[dict]:
    items: List[dict] = []
    for e in feed.get("entries", []) or []:
        title = (e.get("title") or "").strip()
        link = (e.get("link") or "").strip()
        summary = _clean_html(e.get("summary") or e.get("description") or "")
        published = e.get("published_parsed") or e.get("updated_parsed")
        published_at: Optional[datetime] = None
        if published:
            published_at = datetime(*published[:6], tzinfo=timezone.utc)

        raw = json.dumps({k: e.get(k) for k in list(e.keys())[:50]}, default=str)

        if not title or not link:
            continue

        items.append(
            {
                "source": feed.get("feed", {}).get("title") or source_url,
                "source_url": source_url,
                "title": title,
                "url": link,
                "summary": summary[:2000],
                "published_at": published_at,
                "raw_json": raw,
            }
        )
    return items
