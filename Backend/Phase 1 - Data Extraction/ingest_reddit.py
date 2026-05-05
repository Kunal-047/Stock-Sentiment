# ingest_reddit.py
import requests
import re
import time
from db import get_conn
from config import TICKERS

SUBREDDITS = ["wallstreetbets", "investing", "stocks"]
POST_LIMIT  = 100
HEADERS     = {"User-Agent": "stock-sentiment-bot/1.0"}

# Build a regex to spot any tracked ticker in post text
TICKER_RE = re.compile(
    r'\b(' + '|'.join(re.escape(t.split("-")[0]) for t in TICKERS) + r')\b'
)

def extract_ticker(text: str):
    """Return first matched ticker from text, or None."""
    m = TICKER_RE.search(text or "")
    return m.group(1) if m else None

def fetch_subreddit_posts(subreddit_name: str):
    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json"
    params = {"limit": POST_LIMIT}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()

    children = resp.json()["data"]["children"]
    posts = []
    for child in children:
        p = child["data"]
        full_text = f"{p.get('title', '')} {p.get('selftext', '')}"
        posts.append({
            "post_id":      p["id"],
            "subreddit":    subreddit_name,
            "ticker":       extract_ticker(full_text),
            "title":        p.get("title", ""),
            "body":         p.get("selftext", "")[:2000],
            "score":        p.get("score", 0),
            "num_comments": p.get("num_comments", 0),
            "created_utc":  str(p.get("created_utc", "")),
        })
    return posts

def store_posts(rows: list):
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO reddit_posts
                    (post_id, subreddit, ticker, title, body,
                     score, num_comments, created_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["post_id"], r["subreddit"], r["ticker"],
                  r["title"], r["body"], r["score"],
                  r["num_comments"], r["created_utc"]))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Reddit insert error: {e}")
    conn.commit()
    conn.close()
    return inserted

def run():
    for sub in SUBREDDITS:
        print(f"[Reddit] Scraping r/{sub}...")
        posts = fetch_subreddit_posts(sub)
        n = store_posts(posts)
        print(f"  Inserted {n}/{len(posts)} posts")
        time.sleep(2)   # be polite — Reddit rate limits ~1 req/sec

if __name__ == "__main__":
    run()