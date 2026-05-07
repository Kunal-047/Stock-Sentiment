"""
Stock Sentiment Analyzer — Portfolio Dashboard
Author: Divyam
Stack: FastAPI · FinBERT · PostgreSQL · Redis · React · Docker
"""

import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Sentiment Alpha · Portfolio",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# THEME / CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap');

  /* ── Root variables ── */
  :root {
    --bg:       #08090d;
    --surface:  #0f1117;
    --card:     #141720;
    --border:   #1e2130;
    --accent:   #4fffb0;
    --accent2:  #7c6bff;
    --danger:   #ff4f6b;
    --warn:     #ffb84f;
    --text:     #e4e7f0;
    --muted:    #5c617a;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }

  /* ── Global resets ── */
  html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] * { font-family: var(--font-mono) !important; }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
  }
  [data-testid="metric-container"] label {
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-head) !important;
    font-weight: 700;
    font-size: 1.8rem !important;
    color: var(--text) !important;
  }

  /* ── Section headers ── */
  .section-label {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 2rem 0 0.5rem;
  }
  .section-title {
    font-family: var(--font-head);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 1rem;
  }

  /* ── Hero banner ── */
  .hero {
    background: linear-gradient(135deg, #0f1117 0%, #141720 60%, #0d1a14 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(79,255,176,0.08) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title {
    font-family: var(--font-head);
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 0.4rem;
    letter-spacing: -0.02em;
  }
  .hero-title span { color: var(--accent); }
  .hero-sub {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--muted);
    margin: 0 0 1.2rem;
  }
  .tech-badge {
    display: inline-block;
    background: rgba(79,255,176,0.06);
    border: 1px solid rgba(79,255,176,0.18);
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    padding: 3px 10px;
    border-radius: 4px;
    margin: 0 4px 4px 0;
    text-transform: uppercase;
  }

  /* ── Cards ── */
  .info-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    height: 100%;
  }
  .info-card-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.3rem;
  }
  .info-card-value {
    font-family: var(--font-head);
    font-size: 1.6rem;
    font-weight: 700;
  }
  .positive { color: var(--accent); }
  .negative { color: var(--danger); }
  .neutral  { color: var(--warn); }

  /* ── Pipeline diagram ── */
  .pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 1rem 0;
    flex-wrap: wrap;
  }
  .pipe-step {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: var(--text);
    white-space: nowrap;
  }
  .pipe-arrow {
    color: var(--muted);
    margin: 0 6px;
    font-size: 0.9rem;
  }

  /* ── Headline cards ── */
  .headline-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    line-height: 1.5;
  }
  .headline-card.neg { border-left-color: var(--danger); }
  .headline-card .source-tag {
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.3rem;
  }
  .headline-card .title-text {
    color: var(--text);
    font-size: 0.8rem;
  }
  .headline-card .ts {
    font-size: 0.65rem;
    color: var(--muted);
    margin-top: 0.25rem;
  }

  /* ── Selectbox / widgets ── */
  .stSelectbox > div > div {
    background: var(--card) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
  }
  .stSlider > div > div { color: var(--accent) !important; }

  /* ── Divider ── */
  hr { border-color: var(--border); opacity: 1; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────
DB_PATH  = os.path.join(os.path.dirname(__file__), "market_data.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "feature_matrix.csv")

@st.cache_data(ttl=300)
def load_data():
    con = sqlite3.connect(DB_PATH)

    ohlcv     = pd.read_sql("SELECT * FROM ohlcv ORDER BY ticker, date",     con)
    headlines = pd.read_sql("SELECT * FROM headlines ORDER BY published_at DESC", con)
    reddit    = pd.read_sql("SELECT * FROM reddit_posts ORDER BY created_utc DESC", con)
    con.close()

    ohlcv["date"]     = pd.to_datetime(ohlcv["date"])
    headlines["published_at"] = pd.to_datetime(headlines["published_at"], utc=True, errors="coerce")

    feat = pd.read_csv(CSV_PATH)
    feat["date"] = pd.to_datetime(feat["date"], dayfirst=True, errors="coerce")

    return ohlcv, headlines, reddit, feat

ohlcv, headlines, reddit, feat = load_data()
TICKERS = sorted(ohlcv["ticker"].unique().tolist())

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⬡ &nbsp;Sentiment Alpha")
    st.markdown('<div style="font-size:0.7rem;color:#5c617a;margin-bottom:1.5rem;">Stock Sentiment Analyzer · Portfolio Build</div>', unsafe_allow_html=True)

    ticker = st.selectbox("Asset", TICKERS, index=0)
    st.markdown("---")

    st.markdown('<div style="font-size:0.68rem;letter-spacing:0.12em;text-transform:uppercase;color:#5c617a;margin-bottom:0.4rem;">Date Window</div>', unsafe_allow_html=True)
    t_ohlcv = ohlcv[ohlcv["ticker"] == ticker]
    min_d = t_ohlcv["date"].min().date()
    max_d = t_ohlcv["date"].max().date()
    date_range = st.slider(
        "Range", min_value=min_d, max_value=max_d,
        value=(max_d - timedelta(days=90), max_d),
        label_visibility="collapsed",
    )
    st.markdown("---")

    st.markdown('<div style="font-size:0.68rem;letter-spacing:0.12em;text-transform:uppercase;color:#5c617a;margin-bottom:0.5rem;">Pipeline</div>', unsafe_allow_html=True)
    for step in ["GNews API", "Reddit PRAW", "FinBERT NLP", "Feature Matrix", "ML Model", "FastAPI", "React UI"]:
        st.markdown(f'<div style="font-size:0.72rem;padding:3px 0;color:#e4e7f0;">↳ {step}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="font-size:0.65rem;color:#5c617a;">Data via yfinance · gnews · PRAW<br>Model: FinBERT (HuggingFace)</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FILTER DATA BY TICKER + WINDOW
# ──────────────────────────────────────────────
d_start = pd.Timestamp(date_range[0])
d_end   = pd.Timestamp(date_range[1])

t_ohlcv = ohlcv[(ohlcv["ticker"] == ticker) & (ohlcv["date"] >= d_start) & (ohlcv["date"] <= d_end)].copy()
t_feat  = feat[(feat["ticker"] == ticker)  & (feat["date"]  >= d_start) & (feat["date"]  <= d_end)].copy()
t_news  = headlines[headlines["ticker"] == ticker].copy()

# ──────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────
last_close  = t_ohlcv["close"].iloc[-1]  if len(t_ohlcv) else 0
prev_close  = t_ohlcv["close"].iloc[-2]  if len(t_ohlcv) > 1 else last_close
pct_chg     = (last_close - prev_close) / prev_close * 100 if prev_close else 0
chg_color   = "#4fffb0" if pct_chg >= 0 else "#ff4f6b"
chg_arrow   = "▲" if pct_chg >= 0 else "▼"

sentiment_label = "NEUTRAL"
sentiment_color = "#ffb84f"
if len(t_feat) and t_feat["mean_sentiment"].notna().any():
    avg_sent = t_feat["mean_sentiment"].mean()
    if avg_sent > 0.1:
        sentiment_label, sentiment_color = "BULLISH", "#4fffb0"
    elif avg_sent < -0.1:
        sentiment_label, sentiment_color = "BEARISH", "#ff4f6b"

st.markdown(f"""
<div class="hero">
  <div class="hero-title">Sentiment <span>Alpha</span></div>
  <div class="hero-sub">NLP-Driven Market Intelligence Pipeline · {ticker}</div>
  <div>
    <span class="tech-badge">FastAPI</span>
    <span class="tech-badge">FinBERT</span>
    <span class="tech-badge">HuggingFace</span>
    <span class="tech-badge">PostgreSQL</span>
    <span class="tech-badge">Redis</span>
    <span class="tech-badge">Docker</span>
    <span class="tech-badge">React</span>
    <span class="tech-badge">Streamlit</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# KPI ROW
# ──────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric("Last Close", f"${last_close:,.2f}", f"{chg_arrow} {pct_chg:+.2f}%")
with k2:
    rsi_val = t_feat["RSI_14"].dropna().iloc[-1] if (len(t_feat) and t_feat["RSI_14"].notna().any()) else 0
    rsi_delta = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
    st.metric("RSI (14)", f"{rsi_val:.1f}", rsi_delta)
with k3:
    n_headlines = len(t_news)
    st.metric("News Headlines", n_headlines, "from GNews API")
with k4:
    n_reddit = len(reddit[reddit["ticker"].isin([ticker, ticker.replace("-USD", "")])])
    st.metric("Reddit Posts", f"{n_reddit:,}", "r/wsb · r/stocks · r/crypto")
with k5:
    win_rate = (t_feat["price_direction"] == 1).mean() * 100 if len(t_feat) else 0
    st.metric("Bullish Days", f"{win_rate:.0f}%", f"of {len(t_feat)} trading days")

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CHART 1 — Price + Volume
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">01 — OHLCV</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Price & Volume</div>', unsafe_allow_html=True)

if len(t_ohlcv):
    fig_price = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.04,
    )

    # Candlestick
    fig_price.add_trace(go.Candlestick(
        x=t_ohlcv["date"],
        open=t_ohlcv["open"], high=t_ohlcv["high"],
        low=t_ohlcv["low"],   close=t_ohlcv["close"],
        increasing_line_color="#4fffb0", decreasing_line_color="#ff4f6b",
        increasing_fillcolor="rgba(79,255,176,0.15)",
        decreasing_fillcolor="rgba(255,79,107,0.15)",
        name="OHLC",
    ), row=1, col=1)

    # SMAs from feature matrix if available
    for sma_col, sma_color, sma_label in [
        ("SMA_5",  "#7c6bff", "SMA 5"),
        ("SMA_20", "#ffb84f", "SMA 20"),
    ]:
        if sma_col in t_feat.columns and t_feat[sma_col].notna().any():
            merged = t_ohlcv[["date"]].merge(t_feat[["date", sma_col]], on="date", how="left")
            fig_price.add_trace(go.Scatter(
                x=merged["date"], y=merged[sma_col],
                mode="lines", line=dict(color=sma_color, width=1.2, dash="dot"),
                name=sma_label, opacity=0.8,
            ), row=1, col=1)

    # Volume bars
    vol_colors = ["rgba(79,255,176,0.5)" if c >= o else "rgba(255,79,107,0.5)"
                  for c, o in zip(t_ohlcv["close"], t_ohlcv["open"])]
    fig_price.add_trace(go.Bar(
        x=t_ohlcv["date"], y=t_ohlcv["volume"],
        marker_color=vol_colors, name="Volume", showlegend=False,
    ), row=2, col=1)

    fig_price.update_layout(
        height=480,
        paper_bgcolor="#08090d", plot_bgcolor="#0f1117",
        font=dict(family="DM Mono, monospace", color="#5c617a", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e7f0", size=10)),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    for axis in ["xaxis", "yaxis", "xaxis2", "yaxis2"]:
        fig_price.update_layout(**{
            axis: dict(
                gridcolor="#1e2130", zerolinecolor="#1e2130",
                color="#5c617a",
            )
        })

    st.plotly_chart(fig_price, use_container_width=True)
else:
    st.info("No OHLCV data for selected window.")

# ──────────────────────────────────────────────
# CHART 2 — Sentiment Over Time
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">02 — FINBERT OUTPUT</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Sentiment Score Timeline</div>', unsafe_allow_html=True)

if len(t_feat) and t_feat["mean_sentiment"].notna().any():
    sent_df = t_feat.dropna(subset=["mean_sentiment"]).copy()

    fig_sent = go.Figure()

    # Zero line fill
    fig_sent.add_hline(y=0, line_color="#1e2130", line_width=1)

    # Positive / negative area
    fig_sent.add_trace(go.Scatter(
        x=sent_df["date"], y=sent_df["mean_sentiment"].clip(lower=0),
        fill="tozeroy", mode="none",
        fillcolor="rgba(79,255,176,0.12)", name="Bullish",
    ))
    fig_sent.add_trace(go.Scatter(
        x=sent_df["date"], y=sent_df["mean_sentiment"].clip(upper=0),
        fill="tozeroy", mode="none",
        fillcolor="rgba(255,79,107,0.12)", name="Bearish",
    ))

    # Line
    fig_sent.add_trace(go.Scatter(
        x=sent_df["date"], y=sent_df["mean_sentiment"],
        mode="lines", line=dict(color="#4fffb0", width=1.8),
        name="Mean Sentiment",
    ))

    # Negative spike flags
    spikes = sent_df[sent_df["negative_spike_flag"] == 1]
    if len(spikes):
        fig_sent.add_trace(go.Scatter(
            x=spikes["date"], y=spikes["mean_sentiment"],
            mode="markers",
            marker=dict(symbol="triangle-down", color="#ff4f6b", size=10),
            name="Neg. Spike",
        ))

    fig_sent.update_layout(
        height=280,
        paper_bgcolor="#08090d", plot_bgcolor="#0f1117",
        font=dict(family="DM Mono, monospace", color="#5c617a", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e7f0", size=10),
                    orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(gridcolor="#1e2130", color="#5c617a"),
        yaxis=dict(gridcolor="#1e2130", color="#5c617a", title="Score"),
    )
    st.plotly_chart(fig_sent, use_container_width=True)
else:
    st.info("Sentiment data not yet scored. Run the FinBERT pipeline to populate this view.")

# ──────────────────────────────────────────────
# CHART 3 — Technical Indicators (RSI + MACD + Bollinger)
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">03 — FEATURE MATRIX</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Technical Indicators</div>', unsafe_allow_html=True)

if len(t_feat) and t_feat["RSI_14"].notna().any():
    fig_tech = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.38, 0.32, 0.30],
        vertical_spacing=0.05,
        subplot_titles=["RSI (14)", "MACD (12·26·9)", "Bollinger Bands"],
    )
    # Update subplot title colors
    for ann in fig_tech.layout.annotations:
        ann.font.color = "#5c617a"
        ann.font.size = 10
        ann.font.family = "DM Mono, monospace"

    tf = t_feat.dropna(subset=["RSI_14"])

    # RSI
    fig_tech.add_trace(go.Scatter(
        x=tf["date"], y=tf["RSI_14"],
        mode="lines", line=dict(color="#7c6bff", width=1.5), name="RSI",
    ), row=1, col=1)
    fig_tech.add_hrect(y0=70, y1=100, fillcolor="rgba(255,79,107,0.07)", line_width=0, row=1, col=1)
    fig_tech.add_hrect(y0=0,  y1=30,  fillcolor="rgba(79,255,176,0.07)", line_width=0, row=1, col=1)
    fig_tech.add_hline(y=70, line_dash="dot", line_color="#ff4f6b", line_width=0.8, row=1, col=1)
    fig_tech.add_hline(y=30, line_dash="dot", line_color="#4fffb0", line_width=0.8, row=1, col=1)

    # MACD
    if "MACD_12_26_9" in tf.columns:
        fig_tech.add_trace(go.Scatter(
            x=tf["date"], y=tf["MACD_12_26_9"],
            mode="lines", line=dict(color="#4fffb0", width=1.4), name="MACD",
        ), row=2, col=1)
        fig_tech.add_trace(go.Scatter(
            x=tf["date"], y=tf["MACDs_12_26_9"],
            mode="lines", line=dict(color="#ffb84f", width=1.2, dash="dot"), name="Signal",
        ), row=2, col=1)
        bar_colors = ["rgba(79,255,176,0.6)" if v >= 0 else "rgba(255,79,107,0.6)"
                      for v in tf["MACDh_12_26_9"].fillna(0)]
        fig_tech.add_trace(go.Bar(
            x=tf["date"], y=tf["MACDh_12_26_9"],
            marker_color=bar_colors, name="Histogram", showlegend=False,
        ), row=2, col=1)

    # Bollinger Bands
    for col in ["BBL_20_2.0", "BBM_20_2.0", "BBU_20_2.0"]:
        if col not in tf.columns: continue
    if all(c in tf.columns for c in ["BBL_20_2.0", "BBU_20_2.0", "BBM_20_2.0"]):
        fig_tech.add_trace(go.Scatter(
            x=pd.concat([tf["date"], tf["date"][::-1]]),
            y=pd.concat([tf["BBU_20_2.0"], tf["BBL_20_2.0"][::-1]]),
            fill="toself", fillcolor="rgba(124,107,255,0.07)",
            line=dict(color="rgba(0,0,0,0)"), name="BB Band", showlegend=True,
        ), row=3, col=1)
        fig_tech.add_trace(go.Scatter(
            x=tf["date"], y=tf["BBM_20_2.0"],
            mode="lines", line=dict(color="#7c6bff", width=1.2, dash="dot"), name="BB Mid",
        ), row=3, col=1)
        # Price on BB chart
        merged_bb = t_ohlcv[["date", "close"]].merge(tf[["date"]], on="date", how="inner")
        fig_tech.add_trace(go.Scatter(
            x=merged_bb["date"], y=merged_bb["close"],
            mode="lines", line=dict(color="#e4e7f0", width=1.2), name="Price",
        ), row=3, col=1)

    fig_tech.update_layout(
        height=520,
        paper_bgcolor="#08090d", plot_bgcolor="#0f1117",
        font=dict(family="DM Mono, monospace", color="#5c617a", size=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e7f0", size=9),
                    orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
    )
    for axis in ["xaxis", "yaxis", "xaxis2", "yaxis2", "xaxis3", "yaxis3"]:
        fig_tech.update_layout(**{axis: dict(gridcolor="#1e2130", color="#5c617a")})

    st.plotly_chart(fig_tech, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 4 — Sentiment Breakdown Pie + Scatter
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">04 — SENTIMENT DISTRIBUTION</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Positive · Neutral · Negative Split</div>', unsafe_allow_html=True)

col_pie, col_scatter = st.columns([1, 2])

with col_pie:
    if len(t_feat) and all(c in t_feat.columns for c in ["mean_positive", "mean_neutral", "mean_negative"]):
        totals = t_feat[["mean_positive", "mean_neutral", "mean_negative"]].mean()
        fig_pie = go.Figure(go.Pie(
            labels=["Positive", "Neutral", "Negative"],
            values=totals.values,
            hole=0.55,
            marker=dict(colors=["#4fffb0", "#ffb84f", "#ff4f6b"],
                        line=dict(color="#08090d", width=2)),
            textfont=dict(family="DM Mono, monospace", size=10, color="#e4e7f0"),
        ))
        fig_pie.update_layout(
            height=260,
            paper_bgcolor="#08090d", plot_bgcolor="#08090d",
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e7f0", size=10)),
            margin=dict(l=0, r=0, t=10, b=10),
            annotations=[dict(
                text=ticker, x=0.5, y=0.5, font_size=16,
                font_family="Syne, sans-serif", font_color="#e4e7f0",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with col_scatter:
    if len(t_feat) and t_feat["mean_sentiment"].notna().any():
        scatter_df = t_ohlcv[["date", "close", "volume"]].merge(
            t_feat[["date", "mean_sentiment", "price_direction"]], on="date", how="inner"
        ).dropna()
        if len(scatter_df):
            color_map = {1: "#4fffb0", 0: "#ffb84f", -1: "#ff4f6b"}
            scatter_df["color"] = scatter_df["price_direction"].map(color_map).fillna("#5c617a")

            fig_sc = go.Figure()
            for direction, label, color in [(1, "Up", "#4fffb0"), (0, "Flat", "#ffb84f"), (-1, "Down", "#ff4f6b")]:
                sub = scatter_df[scatter_df["price_direction"] == direction]
                if len(sub):
                    fig_sc.add_trace(go.Scatter(
                        x=sub["mean_sentiment"], y=sub["close"],
                        mode="markers",
                        marker=dict(color=color, size=7, opacity=0.7,
                                    line=dict(color=color, width=0.5)),
                        name=label,
                    ))

            fig_sc.update_layout(
                height=260,
                paper_bgcolor="#08090d", plot_bgcolor="#0f1117",
                font=dict(family="DM Mono, monospace", color="#5c617a", size=10),
                xaxis=dict(title="Sentiment Score", gridcolor="#1e2130", color="#5c617a"),
                yaxis=dict(title="Close Price", gridcolor="#1e2130", color="#5c617a"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e7f0", size=10)),
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

# ──────────────────────────────────────────────
# NEWS HEADLINES
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">05 — LIVE NEWS FEED</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Latest Headlines</div>', unsafe_allow_html=True)

if len(t_news):
    display_news = t_news.head(8)
    for _, row in display_news.iterrows():
        card_class = "headline-card"
        ts_str = row["published_at"].strftime("%b %d, %Y  %H:%M UTC") if pd.notna(row["published_at"]) else ""
        url_part = f'<a href="{row["url"]}" target="_blank" style="color:#5c617a;font-size:0.65rem;">↗ Read more</a>' if row.get("url") else ""
        st.markdown(f"""
        <div class="{card_class}">
          <div class="source-tag">⬡ {row['source'].upper()} · {ticker}</div>
          <div class="title-text">{row['title']}</div>
          <div class="ts">{ts_str} &nbsp; {url_part}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No headlines fetched for this ticker yet.")

# ──────────────────────────────────────────────
# REDDIT SAMPLE
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">06 — SOCIAL SIGNAL</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Reddit Pulse</div>', unsafe_allow_html=True)

ticker_base = ticker.replace("-USD", "")
r_filtered  = reddit[reddit["ticker"].isin([ticker, ticker_base]) & reddit["title"].notna()].head(6)

if len(r_filtered):
    rcol1, rcol2 = st.columns(2)
    for i, (_, row) in enumerate(r_filtered.iterrows()):
        col = rcol1 if i % 2 == 0 else rcol2
        score = int(row["score"]) if pd.notna(row["score"]) else 0
        comments = int(row["num_comments"]) if pd.notna(row["num_comments"]) else 0
        title_text = str(row["title"])[:120] + ("…" if len(str(row["title"])) > 120 else "")
        col.markdown(f"""
        <div class="headline-card" style="border-left-color:#7c6bff;">
          <div class="source-tag">r/{row['subreddit']} · ▲ {score} · 💬 {comments}</div>
          <div class="title-text">{title_text}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No tagged Reddit posts for this ticker.")

# ──────────────────────────────────────────────
# PIPELINE DIAGRAM
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">07 — ARCHITECTURE</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">End-to-End Pipeline</div>', unsafe_allow_html=True)

st.markdown("""
<div class="pipeline">
  <div class="pipe-step">GNews API</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">Reddit PRAW</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">SQLite / PostgreSQL</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">Jupyter Notebook</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">FinBERT NLP</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">Feature Matrix CSV</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">ML Classifier</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">FastAPI</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">Redis Cache</div><div class="pipe-arrow">→</div>
  <div class="pipe-step">React Dashboard</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# RAW DATA EXPANDERS
# ──────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🗄️  Raw OHLCV Table"):
    st.dataframe(
        t_ohlcv[["date","open","high","low","close","volume"]].sort_values("date", ascending=False),
        use_container_width=True, height=300,
    )

with st.expander("🧬  Feature Matrix (Sentiment + Technicals)"):
    display_cols = [c for c in t_feat.columns if c not in ["id"]]
    st.dataframe(t_feat[display_cols].sort_values("date", ascending=False), use_container_width=True, height=300)

with st.expander("📰  Full Headlines"):
    st.dataframe(
        t_news[["published_at","source","title","url"]].sort_values("published_at", ascending=False),
        use_container_width=True, height=300,
    )

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;">
  <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#5c617a;">
    Sentiment Alpha · Portfolio Project · Built with FastAPI · FinBERT · Streamlit
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#5c617a;">
    Data: yfinance · GNews · PRAW &nbsp;|&nbsp; Model: ProsusAI/finbert
  </div>
</div>
""", unsafe_allow_html=True)