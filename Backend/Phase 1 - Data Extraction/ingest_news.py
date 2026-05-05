# ingest_news.py
import requests
from datetime import datetime, timedelta
from db import get_conn
from config import NEWSAPI_KEY, GNEWS_KEY, TICKERS

def fetch_newsapi(ticker: str):
    """Pull headlines mentioning ticker from NewsAPI (last 24h)."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "from": yesterday,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])

    rows = []
    for a in articles:
        rows.append({
            "source": "newsapi",
            "ticker": ticker,
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
        })
    return rows

def fetch_gnews(ticker: str):
    """Pull headlines mentioning ticker from GNews."""
    # Sanitize ticker for search — strip exchange suffixes like -USD
    query = ticker.split("-")[0]

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "lang": "en",
        "max": 10,
        "token": GNEWS_KEY,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])

    rows = []
    for a in articles:
        rows.append({
            "source": "gnews",
            "ticker": ticker,           # store original ticker tag
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
        })
    return rows

def store_headlines(rows: list):
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO headlines
                    (source, ticker, title, description, url, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (r["source"], r["ticker"], r["title"],
                  r["description"], r["url"], r["published_at"]))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Skipped duplicate/error: {e}")
    conn.commit()
    conn.close()
    return inserted


def run():
    for ticker in TICKERS:
        print(f"[News] Fetching for {ticker}...")
        rows = []
        rows += fetch_newsapi(ticker)
        try:
            rows += fetch_gnews(ticker)
        except Exception as e:
            print(f"  GNews failed for {ticker}: {e} — skipping")
        n = store_headlines(rows)
        print(f"  Inserted {n}/{len(rows)} headlines for {ticker}")

if __name__ == "__main__":
    run()