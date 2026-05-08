# ingest_reddit.py
# Sources: Arctic Shift API (free, full Reddit archive) + live Reddit /hot.json
# DB target: reddit_posts(post_id, subreddit, ticker, title, body, score, num_comments, created_utc)
# Dedup key: UNIQUE(post_id)

import requests
import re
import time
from datetime import datetime, timedelta
from db import get_conn
from config import TICKERS

SUBREDDITS  = ["wallstreetbets", "investing", "stocks"]
HEADERS     = {"User-Agent": "stock-sentiment-bot/1.0"}

# Build a regex to spot any tracked ticker in post text
TICKER_RE = re.compile(
    r'\b(' + '|'.join(re.escape(t.split("-")[0]) for t in TICKERS) + r')\b'
)


def extract_ticker(text: str):
    """Return first matched ticker from text, or None."""
    m = TICKER_RE.search(text or "")
    return m.group(1) if m else None


# ── Arctic Shift: historical archive (free, no key) ───────────────────────────

def fetch_arctic_shift_historical(
    subreddit: str,
    after_date: str,
    before_date: str,
    limit: int = 100,
):
    """
    Pull archived Reddit posts from Arctic Shift.
    Free public API, no key required, covers the full Reddit archive.
    after_date / before_date: "YYYY-MM-DD" strings.
    Returns a list of raw post dicts with keys matching the DB schema.
    """
    url = "https://arctic-shift.photon-reddit.com/api/posts/search"
    params = {
        "subreddit": subreddit,
        "after":     after_date,
        "before":    before_date,
        "limit":     limit,
        "sort":      "desc",
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("data", [])
    except Exception as e:
        print(f"  Arctic Shift failed for r/{subreddit}: {e}")
        return []

    posts = []
    for p in items:
        full_text = f"{p.get('title', '')} {p.get('selftext', '')}"
        posts.append({
            "post_id":      p.get("id", ""),
            "subreddit":    subreddit,
            "ticker":       extract_ticker(full_text),
            "title":        p.get("title", ""),
            "body":         (p.get("selftext", "") or "")[:2000],
            "score":        int(p.get("score", 0) or 0),
            "num_comments": int(p.get("num_comments", 0) or 0),
            # Arctic Shift returns created_utc as an integer — store as "float
            # string" to match the format already in the DB ("1777052813.0")
            "created_utc":  str(float(p.get("created_utc", 0))),
        })
    return posts


def fetch_arctic_shift_year(subreddit: str, months_back: int = 12):
    """
    Paginate Arctic Shift month by month to collect ~1 year of posts.
    Sleeping between requests to respect rate limits.
    """
    all_posts = []
    now = datetime.utcnow()

    for i in range(months_back):
        before = (now - timedelta(days=30 * i)).strftime("%Y-%m-%d")
        after  = (now - timedelta(days=30 * (i + 1))).strftime("%Y-%m-%d")
        print(f"    Arctic Shift r/{subreddit}: {after} → {before}")
        posts = fetch_arctic_shift_historical(subreddit, after, before, limit=100)
        all_posts.extend(posts)
        time.sleep(1.5)   # Arctic Shift asks for ~1 req/sec

    return all_posts


# ── Live Reddit hot.json (current posts, no auth needed) ──────────────────────

def fetch_live_hot(subreddit: str, limit: int = 100):
    """
    Fetch the current hot listing from Reddit's public JSON endpoint.
    No auth required. Kept for freshness alongside historical backfill.
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    params = {"limit": limit}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        children = resp.json()["data"]["children"]
    except Exception as e:
        print(f"  Live Reddit failed for r/{subreddit}: {e}")
        return []

    posts = []
    for child in children:
        p = child["data"]
        full_text = f"{p.get('title', '')} {p.get('selftext', '')}"
        posts.append({
            "post_id":      p["id"],
            "subreddit":    subreddit,
            "ticker":       extract_ticker(full_text),
            "title":        p.get("title", ""),
            "body":         (p.get("selftext", "") or "")[:2000],
            "score":        int(p.get("score", 0) or 0),
            "num_comments": int(p.get("num_comments", 0) or 0),
            # Match existing DB format: created_utc stored as "1777052813.0"
            "created_utc":  str(float(p.get("created_utc", 0))),
        })
    return posts


# ── Filter removed posts ──────────────────────────────────────────────────────

REMOVED_PATTERNS = {"[removed]", "[ removed by moderator ]"}

def is_removed(post: dict) -> bool:
    """Return True if Reddit scrubbed the post (title or body signals removal)."""
    title = (post.get("title") or "").strip().lower()
    body  = (post.get("body")  or "").strip().lower()
    return title in REMOVED_PATTERNS or body in REMOVED_PATTERNS


# ── DB writer ─────────────────────────────────────────────────────────────────

def store_posts(rows: list):
    """
    Insert into reddit_posts table.
    Schema: id, post_id, subreddit, ticker, title, body, score, num_comments, created_utc, fetched_at
    Dedup key: UNIQUE(post_id)
    """
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        if not r.get("post_id"):
            continue
        try:
            cur.execute("""
                INSERT OR IGNORE INTO reddit_posts
                    (post_id, subreddit, ticker, title, body,
                     score, num_comments, created_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["post_id"],
                r["subreddit"],
                r["ticker"],
                r["title"],
                r["body"],
                r["score"],
                r["num_comments"],
                r["created_utc"],
            ))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Reddit insert error: {e}")
    conn.commit()
    conn.close()
    return inserted


# ── Entry point ───────────────────────────────────────────────────────────────

def run(historical: bool = True):
    """
    historical=True  →  backfill ~12 months via Arctic Shift (slow, run once)
    historical=False →  only fetch live hot posts (fast, run on schedule)
    """
    for sub in SUBREDDITS:
        print(f"[Reddit] Scraping r/{sub}...")
        posts = []

        if historical:
            # Full year backfill via Arctic Shift
            hist = fetch_arctic_shift_year(sub, months_back=12)
            posts.extend(hist)
            print(f"  Arctic Shift: {len(hist)} historical posts")

        # Always grab live hot posts for freshness
        live = fetch_live_hot(sub)
        posts.extend(live)
        print(f"  Live hot: {len(live)} posts")

        posts = [p for p in posts if not is_removed(p)]
        n = store_posts(posts)
        print(f"  Inserted {n}/{len(posts)} posts for r/{sub}")
        time.sleep(2)


if __name__ == "__main__":
    # Pass historical=False if you just want a quick live refresh
    run(historical=True)