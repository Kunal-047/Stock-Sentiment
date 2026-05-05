"""
features.py — Phase 4 Serving Layer
Reconstructs the 23-feature vector from market_data.db at request time.
Mirrors Phase 2 logic exactly: same column names, same indicator math.
"""

import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Feature column order MUST match Phase 3 training exactly ─────────────────
FEATURE_COLS = [
    "mean_sentiment", "sentiment_volatility", "headline_volume",
    "negative_spike_flag", "mean_positive", "mean_negative", "mean_neutral",
    "RSI_14",
    "MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9",
    "BBL_20_2.0", "BBM_20_2.0", "BBU_20_2.0", "BBB_20_2.0", "BBP_20_2.0",
    "SMA_5", "SMA_10", "SMA_20",
    "close", "volume", "volume_delta", "overnight_gap", "earnings_proximity",
]

LABEL_MAP = {0: "Down", 1: "Flat", 2: "Up"}   # encoded label → human label
# LabelEncoder fitted on [-1, 0, 1] → classes_ = [-1, 0, 1] → encoded [0, 1, 2]


# ── Technical indicator helpers (pure NumPy/pandas — matches Phase 2) ─────────

def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast    = close.ewm(span=fast,   adjust=False).mean()
    ema_slow    = close.ewm(span=slow,   adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({
        "MACD_12_26_9":  macd_line,
        "MACDs_12_26_9": signal_line,
        "MACDh_12_26_9": macd_line - signal_line,
    })


def _bbands(close: pd.Series, length=20, std=2.0) -> pd.DataFrame:
    mid   = close.rolling(length).mean()
    sigma = close.rolling(length).std(ddof=0)
    upper = mid + std * sigma
    lower = mid - std * sigma
    tag   = f"{length}_{std}"
    return pd.DataFrame({
        f"BBL_{tag}": lower,
        f"BBM_{tag}": mid,
        f"BBU_{tag}": upper,
        f"BBB_{tag}": (upper - lower) / mid.replace(0, np.nan),
        f"BBP_{tag}": (close - lower) / (upper - lower).replace(0, np.nan),
    })


# ── Sentiment aggregation from DB (pre-scored by Phase 2 / ingest pipeline) ──

def _sentiment_from_db(conn: sqlite3.Connection, ticker: str) -> pd.DataFrame:
    """
    Reads pre-scored headlines + reddit posts from DB and aggregates to
    daily sentiment features.  FinBERT scores must already be in the DB
    (written by Phase 2).  If they're absent we fall back to neutral zeros.

    NOTE: DB currently stores raw text, not FinBERT scores.
    Phase 2 runs FinBERT offline and writes feature_matrix.csv.
    Until the ingest pipeline is wired to write scores back to the DB,
    this function returns neutral-fill rows keyed by ohlcv dates so the
    feature vector is always complete.
    """
    # Try to read a sentiment_scores table written by a future ingest step
    try:
        sent = pd.read_sql(
            """
            SELECT date, mean_sentiment, sentiment_volatility, headline_volume,
                   negative_spike_flag, mean_positive, mean_negative, mean_neutral
            FROM sentiment_scores
            WHERE ticker = ?
            ORDER BY date
            """,
            conn, params=(ticker,)
        )
        if not sent.empty:
            return sent
    except Exception:
        pass

    # Fallback: neutral zeros (same fill Phase 2 uses for days with no news)
    return pd.DataFrame(columns=[
        "date", "mean_sentiment", "sentiment_volatility", "headline_volume",
        "negative_spike_flag", "mean_positive", "mean_negative", "mean_neutral",
    ])


# ── Main feature builder ───────────────────────────────────────────────────────

def build_feature_vector(ticker: str, db_path: str) -> pd.DataFrame:
    """
    Returns a DataFrame of shape (n_days, len(FEATURE_COLS)) for `ticker`,
    sorted ascending by date.  The last row is the most recent tradeable day.
    """
    conn = sqlite3.connect(db_path)
    try:
        ohlcv = pd.read_sql(
            "SELECT date, open, high, low, close, volume FROM ohlcv "
            "WHERE ticker = ? ORDER BY date",
            conn, params=(ticker,)
        )
        if ohlcv.empty:
            raise ValueError(f"No OHLCV data for ticker '{ticker}'")

        ohlcv["date"] = pd.to_datetime(ohlcv["date"])
        ohlcv = ohlcv.sort_values("date").reset_index(drop=True)

        # ── Technical indicators ──────────────────────────────────────────────
        ohlcv["RSI_14"] = _rsi(ohlcv["close"])

        macd_df = _macd(ohlcv["close"])
        ohlcv   = pd.concat([ohlcv, macd_df], axis=1)

        bb_df = _bbands(ohlcv["close"])
        ohlcv = pd.concat([ohlcv, bb_df], axis=1)

        ohlcv["SMA_5"]  = ohlcv["close"].rolling(5).mean()
        ohlcv["SMA_10"] = ohlcv["close"].rolling(10).mean()
        ohlcv["SMA_20"] = ohlcv["close"].rolling(20).mean()

        ohlcv["volume_delta"]  = ohlcv["volume"].pct_change()
        ohlcv["overnight_gap"] = (
            ohlcv["open"] - ohlcv["close"].shift(1)
        ) / ohlcv["close"].shift(1)
        ohlcv["earnings_proximity"] = 0  # wire in earnings dates when available

        # ── Sentiment features (from DB; neutral-fill if absent) ──────────────
        sent = _sentiment_from_db(conn, ticker)

        ohlcv["date_str"] = ohlcv["date"].dt.strftime("%Y-%m-%d")

        SENT_COLS = [
            "mean_sentiment", "sentiment_volatility", "headline_volume",
            "negative_spike_flag", "mean_positive", "mean_negative", "mean_neutral",
        ]
        SENT_DEFAULTS = {
            "mean_sentiment": 0.0, "sentiment_volatility": 0.0,
            "headline_volume": 0,  "negative_spike_flag": 0,
            "mean_positive": 0.0,  "mean_negative": 0.0, "mean_neutral": 1.0,
        }

        if not sent.empty:
            ohlcv = ohlcv.merge(
                sent.rename(columns={"date": "date_str"}),
                on="date_str", how="left"
            )
            for col, val in SENT_DEFAULTS.items():
                ohlcv[col] = ohlcv[col].fillna(val)
        else:
            for col, val in SENT_DEFAULTS.items():
                ohlcv[col] = val

        # ── Select & order columns ────────────────────────────────────────────
        available = [c for c in FEATURE_COLS if c in ohlcv.columns]
        missing   = [c for c in FEATURE_COLS if c not in ohlcv.columns]
        if missing:
            for c in missing:
                ohlcv[c] = 0.0  # safe default; log in prod

        result = ohlcv[["date_str"] + FEATURE_COLS].copy()
        result = result.rename(columns={"date_str": "date"})

        # Forward-fill then median-fill NaNs (matches Phase 3 preprocessing)
        for col in FEATURE_COLS:
            result[col] = result[col].ffill().bfill()
        result[FEATURE_COLS] = result[FEATURE_COLS].fillna(
            result[FEATURE_COLS].median()
        )

        return result

    finally:
        conn.close()


def get_latest_feature_row(ticker: str, db_path: str) -> dict:
    """Returns the most recent day's feature vector as a dict."""
    df = build_feature_vector(ticker, db_path)
    row = df.iloc[-1]
    return {"date": row["date"], "features": row[FEATURE_COLS].to_dict()}


def get_sentiment_trend(ticker: str, db_path: str, days: int = 7) -> list[dict]:
    """Returns last `days` rows of sentiment features."""
    df = build_feature_vector(ticker, db_path)
    sent_cols = [
        "mean_sentiment", "sentiment_volatility", "headline_volume",
        "negative_spike_flag", "mean_positive", "mean_negative", "mean_neutral",
    ]
    tail = df.tail(days)[["date"] + sent_cols]
    return tail.to_dict(orient="records")


def get_ohlcv_history(ticker: str, db_path: str) -> list[dict]:
    """Returns raw OHLCV rows for the /history endpoint."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql(
            "SELECT date, open, high, low, close, volume FROM ohlcv "
            "WHERE ticker = ? ORDER BY date",
            conn, params=(ticker,)
        )
        return df.to_dict(orient="records")
    finally:
        conn.close()


def get_top_headline(ticker: str, db_path: str) -> dict | None:
    """Returns the most recent headline for a ticker."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT title, description, url, published_at FROM headlines "
            "WHERE ticker = ? ORDER BY published_at DESC LIMIT 1",
            (ticker,)
        )
        row = cur.fetchone()
        if row:
            return {
                "title": row[0],
                "description": row[1],
                "url": row[2],
                "published_at": row[3],
            }
        return None
    finally:
        conn.close()


def get_last_ingest_time(db_path: str) -> str | None:
    """Returns the most recent fetched_at timestamp across all tables."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        times = []
        for table in ["headlines", "ohlcv", "reddit_posts"]:
            try:
                cur.execute(f"SELECT MAX(fetched_at) FROM {table}")
                t = cur.fetchone()[0]
                if t:
                    times.append(t)
            except Exception:
                pass
        return max(times) if times else None
    finally:
        conn.close()
