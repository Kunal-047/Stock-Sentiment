# ingest_news.py
# ingest_news.py
# Sources: GDELT (free, no key, ~1 year of news) + GNews (free tier, recent)
# DB target: headlines(source, ticker, title, description, url, published_at)
# Dedup key: UNIQUE(url)

import requests
import time
from datetime import datetime, timedelta
from db import get_conn
from config import TICKERS

# ── GDELT ────────────────────────────────────────────────────────────────────

def fetch_gdelt(ticker: str, timespan: str = "1y"):
    """
    Pull headlines from GDELT Doc 2.0 API.
    Free, no API key. Returns up to 250 articles per query.
    timespan: "1y" | "6m" | "90d" | "30d" | "7d" etc.
    published_at is returned in GDELT's YYYYMMDDTHHMMSSZ format —
    we normalise to ISO-8601 (matching existing rows in the DB).
    """
    query = ticker.split("-")[0]   # strip -USD etc.
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query":      f'"{query}" sourcelang:english',
        "mode":       "artlist",
        "maxrecords": 250,
        "format":     "json",
        "timespan":   timespan,
        "sort":       "DateDesc",
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        articles = resp.json().get("articles") or []
    except Exception as e:
        print(f"  GDELT failed for {ticker}: {e}")
        return []

    rows = []
    for a in articles:
        # GDELT date format: "20250101T120000Z" → "2025-01-01T12:00:00Z"
        raw_date = a.get("seendate", "")
        try:
            dt = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ")
            published_at = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            published_at = raw_date   # store as-is if parse fails

        rows.append({
            "source":       "gdelt",
            "ticker":       ticker,
            "title":        a.get("title", ""),
            "description":  "",          # GDELT artlist doesn't return a body snippet
            "url":          a.get("url", ""),
            "published_at": published_at,
        })
    return rows


# ── GNews (free tier — recent headlines only) ─────────────────────────────────

def fetch_gnews(ticker: str, gnews_key: str):
    """
    Pull recent headlines from GNews free tier.
    Kept as a secondary source for recency; GDELT covers the history.
    """
    query = ticker.split("-")[0]
    url = "https://gnews.io/api/v4/search"
    params = {
        "q":     query,
        "lang":  "en",
        "max":   10,
        "token": gnews_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception as e:
        print(f"  GNews failed for {ticker}: {e}")
        return []

    rows = []
    for a in articles:
        rows.append({
            "source":       "gnews",
            "ticker":       ticker,
            "title":        a.get("title", ""),
            "description":  a.get("description", ""),
            "url":          a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
        })
    return rows


# ── HuggingFace financial-news dataset (static historical dump) ───────────────

def fetch_hf_dataset(ticker: str):
    """
    Pull from the 'ashraq/financial-news-articles' HuggingFace dataset.
    This is a static ~300k-headline dump — great for backfilling history.
    Requires: pip install datasets
    Only runs if the 'datasets' package is available; skips silently otherwise.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        return []

    query = ticker.split("-")[0].upper()
    try:
        # streaming=True avoids downloading the full dataset upfront
        ds = load_dataset(
            "ashraq/financial-news-articles",
            split="train",
            streaming=True,
        )
    except Exception as e:
        print(f"  HuggingFace dataset failed: {e}")
        return []

    rows = []
    for item in ds:
        text = f"{item.get('headline', '')} {item.get('text', '')}".upper()
        if query not in text:
            continue
        # Dataset has a 'date' field in "YYYY-MM-DD" format
        raw_date = item.get("date", "")
        published_at = f"{raw_date}T00:00:00Z" if raw_date else ""
        rows.append({
            "source":       "hf_financial_news",
            "ticker":       ticker,
            "title":        item.get("headline", ""),
            "description":  item.get("text", "")[:500],
            "url":          item.get("url", ""),
            "published_at": published_at,
        })
        if len(rows) >= 500:   # cap per ticker to avoid runaway memory
            break

    return rows


# ── DB writer ─────────────────────────────────────────────────────────────────

def store_headlines(rows: list):
    """
    Insert rows into headlines table.
    Schema: id, source, ticker, title, description, url, published_at, fetched_at
    Dedup key: UNIQUE(url)  →  INSERT OR IGNORE silently skips duplicates.
    """
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        if not r.get("url"):        # rows with no URL can't be deduped — skip
            continue
        try:
            cur.execute("""
                INSERT OR IGNORE INTO headlines
                    (source, ticker, title, description, url, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r["source"],
                r["ticker"],
                r["title"],
                r["description"],
                r["url"],
                r["published_at"],
            ))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Skipped duplicate/error: {e}")
    conn.commit()
    conn.close()
    return inserted


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    # Import GNEWS_KEY lazily — if it doesn't exist in config, skip GNews
    try:
        from config import GNEWS_KEY
    except ImportError:
        GNEWS_KEY = None

    for ticker in TICKERS:
        print(f"[News] Fetching for {ticker}...")
        rows = []

        # 1. GDELT — free, no key, ~1 year of history
        gdelt_rows = fetch_gdelt(ticker, timespan="2d")
        rows += gdelt_rows
        print(f"  GDELT: {len(gdelt_rows)} articles")
        time.sleep(1)   # be polite to GDELT

        # 2. GNews — free tier, recent headlines, richer description field
        if GNEWS_KEY:
            gnews_rows = fetch_gnews(ticker, GNEWS_KEY)
            rows += gnews_rows
            print(f"  GNews: {len(gnews_rows)} articles")

        # 3. HuggingFace static dataset — deep historical backfill
        hf_rows = fetch_hf_dataset(ticker)
        rows += hf_rows
        if hf_rows:
            print(f"  HuggingFace: {len(hf_rows)} articles")

        n = store_headlines(rows)
        print(f"  Inserted {n}/{len(rows)} headlines for {ticker}")


if __name__ == "__main__":
    run()