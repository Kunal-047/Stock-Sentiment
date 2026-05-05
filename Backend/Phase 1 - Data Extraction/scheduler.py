# scheduler.py — Run all ingestion jobs on a schedule
import schedule
import time
import ingest_news
import ingest_prices
import ingest_reddit
from db import init_db

def run_all():
    print("\n=== Starting ingestion run ===")
    ingest_prices.run()   # prices first (market hours sensitive)
    ingest_news.run()
    ingest_reddit.run()
    print("=== Run complete ===\n")

if __name__ == "__main__":
    init_db()             # ensure schema exists on first run

    # Schedule: prices every 30min, news/reddit every hour
    schedule.every(30).minutes.do(ingest_prices.run)
    schedule.every(1).hours.do(ingest_news.run)
    schedule.every(1).hours.do(ingest_reddit.run)

    run_all()             # run immediately on start
    while True:
        schedule.run_pending()
        time.sleep(60)