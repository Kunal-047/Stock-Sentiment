"""
main.py — Phase 4 Serving Layer  |  Stock Sentiment Analyzer
FastAPI backend exposing prediction + sentiment endpoints.

Endpoints:
    GET  /predict/{ticker}    → latest prediction + confidence + SHAP
    GET  /sentiment/{ticker}  → last 7 days sentiment trend
    GET  /history/{ticker}    → historical OHLCV + predictions
    POST /retrain             → trigger Phase 3 retraining (admin)
    GET  /health              → pipeline status + last ingest time

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Environment variables (or edit CONFIG below):
    DB_PATH            path to market_data.db
    MODEL_PATH         path to champion_model.pkl
    RETRAIN_SCRIPT     path to retrain script (optional)
    ADMIN_TOKEN        bearer token for POST /retrain (optional)
"""

import os
import subprocess
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import model as champion
import features as feat

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG = {
    "db_path":        os.getenv("DB_PATH",        "market_data.db"),
    "model_path":     os.getenv("MODEL_PATH",     "champion_model.pkl"),
    "retrain_script": os.getenv("RETRAIN_SCRIPT", ""),
    "admin_token":    os.getenv("ADMIN_TOKEN",    ""),
}

SUPPORTED_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "BTC-USD"]

_startup_time = datetime.now(timezone.utc).isoformat()
_model_loaded = False


# ── Lifespan: load model once at startup ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model_loaded
    try:
        champion.load_model(CONFIG["model_path"])
        _model_loaded = True
    except FileNotFoundError as e:
        print(f"[startup] ⚠️  {e}")
        print("[startup]    API will start but /predict will return 503 until model is present.")
        _model_loaded = False
    yield


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Stock Sentiment Analyzer — Serving API",
    description=(
        "Phase 4 of the Stock Sentiment Analyzer portfolio project. "
        "Serves predictions from the Phase 3 champion model (XGBoost) "
        "using features engineered from OHLCV + FinBERT-scored news "
        "(Phase 2 output)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your Vercel domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _require_model():
    if not _model_loaded or not champion.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=(
                "Champion model not loaded. "
                "Copy champion_model.pkl to the API root and restart."
            ),
        )


def _validate_ticker(ticker: str) -> str:
    t = ticker.upper()
    if t not in SUPPORTED_TICKERS:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{t}' not supported. Supported: {SUPPORTED_TICKERS}",
        )
    return t


def _check_admin(request: Request):
    token = CONFIG["admin_token"]
    if not token:
        return  # no auth configured — open
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Invalid admin token.")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    """
    Pipeline status check.
    Returns model load status, last ingest timestamp, and uptime.
    """
    last_ingest = feat.get_last_ingest_time(CONFIG["db_path"])
    return {
        "status":        "ok",
        "model_loaded":  _model_loaded,
        "model_path":    champion.get_model_path(),
        "last_ingest":   last_ingest,
        "startup_time":  _startup_time,
        "db_path":       CONFIG["db_path"],
        "supported_tickers": SUPPORTED_TICKERS,
    }


@app.get("/predict/{ticker}", tags=["prediction"])
def predict(ticker: str):
    """
    Latest prediction for a ticker.

    Returns:
    - **prediction**: Up / Flat / Down
    - **confidence**: model's max class probability (0–1)
    - **probabilities**: per-class breakdown
    - **sentiment_score**: net sentiment of the latest day (positive − negative)
    - **top_headline**: most recent news headline from DB
    - **feature_contributions**: top-10 SHAP values driving this prediction
    - **feature_date**: the trading date the features were built from
    """
    _require_model()
    t = _validate_ticker(ticker)

    try:
        latest  = feat.get_latest_feature_row(t, CONFIG["db_path"])
        feature_dict = latest["features"]
        feature_date = latest["date"]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {e}")

    try:
        result = champion.predict(feature_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {e}")

    try:
        shap_vals = champion.shap_contributions(feature_dict, top_n=10)
    except Exception as e:
        shap_vals = []  # SHAP is best-effort; don't fail the whole request
        print(f"[predict] SHAP failed for {t}: {e}")

    top_headline = feat.get_top_headline(t, CONFIG["db_path"])

    return {
        "ticker":               t,
        "feature_date":         feature_date,
        "prediction":           result["prediction"],
        "predicted_class":      result["predicted_class"],
        "confidence":           round(result["confidence"], 4),
        "probabilities":        {k: round(v, 4) for k, v in result["probabilities"].items()},
        "sentiment_score":      round(feature_dict.get("mean_sentiment", 0.0), 4),
        "top_headline":         top_headline,
        "feature_contributions": shap_vals,
    }


@app.get("/sentiment/{ticker}", tags=["sentiment"])
def sentiment(ticker: str, days: int = 7):
    """
    Sentiment trend for the last N days (default 7).

    Each row contains: date, mean_sentiment, sentiment_volatility,
    headline_volume, negative_spike_flag, mean_positive, mean_negative, mean_neutral.
    """
    t = _validate_ticker(ticker)
    if not 1 <= days <= 90:
        raise HTTPException(status_code=400, detail="'days' must be between 1 and 90.")

    try:
        trend = feat.get_sentiment_trend(t, CONFIG["db_path"], days=days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "ticker":   t,
        "days":     days,
        "trend":    trend,
    }


@app.get("/history/{ticker}", tags=["history"])
def history(ticker: str):
    """
    Historical OHLCV data for a ticker.

    In a production setup this would be joined with stored predictions
    and actuals to show prediction accuracy over time.  Phase 4 returns
    raw OHLCV; wire in a predictions table once the ingest loop persists
    daily predictions.
    """
    t = _validate_ticker(ticker)

    try:
        rows = feat.get_ohlcv_history(t, CONFIG["db_path"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        raise HTTPException(status_code=404, detail=f"No history found for '{t}'.")

    return {
        "ticker":  t,
        "count":   len(rows),
        "history": rows,
        "note": (
            "Prediction vs actual overlay will be available once the daily "
            "ingest pipeline persists model outputs to a predictions table."
        ),
    }


@app.post("/retrain", tags=["ops"])
def retrain(request: Request):
    """
    Trigger Phase 3 retraining (admin only).

    Kicks off the retrain script defined in RETRAIN_SCRIPT env var.
    Returns immediately with a job acknowledgement — does not block.

    Requires Authorization: Bearer <ADMIN_TOKEN> if ADMIN_TOKEN is set.
    """
    _check_admin(request)

    script = CONFIG["retrain_script"]
    if not script:
        return JSONResponse(
            status_code=200,
            content={
                "status":  "noop",
                "message": (
                    "No RETRAIN_SCRIPT configured. "
                    "Set the RETRAIN_SCRIPT env var to the path of your Phase 3 runner."
                ),
            },
        )

    import shutil
    if not shutil.which("python3") and not os.path.exists(script):
        raise HTTPException(status_code=500, detail=f"Retrain script not found: {script}")

    try:
        proc = subprocess.Popen(
            ["python3", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return {
            "status":  "triggered",
            "pid":     proc.pid,
            "script":  script,
            "message": "Retraining started in background. Restart the API after it completes to load the new champion model.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch retrain: {e}")


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
