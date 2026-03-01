"""FastAPI web application for the Beacon news dashboard."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import Config
from src.database import Database

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Beacon Dashboard")

_BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))

# Initialised once at startup; both are read-only from the web process.
_cfg = Config("config/config.yaml")
_db = Database(_cfg.get_database_path())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _group_by_source(
    articles: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Group articles by source_name, preserving configured source order.

    Sources defined in config.yaml are always present (even if empty).
    Articles whose source_name doesn't match any configured source are
    collected under an 'Unknown' bucket appended at the end.
    """
    # Build ordered map: source name → {meta, articles}
    source_map = {}
    for s in sources:
        name = s["name"]
        source_map[name] = {
            "name": name,
            "url": s["url"],
            "articles": [],
        }

    unknown_bucket: List[Dict[str, Any]] = []

    for article in articles:
        name = article.get("source_name") or ""
        if name in source_map:
            source_map[name]["articles"].append(article)
        else:
            unknown_bucket.append(article)

    result = list(source_map.values())

    if unknown_bucket:
        result.append(
            {
                "name": "Unknown",
                "url": None,
                "articles": unknown_bucket,
            }
        )

    return result


def _split_today_older(
    articles: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Split articles into today's articles and older articles.

    Args:
        articles: List of article dicts, each with a ``scraped_at`` datetime.

    Returns:
        Dict with keys ``today`` and ``older``, each containing a list of articles.
    """
    today_utc = datetime.now(timezone.utc).date()
    today: List[Dict[str, Any]] = []
    older: List[Dict[str, Any]] = []
    for article in articles:
        scraped = article.get("scraped_at")
        if scraped is not None and scraped.date() == today_utc:
            today.append(article)
        else:
            older.append(article)
    return {"today": today, "older": older}


def _source_stats(articles: List[Dict[str, Any]], threshold: int) -> Dict[str, int]:
    """Compute accept/reject/pending stats for a list of articles.

    Args:
        articles: List of article dicts.
        threshold: Minimum relevance score to count as accepted.

    Returns:
        Dict with keys ``total``, ``accepted``, ``rejected``, ``pending``.
    """
    total = len(articles)
    accepted = sum(
        1
        for a in articles
        if a.get("relevance_score") is not None and a["relevance_score"] >= threshold
    )
    rejected = sum(
        1
        for a in articles
        if a.get("relevance_score") is not None and a["relevance_score"] < threshold
    )
    pending = total - accepted - rejected
    return {"total": total, "accepted": accepted, "rejected": rejected, "pending": pending}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    articles = _db.get_recent_articles(days=3)
    sources = _cfg.get_news_sources()
    threshold = _cfg.get_min_relevance_score()

    by_source = _group_by_source(articles, sources)

    # Attach per-source stats and today/older split
    for group in by_source:
        group["stats"] = _source_stats(group["articles"], threshold)
        split = _split_today_older(group["articles"])
        group["today"] = split["today"]
        group["older"] = split["older"]

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "by_source": by_source,
            "threshold": threshold,
            "generated_at": now_utc,
        },
    )
