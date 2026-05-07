# db.py — Schema setup for SQLite (drop-in replaceable with PostgreSQL)
import sqlite3
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS headlines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,          -- 'newsapi' | 'gnews'
            ticker      TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT,
            url         TEXT UNIQUE,
            published_at TEXT NOT NULL,         -- ISO 8601
            fetched_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ohlcv (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker     TEXT NOT NULL,
            date       TEXT NOT NULL,           -- YYYY-MM-DD
            open       REAL,
            high       REAL,
            low        REAL,
            close      REAL,
            volume     REAL,
            source     TEXT DEFAULT 'yfinance',
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(ticker, date)
        );

        CREATE TABLE IF NOT EXISTS intraday (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker     TEXT NOT NULL,
            timestamp  TEXT NOT NULL,           -- ISO 8601
            open       REAL,
            high       REAL,
            low        REAL,
            close      REAL,
            volume     REAL,
            interval   TEXT DEFAULT '5min',
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(ticker, timestamp, interval)
        );

        CREATE TABLE IF NOT EXISTS reddit_posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id     TEXT UNIQUE NOT NULL,
            subreddit   TEXT NOT NULL,
            ticker      TEXT,                   -- NULL if no ticker matched
            title       TEXT,
            body        TEXT,
            score       INTEGER,
            num_comments INTEGER,
            created_utc TEXT NOT NULL,
            fetched_at  TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()
    print("DB initialized.")

if __name__ == "__main__":
    init_db()