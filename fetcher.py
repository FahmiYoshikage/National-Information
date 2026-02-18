"""
RSS Fetcher
Mengambil dan mem-parsing artikel dari semua feed yang dikonfigurasi
"""

import logging
import feedparser
import requests
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NasionalNewsBot/1.0; "
        "+https://github.com/nationalbot)"
    )
}


@dataclass
class Article:
    source: str          # nama feed, e.g. "🇮🇩 Antara - Top News"
    title: str
    url: str
    summary: str = ""
    published: str = ""
    image_url: Optional[str] = field(default=None)


def _get_image(entry) -> Optional[str]:
    """Coba ambil URL gambar dari berbagai field RSS yang umum."""
    # media:content
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url")
    # media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    # enclosures (format podcast/RSS standar)
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("url") or enc.get("href")
    # links
    if hasattr(entry, "links"):
        for link in entry.links:
            if link.get("type", "").startswith("image"):
                return link.get("href")
    return None


def _clean_summary(raw: str, max_len: int = 300) -> str:
    """Hapus tag HTML sederhana dan potong text jika terlalu panjang."""
    import re
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text


def fetch_feed(source_name: str, feed_url: str) -> List[Article]:
    """Ambil artikel terbaru dari satu RSS feed."""
    articles: List[Article] = []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        entries = feed.entries[:MAX_ARTICLES_PER_FEED]
        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue

            title = entry.get("title", "Tanpa Judul").strip()
            summary = _clean_summary(entry.get("summary", ""))
            image = _get_image(entry)

            # Format tanggal
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    published = dt.strftime("%d %b %Y, %H:%M WIB")
                except Exception:
                    published = ""

            articles.append(Article(
                source=source_name,
                title=title,
                url=url,
                summary=summary,
                published=published,
                image_url=image,
            ))

    except requests.RequestException as e:
        logger.warning("Gagal mengambil feed [%s]: %s", source_name, e)
    except Exception as e:
        logger.error("Error parsing feed [%s]: %s", source_name, e)

    return articles


def fetch_all_feeds() -> List[Article]:
    """Ambil artikel dari SEMUA feed yang terdaftar di config."""
    all_articles: List[Article] = []
    for name, url in RSS_FEEDS.items():
        logger.debug("Mengambil feed: %s", name)
        articles = fetch_feed(name, url)
        all_articles.extend(articles)
        logger.info("[%s] → %d artikel ditemukan.", name, len(articles))
    return all_articles
