import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Market Intelligence Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Market Intelligence Terminal")
st.markdown(
    "Dense analytics dashboard with financial, sentiment, and engagement intelligence."
)

# =========================
# DATABASE CONNECTION
# =========================
DB_PATH = "market_data.db"

conn = sqlite3.connect(DB_PATH)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_ohlcv():
    query = "SELECT * FROM ohlcv"
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def load_news():
    try:
        query = "SELECT * FROM headlines"
        df = pd.read_sql(query, conn)

        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])

        return df

    except:
        return pd.DataFrame()


@st.cache_data
def load_reddit():
    try:
        query = "SELECT * FROM reddit_posts"
        df = pd.read_sql(query, conn)

        if 'created_utc' in df.columns:
            df['created_utc'] = pd.to_datetime(df['created_utc'])

        return df

    except:
        return pd.DataFrame()


@st.cache_data
def load_feature_matrix():
    try:
        return pd.read_csv("feature_matrix.csv")
    except:
        return pd.DataFrame()


# =========================
# LOAD TABLES
# =========================
price_df = load_ohlcv()
news_df = load_news()
reddit_df = load_reddit()
feature_df = load_feature_matrix()

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Dashboard Controls")

available_tickers = sorted(price_df['ticker'].unique())

selected_ticker = st.sidebar.selectbox(
    "Select Ticker",
    available_tickers,
    index=0
)

# =========================
# FILTER STOCK DATA
# =========================
stock_df = price_df[price_df['ticker'] == selected_ticker].copy()

stock_df = stock_df.sort_values('date')

min_date = stock_df['date'].min().date()
max_date = stock_df['date'].max().date()

selected_dates = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

stock_df = stock_df[
    (stock_df['date'].dt.date >= selected_dates[0]) &
    (stock_df['date'].dt.date <= selected_dates[1])
]

# =========================
# FEATURE ENGINEERING
# =========================
stock_df['returns'] = stock_df['close'].pct_change() * 100

stock_df['MA20'] = stock_df['close'].rolling(20).mean()

stock_df['MA50'] = stock_df['close'].rolling(50).mean()

stock_df['direction'] = stock_df['returns'].apply(
    lambda x: 'Up Day' if x > 0 else 'Down Day'
)

stock_df['month'] = stock_df['date'].dt.strftime('%b')

stock_df['weekday'] = stock_df['date'].dt.day_name()

stock_df['week'] = stock_df['date'].dt.isocalendar().week

# =========================
# METRICS
# =========================
latest_close = stock_df['close'].iloc[-1]

first_close = stock_df['close'].iloc[0]

price_change = ((latest_close - first_close) / first_close) * 100

avg_volume = stock_df['volume'].mean()

volatility = stock_df['close'].pct_change().std() * 100

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("Latest Close", f"${latest_close:.2f}")

metric2.metric("Period Return", f"{price_change:.2f}%")

metric3.metric("Average Volume", f"{avg_volume:,.0f}")

metric4.metric("Volatility", f"{volatility:.2f}%")

# =========================
# MINI SPARKLINE
# =========================
spark_fig = px.line(
    stock_df.tail(30),
    x='date',
    y='close',
    template='plotly_dark'
)

spark_fig.update_layout(
    height=120,
    margin=dict(l=10, r=10, t=10, b=10)
)

st.plotly_chart(spark_fig, use_container_width=True)

# =========================
# GAUGE + BOXPLOT
# =========================
top_left, top_right = st.columns(2)

# -------------------------
# Gauge
# -------------------------
with top_left:

    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=price_change,
        title={'text': "Return %"},
        gauge={
            'axis': {'range': [-20, 20]}
        }
    ))

    gauge_fig.update_layout(
        height=250,
        template='plotly_dark'
    )

    st.plotly_chart(gauge_fig, use_container_width=True)

# -------------------------
# Boxplot
# -------------------------
with top_right:

    box_fig = px.box(
        stock_df,
        y='returns',
        template='plotly_dark'
    )

    box_fig.update_layout(
        title="Return Volatility",
        height=250
    )

    st.plotly_chart(box_fig, use_container_width=True)

# =========================
# MAIN COMBINED DASHBOARD
# =========================
st.subheader(f"📊 {selected_ticker} Market Dashboard")

dashboard_fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "Candlestick",
        "Moving Averages",
        "Volume",
        "Returns Distribution"
    ),
    vertical_spacing=0.12
)

# -------------------------
# Candlestick
# -------------------------
dashboard_fig.add_trace(
    go.Candlestick(
        x=stock_df['date'],
        open=stock_df['open'],
        high=stock_df['high'],
        low=stock_df['low'],
        close=stock_df['close'],
        name='OHLC'
    ),
    row=1,
    col=1
)

# -------------------------
# Moving Averages
# -------------------------
dashboard_fig.add_trace(
    go.Scatter(
        x=stock_df['date'],
        y=stock_df['close'],
        mode='lines',
        name='Close'
    ),
    row=1,
    col=2
)

dashboard_fig.add_trace(
    go.Scatter(
        x=stock_df['date'],
        y=stock_df['MA20'],
        mode='lines',
        name='MA20'
    ),
    row=1,
    col=2
)

dashboard_fig.add_trace(
    go.Scatter(
        x=stock_df['date'],
        y=stock_df['MA50'],
        mode='lines',
        name='MA50'
    ),
    row=1,
    col=2
)

# -------------------------
# Volume
# -------------------------
dashboard_fig.add_trace(
    go.Bar(
        x=stock_df['date'],
        y=stock_df['volume'],
        name='Volume'
    ),
    row=2,
    col=1
)

# -------------------------
# Returns Distribution
# -------------------------
dashboard_fig.add_trace(
    go.Histogram(
        x=stock_df['returns'],
        nbinsx=40,
        name='Returns'
    ),
    row=2,
    col=2
)

dashboard_fig.update_layout(
    height=700,
    template="plotly_dark",
    showlegend=False
)

st.plotly_chart(dashboard_fig, use_container_width=True)

# =========================
# SECOND GRID
# =========================
grid_left, grid_right = st.columns(2)

# -------------------------
# PIE CHART
# -------------------------
with grid_left:

    direction_counts = stock_df['direction'].value_counts().reset_index()

    direction_counts.columns = ['Direction', 'Count']

    pie_fig = px.pie(
        direction_counts,
        names='Direction',
        values='Count',
        hole=0.5,
        template='plotly_dark'
    )

    pie_fig.update_layout(
        title="Market Direction",
        height=320
    )

    st.plotly_chart(pie_fig, use_container_width=True)

# -------------------------
# DONUT CHART
# -------------------------
with grid_right:

    monthly_volume = stock_df.groupby('month')['volume'].sum().reset_index()

    donut_fig = px.pie(
        monthly_volume,
        names='month',
        values='volume',
        hole=0.6,
        template='plotly_dark'
    )

    donut_fig.update_layout(
        title="Volume by Month",
        height=320
    )

    st.plotly_chart(donut_fig, use_container_width=True)

# =========================
# HEATMAP + CORRELATION
# =========================
heat_left, heat_right = st.columns(2)

# -------------------------
# Return Heatmap
# -------------------------
with heat_left:

    heatmap_data = stock_df.pivot_table(
        values='returns',
        index='weekday',
        columns='week',
        aggfunc='mean'
    )

    heatmap_fig = px.imshow(
        heatmap_data,
        aspect='auto',
        template='plotly_dark'
    )

    heatmap_fig.update_layout(
        title="Return Heatmap",
        height=420
    )

    st.plotly_chart(heatmap_fig, use_container_width=True)

# -------------------------
# Correlation Bubble
# -------------------------
with heat_right:

    if not feature_df.empty:

        numeric_cols = feature_df.select_dtypes(include='number')

        corr_matrix = numeric_cols.corr()

        corr = corr_matrix.reset_index().melt(id_vars='index')

        corr.columns = ['Feature1', 'Feature2', 'Correlation']

        # Remove NaN values
        corr = corr.dropna()

        # Bubble size must be positive numeric
        corr['AbsCorrelation'] = corr['Correlation'].abs()

        bubble_fig = px.scatter(
            corr,
            x='Feature1',
            y='Feature2',
            size='AbsCorrelation',
            color='Correlation',
            template='plotly_dark'
        )

        bubble_fig.update_layout(
            title="Feature Correlation",
            height=420
        )

        st.plotly_chart(
            bubble_fig,
            use_container_width=True
        )

# =========================
# NEWS + REDDIT ANALYTICS
# =========================
social_left, social_right = st.columns(2)

# -------------------------
# News Analytics
# -------------------------
with social_left:

    if not news_df.empty:

        st.subheader("📰 News Activity")

        if 'ticker' in news_df.columns:

            ticker_news = news_df[
                news_df['ticker'] == selected_ticker
            ]

            if not ticker_news.empty:

                news_daily = ticker_news.groupby(
                    ticker_news['published_at'].dt.date
                ).size().reset_index(name='count')

                news_fig = px.line(
                    news_daily,
                    x='published_at',
                    y='count',
                    markers=True,
                    template='plotly_dark'
                )

                news_fig.update_layout(
                    height=320
                )

                st.plotly_chart(
                    news_fig,
                    use_container_width=True
                )

# -------------------------
# Reddit Analytics
# -------------------------
with social_right:

    if not reddit_df.empty:

        st.subheader("🚀 Reddit Engagement")

        ticker_reddit = reddit_df[
            reddit_df['ticker'] == selected_ticker
        ]

        if not ticker_reddit.empty:

            if (
                'score' in ticker_reddit.columns and
                'num_comments' in ticker_reddit.columns
            ):

                scatter_fig = px.scatter(
                    ticker_reddit,
                    x='score',
                    y='num_comments',
                    size='num_comments',
                    template='plotly_dark'
                )

                scatter_fig.update_layout(
                    height=320
                )

                st.plotly_chart(
                    scatter_fig,
                    use_container_width=True
                )

# =========================
# RAW DATA
# =========================
with st.expander("📂 View Raw Data"):
    st.dataframe(
        stock_df.tail(100),
        use_container_width=True
    )

# =========================
# FOOTER
# =========================
st.markdown("---")

st.caption(
    "Built with Streamlit + Plotly | Market Intelligence Terminal"
)