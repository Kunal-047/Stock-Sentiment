# ingest_prices.py
# Sources: yfinance (free, 1-year daily) + Alpha Vantage (free tier, intraday)
# DB targets:
#   ohlcv(ticker, date, open, high, low, close, volume)          UNIQUE(ticker, date)
#   intraday(ticker, timestamp, open, high, low, close, volume, interval)  UNIQUE(ticker, timestamp, interval)

import yfinance as yf
import requests
from db import get_conn
from config import TICKERS

# ── Alpha Vantage key (optional — intraday only) ──────────────────────────────
try:
    from config import ALPHA_VANTAGE_KEY
except ImportError:
    ALPHA_VANTAGE_KEY = None


# ── Yahoo Finance: Daily OHLCV ────────────────────────────────────────────────

def fetch_yfinance_daily(ticker: str, period: str = "1y"):
    """
    Fetch daily OHLCV via yfinance.
    period="1y"  →  ~252 trading-day bars, free, no API key.
    Other valid values: "5d", "1mo", "3mo", "6mo", "2y", "5y", "max"
    """
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return []

    rows = []
    for date, row in df.iterrows():
        # yfinance returns MultiIndex columns when downloading a single ticker
        # with recent versions; .iloc[0] handles both cases safely.
        def _val(col):
            v = row[col]
            try:
                return float(v.iloc[0])
            except AttributeError:
                return float(v)

        rows.append({
            "ticker": ticker,
            "date":   date.strftime("%Y-%m-%d"),
            "open":   _val("Open"),
            "high":   _val("High"),
            "low":    _val("Low"),
            "close":  _val("Close"),
            "volume": _val("Volume"),
        })
    return rows


def store_ohlcv(rows: list):
    """
    Insert into ohlcv table.
    Schema: id, ticker, date, open, high, low, close, volume, source, fetched_at
    Dedup key: UNIQUE(ticker, date)
    source column defaults to 'yfinance' in the DB schema — we don't pass it
    explicitly so the DB default is used, matching existing rows exactly.
    """
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO ohlcv
                    (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                r["ticker"],
                r["date"],
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                r["volume"],
            ))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  OHLCV insert error: {e}")
    conn.commit()
    conn.close()
    return inserted


# ── Alpha Vantage: Intraday OHLCV ─────────────────────────────────────────────

def fetch_alpha_vantage_intraday(ticker: str, interval: str = "5min"):
    """
    Fetch intraday bars from Alpha Vantage free tier.
    Free tier: 25 requests/day, compact output = last ~100 bars.
    """
    if not ALPHA_VANTAGE_KEY:
        return []

    url = "https://www.alphavantage.co/query"
    params = {
        "function":   "TIME_SERIES_INTRADAY",
        "symbol":     ticker,
        "interval":   interval,
        "outputsize": "compact",
        "apikey":     ALPHA_VANTAGE_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Alpha Vantage request failed for {ticker}: {e}")
        return []

    key = f"Time Series ({interval})"
    if key not in data:
        print(f"  AV warning for {ticker}: {data.get('Note') or data.get('Information', 'Unknown error')}")
        return []

    rows = []
    for ts, bar in data[key].items():
        rows.append({
            "ticker":    ticker,
            "timestamp": ts,
            "open":      float(bar["1. open"]),
            "high":      float(bar["2. high"]),
            "low":       float(bar["3. low"]),
            "close":     float(bar["4. close"]),
            "volume":    float(bar["5. volume"]),
            "interval":  interval,
        })
    return rows


def store_intraday(rows: list):
    """
    Insert into intraday table.
    Schema: id, ticker, timestamp, open, high, low, close, volume, interval, fetched_at
    Dedup key: UNIQUE(ticker, timestamp, interval)
    """
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO intraday
                    (ticker, timestamp, open, high, low, close, volume, interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["ticker"],
                r["timestamp"],
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                r["volume"],
                r["interval"],
            ))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Intraday insert error: {e}")
    conn.commit()
    conn.close()
    return inserted


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    for ticker in TICKERS:
        # Daily bars — full year, free
        print(f"[Prices] yfinance 1-year daily for {ticker}...")
        rows = fetch_yfinance_daily(ticker, period="1d")
        n = store_ohlcv(rows)
        print(f"  Stored {n}/{len(rows)} daily bars")

        # Intraday — Alpha Vantage free tier; skip crypto (no intraday support)
        if ALPHA_VANTAGE_KEY and not ticker.endswith("-USD"):
            print(f"[Prices] Alpha Vantage intraday for {ticker}...")
            rows = fetch_alpha_vantage_intraday(ticker)
            n = store_intraday(rows)
            print(f"  Stored {n}/{len(rows)} intraday bars")


if __name__ == "__main__":
    run()