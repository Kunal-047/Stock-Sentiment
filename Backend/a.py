from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import sys


class StockHistoryScraper:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.url = f"https://finance.yahoo.com/quote/{self.ticker}/history/"

    def _scrape_html(self) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle")
            html = page.content()
            browser.close()
        return html

    def _parse_html(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="table yf-u4m6f0 noDl hideOnPrint")

        if not table:
            raise ValueError(f"Could not find history table for ticker '{self.ticker}'. "
                             "The page structure may have changed or the ticker is invalid.")

        data = {}
        for row in table.tbody.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 5:
                date = cols[0].get_text(strip=True)
                try:
                    open_  = float(cols[1].get_text(strip=True).replace(",", ""))
                    high   = float(cols[2].get_text(strip=True).replace(",", ""))
                    low    = float(cols[3].get_text(strip=True).replace(",", ""))
                    close  = float(cols[4].get_text(strip=True).replace(",", ""))
                    data[date] = [open_, high, low, close]
                except ValueError:
                    # Skip rows like dividends / splits that don't have numeric prices
                    continue

        return data

    def _save_csv(self, data: dict, output_path: str):
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Open", "High", "Low", "Close"])
            for date, (open_, high, low, close) in data.items():
                writer.writerow([date, open_, high, low, close])

    def run(self, output_path: str = None):
        if output_path is None:
            output_path = f"{self.ticker}_history.csv"

        print(f"Scraping history for {self.ticker}...")
        html = self._scrape_html()

        print("Parsing table...")
        data = self._parse_html(html)

        print(f"Writing {len(data)} rows to {output_path}...")
        self._save_csv(data, output_path)

        print(f"Done! Saved to: {output_path}")
        return output_path


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    scraper = StockHistoryScraper(ticker)
    scraper.run()