"""
Stock Sentiment Analyzer — Dashboard
Powered by FinBERT · FastAPI · PostgreSQL · Redis

Run with:
    streamlit run streamlit_app.py

Expects these files in the same directory (or update the paths below):
    feature_matrix.csv
    market_data.db
"""

import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Stock Sentiment Analyzer",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── THEME / CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Dark background */
  .stApp { background-color: #0d1117; color: #e6edf3; }

  /* Sidebar */
  [data-testid="stSidebar"] {
      background-color: #161b22;
      border-right: 1px solid #30363d;
  }

  /* Metric cards */
  [data-testid="metric-container"] {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 14px 18px;
  }
  [data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.78rem; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #e6edf3; }

  /* Section headers */
  h2, h3 { color: #58a6ff; }

  /* Tab styling */
  .stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 8px; }
  .stTabs [data-baseweb="tab"] { color: #8b949e; }
  .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #58a6ff; border-bottom: 2px solid #58a6ff; }

  /* DataFrame */
  [data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 8px; }

  /* Divider */
  hr { border-color: #30363d; }

  /* News card */
  .news-card {
      background: #161b22;
      border: 1px solid #30363d;
      border-left: 3px solid #58a6ff;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 10px;
  }
  .news-title { font-weight: 600; font-size: 0.92rem; color: #e6edf3; }
  .news-meta  { font-size: 0.75rem; color: #8b949e; margin-top: 4px; }

  /* Sentiment pill */
  .pill-pos { background:#1a3a2a; color:#3fb950; border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; }
  .pill-neg { background:#3a1a1a; color:#f85149; border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; }
  .pill-neu { background:#1f2937; color:#8b949e; border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─── DATA LOADERS ────────────────────────────────────────────────────────────

DB_PATH  = "market_data.db"
CSV_PATH = "feature_matrix.csv"

@st.cache_data
def load_feature_matrix():
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return df

@st.cache_data
def load_ohlcv():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ohlcv ORDER BY ticker, date", conn, parse_dates=["date"])
    conn.close()
    return df

@st.cache_data
def load_headlines():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM headlines ORDER BY published_at DESC", conn,
        parse_dates=["published_at"]
    )
    conn.close()
    return df

@st.cache_data
def load_reddit():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM reddit_posts ORDER BY created_utc DESC LIMIT 500", conn
    )
    conn.close()
    df["created_utc"] = pd.to_datetime(df["created_utc"].astype(float), unit="s", utc=True)
    return df

fm  = load_feature_matrix()
ohlcv = load_ohlcv()
headlines = load_headlines()
reddit = load_reddit()

TICKERS = sorted(fm["ticker"].unique())

TICKER_COLORS = {
    "AAPL":    "#58a6ff",
    "MSFT":    "#3fb950",
    "NVDA":    "#d2a8ff",
    "TSLA":    "#f78166",
    "BTC-USD": "#f0883e",
}
def tcolor(t): return TICKER_COLORS.get(t, "#8b949e")

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font=dict(color="#e6edf3", family="Inter, sans-serif", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📡 Stock Sentiment\nAnalyzer")
    st.markdown("---")

    selected_tickers = st.multiselect(
        "Tickers", TICKERS, default=TICKERS,
        help="Select one or more assets to analyse."
    )
    if not selected_tickers:
        selected_tickers = TICKERS

    date_min = fm["date"].min().date()
    date_max = fm["date"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(date_min, date_max),
        min_value=date_min, max_value=date_max,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_start, d_end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    else:
        d_start, d_end = pd.Timestamp(date_min), pd.Timestamp(date_max)

    st.markdown("---")
    st.caption("Stack: FinBERT · FastAPI · PostgreSQL · Redis · Streamlit")

# ─── FILTER DATA ─────────────────────────────────────────────────────────────

fm_f = fm[
    fm["ticker"].isin(selected_tickers) &
    fm["date"].between(d_start, d_end)
].copy()

ohlcv_f = ohlcv[
    ohlcv["ticker"].isin(selected_tickers) &
    ohlcv["date"].between(d_start, d_end)
].copy()

hl_f = headlines[headlines["ticker"].isin(selected_tickers)].copy()

# ─── HEADER ──────────────────────────────────────────────────────────────────

st.markdown("# 📡 Stock Sentiment Analyzer")
st.markdown(
    f"**{len(selected_tickers)} asset(s)** · "
    f"{d_start.date()} → {d_end.date()} · "
    f"{len(fm_f):,} feature rows · {len(ohlcv_f):,} OHLCV bars"
)
st.markdown("---")

# ─── TOP KPI CARDS ───────────────────────────────────────────────────────────

latest = fm_f.sort_values("date").groupby("ticker").last().reset_index()

kpi_cols = st.columns(len(selected_tickers))
for i, ticker in enumerate(selected_tickers):
    row = latest[latest["ticker"] == ticker]
    if row.empty:
        continue
    row = row.iloc[0]
    sentiment = row["mean_sentiment"]
    close     = row["close"]
    rsi       = row["RSI_14"]
    direction = int(row["price_direction"])
    dir_sym   = "▲" if direction == 1 else ("▼" if direction == -1 else "—")
    dir_col   = "#3fb950" if direction == 1 else ("#f85149" if direction == -1 else "#8b949e")

    with kpi_cols[i]:
        st.metric(
            label=f"**{ticker}** {dir_sym}",
            value=f"${close:,.2f}" if "BTC" not in ticker else f"${close:,.0f}",
            delta=f"RSI {rsi:.1f}" if not np.isnan(rsi) else "RSI n/a",
        )
        sent_label = "POSITIVE" if sentiment > 0.02 else ("NEGATIVE" if sentiment < -0.02 else "NEUTRAL")
        pill_cls   = "pill-pos" if sent_label == "POSITIVE" else ("pill-neg" if sent_label == "NEGATIVE" else "pill-neu")
        st.markdown(
            f'<span class="{pill_cls}">{sent_label} {sentiment:+.3f}</span>',
            unsafe_allow_html=True
        )

st.markdown("---")

# ─── TABS ────────────────────────────────────────────────────────────────────

tabs = st.tabs([
    "📈 Price & Technicals",
    "🧠 Sentiment Analysis",
    "📊 Feature Explorer",
    "📰 News Feed",
    "🔥 Market Heatmap",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRICE & TECHNICALS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[0]:
    ticker_single = st.selectbox("Ticker", selected_tickers, key="pt_ticker")
    show_bands    = st.toggle("Bollinger Bands", value=True)
    show_sma      = st.toggle("SMA 5/10/20",    value=True)

    ohlcv_t = ohlcv_f[ohlcv_f["ticker"] == ticker_single].sort_values("date")
    fm_t    = fm_f[fm_f["ticker"] == ticker_single].sort_values("date")

    if ohlcv_t.empty:
        st.warning("No OHLCV data for selected range.")
    else:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            row_heights=[0.55, 0.25, 0.20],
            vertical_spacing=0.03,
            subplot_titles=("Price", "MACD", "Sentiment")
        )

        # ── Candlestick
        fig.add_trace(go.Candlestick(
            x=ohlcv_t["date"],
            open=ohlcv_t["open"], high=ohlcv_t["high"],
            low=ohlcv_t["low"],   close=ohlcv_t["close"],
            name="OHLCV",
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
            increasing_fillcolor="#1a3a2a",  decreasing_fillcolor="#3a1a1a",
        ), row=1, col=1)

        # ── Bollinger Bands
        if show_bands and "BBU_20_2.0" in fm_t.columns:
            bb = fm_t[["date","BBU_20_2.0","BBM_20_2.0","BBL_20_2.0"]].dropna()
            fig.add_trace(go.Scatter(
                x=bb["date"], y=bb["BBU_20_2.0"],
                mode="lines", line=dict(color="#58a6ff", width=1, dash="dash"),
                name="BB Upper", showlegend=False
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=bb["date"], y=bb["BBL_20_2.0"],
                mode="lines", fill="tonexty",
                fillcolor="rgba(88,166,255,0.07)",
                line=dict(color="#58a6ff", width=1, dash="dash"),
                name="BB Bands"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=bb["date"], y=bb["BBM_20_2.0"],
                mode="lines", line=dict(color="#8b949e", width=1),
                name="BB Mid"
            ), row=1, col=1)

        # ── SMAs
        if show_sma:
            for sma_col, sma_col_name, color in [
                ("SMA_5", "SMA5", "#f0883e"),
                ("SMA_10", "SMA10", "#d2a8ff"),
                ("SMA_20", "SMA20", "#3fb950"),
            ]:
                if sma_col in fm_t.columns:
                    s = fm_t[["date", sma_col]].dropna()
                    fig.add_trace(go.Scatter(
                        x=s["date"], y=s[sma_col],
                        mode="lines", line=dict(color=color, width=1.2),
                        name=sma_col_name
                    ), row=1, col=1)

        # ── MACD
        if "MACD_12_26_9" in fm_t.columns:
            macd = fm_t[["date","MACD_12_26_9","MACDs_12_26_9","MACDh_12_26_9"]].dropna()
            fig.add_trace(go.Bar(
                x=macd["date"],
                y=macd["MACDh_12_26_9"],
                marker_color=["#3fb950" if v >= 0 else "#f85149" for v in macd["MACDh_12_26_9"]],
                name="MACD Hist", showlegend=False
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=macd["date"], y=macd["MACD_12_26_9"],
                mode="lines", line=dict(color="#58a6ff", width=1.5), name="MACD"
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=macd["date"], y=macd["MACDs_12_26_9"],
                mode="lines", line=dict(color="#f0883e", width=1.5), name="Signal"
            ), row=2, col=1)

        # ── Sentiment overlay
        sent = fm_t[["date","mean_sentiment"]].dropna()
        if not sent.empty:
            fig.add_trace(go.Scatter(
                x=sent["date"], y=sent["mean_sentiment"],
                mode="lines+markers",
                marker=dict(size=3),
                line=dict(color="#d2a8ff", width=1.5),
                name="Sentiment"
            ), row=3, col=1)
            fig.add_hline(y=0, line=dict(color="#30363d", width=1), row=3, col=1)

        fig.update_layout(**PLOTLY_LAYOUT, height=680, xaxis_rangeslider_visible=False)
        fig.update_yaxes(row=2, title_text="MACD", title_font_size=10)
        fig.update_yaxes(row=3, title_text="Sent.", title_font_size=10)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SENTIMENT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

with tabs[1]:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Sentiment Time-Series")
        fig_sent = go.Figure()
        for t in selected_tickers:
            df_t = fm_f[fm_f["ticker"] == t].sort_values("date")
            sent_t = df_t[["date","mean_sentiment"]].dropna()
            if sent_t.empty: continue
            fig_sent.add_trace(go.Scatter(
                x=sent_t["date"], y=sent_t["mean_sentiment"],
                mode="lines", name=t,
                line=dict(color=tcolor(t), width=2),
            ))
        fig_sent.add_hline(y=0, line=dict(color="#30363d", width=1, dash="dash"))
        fig_sent.update_layout(**PLOTLY_LAYOUT, height=340,
                               yaxis_title="Mean Sentiment (FinBERT)")
        st.plotly_chart(fig_sent, use_container_width=True)

    with col2:
        st.subheader("Sentiment Distribution")
        all_sent = fm_f[["ticker","mean_sentiment"]].dropna()
        fig_hist = go.Figure()
        for t in selected_tickers:
            s = all_sent[all_sent["ticker"] == t]["mean_sentiment"]
            if s.empty: continue
            fig_hist.add_trace(go.Histogram(
                x=s, name=t, nbinsx=40, opacity=0.75,
                marker_color=tcolor(t),
            ))
        fig_hist.update_layout(**PLOTLY_LAYOUT, barmode="overlay", height=340,
                               xaxis_title="Sentiment Score")
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Sentiment vs. Next-Day Direction")
        heatmap_data = fm_f[["ticker","mean_sentiment","price_direction"]].dropna()
        heatmap_data["sentiment_bucket"] = pd.cut(
            heatmap_data["mean_sentiment"],
            bins=[-1, -0.1, -0.02, 0.02, 0.1, 1],
            labels=["Very Neg", "Neg", "Neutral", "Pos", "Very Pos"]
        )
        cross = heatmap_data.groupby(["sentiment_bucket","price_direction"]).size().unstack(fill_value=0)
        cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100
        fig_hm = px.imshow(
            cross_pct.T,
            color_continuous_scale=[[0,"#3a1a1a"],[0.5,"#21262d"],[1,"#1a3a2a"]],
            labels=dict(x="Sentiment Bucket", y="Price Direction", color="% days"),
            aspect="auto",
        )
        fig_hm.update_layout(**PLOTLY_LAYOUT, height=280, coloraxis_colorbar_title="% days")
        fig_hm.update_yaxes(tickvals=[-1,0,1], ticktext=["▼ Down","— Flat","▲ Up"])
        st.plotly_chart(fig_hm, use_container_width=True)

    with col4:
        st.subheader("Headline Volume & Sentiment Volatility")
        vol_df = fm_f.groupby("ticker").agg(
            avg_volume=("headline_volume","mean"),
            avg_vol_std=("sentiment_volatility","mean"),
        ).reset_index()
        fig_bubble = go.Figure(go.Scatter(
            x=vol_df["avg_volume"], y=vol_df["avg_vol_std"],
            mode="markers+text",
            marker=dict(
                size=vol_df["avg_volume"] * 40 + 18,
                color=[tcolor(t) for t in vol_df["ticker"]],
                opacity=0.85,
            ),
            text=vol_df["ticker"],
            textposition="top center",
            name=""
        ))
        fig_bubble.update_layout(
            **PLOTLY_LAYOUT, height=280,
            xaxis_title="Avg Headline Volume",
            yaxis_title="Avg Sentiment Volatility",
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FEATURE EXPLORER
# ══════════════════════════════════════════════════════════════════════════════

with tabs[2]:
    st.subheader("Feature Correlation Matrix")
    numeric_cols = [
        "mean_sentiment","sentiment_volatility","headline_volume",
        "RSI_14","MACD_12_26_9","BBP_20_2.0",
        "SMA_5","close","volume","overnight_gap","price_direction"
    ]
    corr_df = fm_f[numeric_cols].dropna()
    if len(corr_df) > 10:
        corr = corr_df.corr()
        fig_corr = px.imshow(
            corr,
            color_continuous_scale=[[0,"#f85149"],[0.5,"#21262d"],[1,"#3fb950"]],
            zmin=-1, zmax=1,
            labels=dict(color="r"),
            aspect="auto",
        )
        fig_corr.update_layout(**PLOTLY_LAYOUT, height=480)
        st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")
    st.subheader("RSI Monitor")
    rsi_latest = fm_f.dropna(subset=["RSI_14"]).sort_values("date").groupby("ticker").last()[["RSI_14"]].reset_index()
    if not rsi_latest.empty:
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="#f85149", opacity=0.08, line_width=0)
        fig_rsi.add_hrect(y0=0,  y1=30,  fillcolor="#3fb950", opacity=0.08, line_width=0)
        fig_rsi.add_hline(y=70, line=dict(color="#f85149", width=1, dash="dot"))
        fig_rsi.add_hline(y=30, line=dict(color="#3fb950", width=1, dash="dot"))
        fig_rsi.add_trace(go.Bar(
            x=rsi_latest["ticker"], y=rsi_latest["RSI_14"],
            marker_color=[
                "#f85149" if v > 70 else ("#3fb950" if v < 30 else "#58a6ff")
                for v in rsi_latest["RSI_14"]
            ],
            text=[f"{v:.1f}" for v in rsi_latest["RSI_14"]],
            textposition="outside",
        ))
        fig_rsi.update_layout(**PLOTLY_LAYOUT, height=280)
        fig_rsi.update_yaxes(range=[0, 105], title_text="RSI (14)")
        st.plotly_chart(fig_rsi, use_container_width=True)

    st.markdown("---")
    st.subheader("Raw Feature Table")
    st.dataframe(
        fm_f.sort_values("date", ascending=False).head(200).reset_index(drop=True),
        use_container_width=True, height=320,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — NEWS FEED
# ══════════════════════════════════════════════════════════════════════════════

with tabs[3]:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Latest Headlines")
        n_show = st.slider("Show headlines", 5, 50, 20, step=5)
        for _, row in hl_f.head(n_show).iterrows():
            pub = row["published_at"]
            pub_str = pub.strftime("%b %d, %H:%M UTC") if pd.notna(pub) else "Unknown"
            desc = (row["description"] or "")[:180]
            if len(row.get("description", "") or "") > 180: desc += "…"
            st.markdown(f"""
            <div class="news-card">
              <div class="news-title"><a href="{row['url']}" target="_blank" style="color:#58a6ff;text-decoration:none;">{row['title']}</a></div>
              <div class="news-meta">🏷 {row['ticker']} &nbsp;·&nbsp; 📰 {row['source'].upper()} &nbsp;·&nbsp; 🕒 {pub_str}</div>
              <div style="color:#8b949e;font-size:0.82rem;margin-top:6px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.subheader("Reddit Pulse (WSB)")
        st.caption(f"{len(reddit):,} posts scraped")
        reddit_top = reddit.sort_values("score", ascending=False).head(15)
        fig_reddit = go.Figure(go.Bar(
            x=reddit_top["score"],
            y=[t[:50] + "…" if len(t) > 50 else t for t in reddit_top["title"]],
            orientation="h",
            marker_color="#f0883e",
        ))
        fig_reddit.update_layout(**PLOTLY_LAYOUT, height=540,
                                 xaxis_title="Reddit Score")
        fig_reddit.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_reddit, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — MARKET HEATMAP
# ══════════════════════════════════════════════════════════════════════════════

with tabs[4]:
    st.subheader("Multi-Asset Sentiment Heatmap (calendar view)")

    ticker_heat = st.selectbox("Ticker", selected_tickers, key="hm_ticker")
    fm_hm = fm_f[fm_f["ticker"] == ticker_heat][["date","mean_sentiment"]].dropna().copy()
    fm_hm["week"] = fm_hm["date"].dt.isocalendar().week.astype(int)
    fm_hm["dow"]  = fm_hm["date"].dt.dayofweek   # 0=Mon

    pivot = fm_hm.pivot_table(
        index="dow", columns="week", values="mean_sentiment", aggfunc="mean"
    )
    dow_labels = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
    pivot.index = [dow_labels.get(i, str(i)) for i in pivot.index]

    fig_cal = px.imshow(
        pivot,
        color_continuous_scale=[[0,"#f85149"],[0.5,"#21262d"],[1,"#3fb950"]],
        zmin=-0.3, zmax=0.3,
        labels=dict(x="ISO Week", y="Day", color="Sentiment"),
        aspect="auto",
    )
    fig_cal.update_layout(**PLOTLY_LAYOUT, height=280)
    st.plotly_chart(fig_cal, use_container_width=True)

    st.markdown("---")
    st.subheader("Comparative Performance — Normalised Close")
    fig_norm = go.Figure()
    for t in selected_tickers:
        s = ohlcv_f[ohlcv_f["ticker"] == t].sort_values("date")
        if s.empty or s["close"].iloc[0] == 0: continue
        norm = s["close"] / s["close"].iloc[0] * 100
        fig_norm.add_trace(go.Scatter(
            x=s["date"], y=norm, name=t,
            mode="lines", line=dict(color=tcolor(t), width=2)
        ))
    fig_norm.add_hline(y=100, line=dict(color="#30363d", width=1, dash="dot"))
    fig_norm.update_layout(**PLOTLY_LAYOUT, height=340,
                           yaxis_title="Indexed Price (Base = 100)")
    st.plotly_chart(fig_norm, use_container_width=True)

    st.markdown("---")
    st.subheader("Volume Heatmap")
    vol_pivot = (
        ohlcv_f.assign(month=ohlcv_f["date"].dt.to_period("M").astype(str))
               .groupby(["ticker","month"])["volume"]
               .mean()
               .unstack("month")
    )
    if not vol_pivot.empty:
        fig_vol = px.imshow(
            vol_pivot,
            color_continuous_scale=[[0,"#161b22"],[1,"#58a6ff"]],
            labels=dict(x="Month", y="Ticker", color="Avg Volume"),
            aspect="auto",
        )
        fig_vol.update_layout(**PLOTLY_LAYOUT, height=220)
        st.plotly_chart(fig_vol, use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    "📡 Stock Sentiment Analyzer · FinBERT · FastAPI · PostgreSQL · Redis · Streamlit · "
    f"Data refreshed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
)