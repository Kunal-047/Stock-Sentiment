# config.py — Replace placeholder values with your real credentials

# NewsAPI (https://newsapi.org)
NEWSAPI_KEY = "b4cc562883eb4fc68dd7d5a502e0480d"

# GNews (https://gnews.io)
GNEWS_KEY = "7c9e10303e37c0bc36580b7f62cc7d3c"

# Alpha Vantage (https://www.alphavantage.co)
ALPHA_VANTAGE_KEY = "HKH29GUO7G9W0X82"

# Reddit OAuth (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID     = "YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET"
REDDIT_USER_AGENT    = "stock-sentiment-bot/1.0 by YOUR_REDDIT_USERNAME"

# Tickers to track
TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "TSLA", "NFLX", "AMD", "INTC",
    "JPM", "GS", "BAC", "V", "MA",
    "XOM", "CVX", "LLY", "UNH", "JNJ",
    "SPY", "QQQ", "BTC-USD", "ETH-USD", "PLTR"
]

# DB path (SQLite for local dev; swap with PostgreSQL DSN on deploy)
DB_PATH = "market_data.db"
# POSTGRES_DSN = "postgresql://user:password@localhost:5432/market_data"