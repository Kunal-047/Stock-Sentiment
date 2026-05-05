# ingest_prices.py
import yfinance as yf
import requests
from db import get_conn
from config import ALPHA_VANTAGE_KEY, TICKERS

# ── Yahoo Finance: Daily OHLCV ──────────────────────────────────────────────

def fetch_yfinance_daily(ticker: str, period: str = "5d"):
    """Fetch daily OHLCV for the last N days."""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return []

    rows = []

    for date, row in df.iterrows():
        rows.append({
            "ticker": ticker,
            "date":   date.strftime("%Y-%m-%d"),
            "open":   float(row["Open"].iloc[0]),
          "high":   float(row["High"].iloc[0]),
            "low":    float(row["Low"].iloc[0]),
            "close":  float(row["Close"].iloc[0]),
           "volume": float(row["Volume"].iloc[0]),
        })
    return rows

def store_ohlcv(rows: list):
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO ohlcv
                    (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (r["ticker"], r["date"], r["open"],
                  r["high"], r["low"], r["close"], r["volume"]))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  OHLCV insert error: {e}")
    conn.commit()
    conn.close()
    return inserted

# ── Alpha Vantage: Intraday OHLCV ───────────────────────────────────────────

def fetch_alpha_vantage_intraday(ticker: str, interval: str = "5min"):
    """Fetch intraday OHLCV from Alpha Vantage (compact = last ~100 bars)."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function":   "TIME_SERIES_INTRADAY",
        "symbol":     ticker,
        "interval":   interval,
        "outputsize": "compact",
        "apikey":     ALPHA_VANTAGE_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

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
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for r in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO intraday
                    (ticker, timestamp, open, high, low, close, volume, interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["ticker"], r["timestamp"], r["open"],
                  r["high"], r["low"], r["close"], r["volume"], r["interval"]))
            inserted += cur.rowcount
        except Exception as e:
            print(f"  Intraday insert error: {e}")
    conn.commit()
    conn.close()
    return inserted

def run():
    for ticker in TICKERS:
        print(f"[Prices] yfinance daily for {ticker}...")
        rows = fetch_yfinance_daily(ticker)
        n = store_ohlcv(rows)
        print(f"  Stored {n} daily bars")

        # Alpha Vantage free tier: 25 req/day — skip crypto tickers
        if not ticker.endswith("-USD"):
            print(f"[Prices] Alpha Vantage intraday for {ticker}...")
            rows = fetch_alpha_vantage_intraday(ticker)
            n = store_intraday(rows)
            print(f"  Stored {n} intraday bars")

if __name__ == "__main__":
    run()