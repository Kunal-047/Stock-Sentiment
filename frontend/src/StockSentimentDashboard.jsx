import { useState, useEffect, useCallback } from "react";
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ReferenceLine, Cell
} from "recharts";

// ─── Mock API (replace base URL with your Railway deployment) ────────────────
const API_BASE = "https://your-api.railway.app";

async function fetchAPI(path) {
    // In dev/demo, use mock data
    return null;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────
const MOCK = {
    AAPL: {
        predict: {
            ticker: "AAPL", prediction: "Up", predicted_class: 2,
            confidence: 0.812, feature_date: "2025-05-02",
            probabilities: { Down: 0.081, Flat: 0.107, Up: 0.812 },
            sentiment_score: 0.34,
            top_headline: "Apple reports record services revenue, beating analyst forecasts",
            feature_contributions: [
                { feature: "mean_sentiment", value: 0.38 },
                { feature: "rsi_14", value: 0.27 },
                { feature: "sma_ratio_20_50", value: 0.19 },
                { feature: "negative_spike_flag", value: -0.12 },
                { feature: "headline_volume", value: 0.11 },
                { feature: "volume_ratio", value: 0.09 },
                { feature: "sentiment_volatility", value: -0.07 },
                { feature: "macd_signal", value: 0.06 },
                { feature: "bb_width", value: -0.04 },
                { feature: "return_5d", value: 0.03 },
            ],
        },
        sentiment: {
            ticker: "AAPL", days: 7,
            trend: [
                { date: "04-26", mean_sentiment: 0.21, headline_volume: 8, mean_positive: 0.41, mean_negative: 0.20 },
                { date: "04-27", mean_sentiment: -0.08, headline_volume: 5, mean_positive: 0.29, mean_negative: 0.37 },
                { date: "04-28", mean_sentiment: 0.15, headline_volume: 11, mean_positive: 0.38, mean_negative: 0.23 },
                { date: "04-29", mean_sentiment: 0.29, headline_volume: 9, mean_positive: 0.44, mean_negative: 0.15 },
                { date: "04-30", mean_sentiment: 0.34, headline_volume: 14, mean_positive: 0.51, mean_negative: 0.17 },
                { date: "05-01", mean_sentiment: 0.18, headline_volume: 7, mean_positive: 0.36, mean_negative: 0.18 },
                { date: "05-02", mean_sentiment: 0.34, headline_volume: 12, mean_positive: 0.49, mean_negative: 0.15 },
            ],
        },
        history: [
            { date: "04-14", close: 172.1, volume: 68_000_000 },
            { date: "04-15", close: 174.8, volume: 72_000_000 },
            { date: "04-16", close: 171.3, volume: 81_000_000 },
            { date: "04-17", close: 169.9, volume: 94_000_000 },
            { date: "04-22", close: 173.4, volume: 61_000_000 },
            { date: "04-23", close: 177.2, volume: 58_000_000 },
            { date: "04-24", close: 178.9, volume: 63_000_000 },
            { date: "04-25", close: 176.1, volume: 77_000_000 },
            { date: "04-28", close: 180.3, volume: 69_000_000 },
            { date: "04-29", close: 182.7, volume: 74_000_000 },
            { date: "04-30", close: 184.1, volume: 71_000_000 },
            { date: "05-01", close: 183.4, volume: 66_000_000 },
            { date: "05-02", close: 186.2, volume: 79_000_000 },
        ],
        headlines: [
            { headline: "Apple reports record services revenue, beating analyst forecasts", sentiment: 0.82, label: "positive", time: "2h ago" },
            { headline: "iPhone 17 supply chain concerns emerge from Asian suppliers", sentiment: -0.54, label: "negative", time: "5h ago" },
            { headline: "Apple increases share buyback program by $110 billion", sentiment: 0.71, label: "positive", time: "8h ago" },
            { headline: "EU opens new antitrust probe into App Store practices", sentiment: -0.38, label: "negative", time: "1d ago" },
            { headline: "Vision Pro sales stabilize after initial launch softness", sentiment: 0.29, label: "neutral", time: "1d ago" },
        ],
        stats: { accuracy: 0.684, precision: 0.701, recall: 0.672, f1: 0.686, total_trades: 142 },
    },
    MSFT: {
        predict: {
            ticker: "MSFT", prediction: "Up", predicted_class: 2,
            confidence: 0.741, feature_date: "2025-05-02",
            probabilities: { Down: 0.12, Flat: 0.139, Up: 0.741 },
            sentiment_score: 0.28,
            top_headline: "Microsoft Azure growth accelerates on AI infrastructure demand",
            feature_contributions: [
                { feature: "mean_sentiment", value: 0.31 }, { feature: "rsi_14", value: 0.22 },
                { feature: "sma_ratio_20_50", value: 0.21 }, { feature: "volume_ratio", value: 0.14 },
                { feature: "negative_spike_flag", value: -0.09 }, { feature: "headline_volume", value: 0.08 },
                { feature: "macd_signal", value: 0.07 }, { feature: "bb_width", value: -0.05 },
                { feature: "return_5d", value: 0.04 }, { feature: "sentiment_volatility", value: -0.03 },
            ],
        },
        sentiment: {
            ticker: "MSFT", days: 7,
            trend: [
                { date: "04-26", mean_sentiment: 0.18, headline_volume: 6, mean_positive: 0.37, mean_negative: 0.19 },
                { date: "04-27", mean_sentiment: 0.22, headline_volume: 8, mean_positive: 0.41, mean_negative: 0.19 },
                { date: "04-28", mean_sentiment: 0.11, headline_volume: 10, mean_positive: 0.33, mean_negative: 0.22 },
                { date: "04-29", mean_sentiment: 0.31, headline_volume: 13, mean_positive: 0.48, mean_negative: 0.17 },
                { date: "04-30", mean_sentiment: 0.25, headline_volume: 9, mean_positive: 0.43, mean_negative: 0.18 },
                { date: "05-01", mean_sentiment: 0.19, headline_volume: 7, mean_positive: 0.38, mean_negative: 0.19 },
                { date: "05-02", mean_sentiment: 0.28, headline_volume: 11, mean_positive: 0.46, mean_negative: 0.18 },
            ],
        },
        history: [
            { date: "04-14", close: 418.3, volume: 22_000_000 }, { date: "04-15", close: 421.1, volume: 24_000_000 },
            { date: "04-16", close: 419.8, volume: 26_000_000 }, { date: "04-17", close: 416.2, volume: 31_000_000 },
            { date: "04-22", close: 423.7, volume: 20_000_000 }, { date: "04-23", close: 428.4, volume: 19_000_000 },
            { date: "04-24", close: 432.1, volume: 22_000_000 }, { date: "04-25", close: 430.9, volume: 25_000_000 },
            { date: "04-28", close: 435.6, volume: 21_000_000 }, { date: "04-29", close: 438.2, volume: 23_000_000 },
            { date: "04-30", close: 441.7, volume: 24_000_000 }, { date: "05-01", close: 439.3, volume: 20_000_000 },
            { date: "05-02", close: 444.8, volume: 27_000_000 },
        ],
        headlines: [
            { headline: "Microsoft Azure growth accelerates on AI infrastructure demand", sentiment: 0.77, label: "positive", time: "3h ago" },
            { headline: "Copilot enterprise adoption reaches 1 million paid seats", sentiment: 0.68, label: "positive", time: "6h ago" },
            { headline: "Microsoft faces fresh scrutiny over Teams bundling in Europe", sentiment: -0.42, label: "negative", time: "9h ago" },
            { headline: "OpenAI partnership terms renegotiated, terms undisclosed", sentiment: -0.19, label: "neutral", time: "1d ago" },
            { headline: "Surface lineup refresh expected at Build 2025 conference", sentiment: 0.31, label: "neutral", time: "1d ago" },
        ],
        stats: { accuracy: 0.661, precision: 0.678, recall: 0.649, f1: 0.663, total_trades: 138 },
    },
    NVDA: {
        predict: {
            ticker: "NVDA", prediction: "Up", predicted_class: 2,
            confidence: 0.889, feature_date: "2025-05-02",
            probabilities: { Down: 0.048, Flat: 0.063, Up: 0.889 },
            sentiment_score: 0.61,
            top_headline: "NVIDIA H200 backlog extends to 18 months as hyperscalers race for compute",
            feature_contributions: [
                { feature: "mean_sentiment", value: 0.52 }, { feature: "headline_volume", value: 0.31 },
                { feature: "rsi_14", value: 0.18 }, { feature: "volume_ratio", value: 0.17 },
                { feature: "sma_ratio_20_50", value: 0.14 }, { feature: "return_5d", value: 0.11 },
                { feature: "negative_spike_flag", value: -0.08 }, { feature: "macd_signal", value: 0.07 },
                { feature: "bb_width", value: 0.05 }, { feature: "sentiment_volatility", value: -0.04 },
            ],
        },
        sentiment: {
            ticker: "NVDA", days: 7,
            trend: [
                { date: "04-26", mean_sentiment: 0.42, headline_volume: 18, mean_positive: 0.61, mean_negative: 0.19 },
                { date: "04-27", mean_sentiment: 0.38, headline_volume: 22, mean_positive: 0.57, mean_negative: 0.19 },
                { date: "04-28", mean_sentiment: 0.51, headline_volume: 31, mean_positive: 0.68, mean_negative: 0.17 },
                { date: "04-29", mean_sentiment: 0.59, headline_volume: 28, mean_positive: 0.74, mean_negative: 0.15 },
                { date: "04-30", mean_sentiment: 0.55, headline_volume: 24, mean_positive: 0.71, mean_negative: 0.16 },
                { date: "05-01", mean_sentiment: 0.48, headline_volume: 19, mean_positive: 0.65, mean_negative: 0.17 },
                { date: "05-02", mean_sentiment: 0.61, headline_volume: 27, mean_positive: 0.77, mean_negative: 0.16 },
            ],
        },
        history: [
            { date: "04-14", close: 874.2, volume: 41_000_000 }, { date: "04-15", close: 891.7, volume: 48_000_000 },
            { date: "04-16", close: 886.3, volume: 52_000_000 }, { date: "04-17", close: 879.1, volume: 61_000_000 },
            { date: "04-22", close: 898.4, volume: 39_000_000 }, { date: "04-23", close: 912.6, volume: 37_000_000 },
            { date: "04-24", close: 928.3, volume: 44_000_000 }, { date: "04-25", close: 921.7, volume: 49_000_000 },
            { date: "04-28", close: 941.2, volume: 43_000_000 }, { date: "04-29", close: 958.8, volume: 46_000_000 },
            { date: "04-30", close: 971.4, volume: 51_000_000 }, { date: "05-01", close: 963.9, volume: 44_000_000 },
            { date: "05-02", close: 988.2, volume: 58_000_000 },
        ],
        headlines: [
            { headline: "NVIDIA H200 backlog extends to 18 months as hyperscalers race for compute", sentiment: 0.88, label: "positive", time: "1h ago" },
            { headline: "Jensen Huang keynote at GTC confirms Blackwell Ultra production ramp", sentiment: 0.79, label: "positive", time: "4h ago" },
            { headline: "China export restrictions could impact up to $15B in annual revenue", sentiment: -0.71, label: "negative", time: "7h ago" },
            { headline: "NVIDIA partners with Saudi Aramco on AI refinery optimization", sentiment: 0.64, label: "positive", time: "11h ago" },
            { headline: "AMD MI350 benchmarks show competitive performance at lower cost", sentiment: -0.33, label: "negative", time: "1d ago" },
        ],
        stats: { accuracy: 0.721, precision: 0.738, recall: 0.709, f1: 0.723, total_trades: 156 },
    },
    TSLA: {
        predict: {
            ticker: "TSLA", prediction: "Down", predicted_class: 0,
            confidence: 0.627, feature_date: "2025-05-02",
            probabilities: { Down: 0.627, Flat: 0.201, Up: 0.172 },
            sentiment_score: -0.29,
            top_headline: "Tesla Q1 deliveries miss estimates for second consecutive quarter",
            feature_contributions: [
                { feature: "negative_spike_flag", value: -0.44 }, { feature: "mean_sentiment", value: -0.38 },
                { feature: "headline_volume", value: -0.21 }, { feature: "rsi_14", value: -0.18 },
                { feature: "sentiment_volatility", value: -0.14 }, { feature: "sma_ratio_20_50", value: -0.11 },
                { feature: "volume_ratio", value: 0.09 }, { feature: "macd_signal", value: -0.07 },
                { feature: "return_5d", value: -0.05 }, { feature: "bb_width", value: 0.03 },
            ],
        },
        sentiment: {
            ticker: "TSLA", days: 7,
            trend: [
                { date: "04-26", mean_sentiment: -0.11, headline_volume: 19, mean_positive: 0.28, mean_negative: 0.39 },
                { date: "04-27", mean_sentiment: -0.24, headline_volume: 24, mean_positive: 0.22, mean_negative: 0.46 },
                { date: "04-28", mean_sentiment: -0.31, headline_volume: 33, mean_positive: 0.19, mean_negative: 0.50 },
                { date: "04-29", mean_sentiment: -0.19, headline_volume: 21, mean_positive: 0.24, mean_negative: 0.43 },
                { date: "04-30", mean_sentiment: -0.35, headline_volume: 28, mean_positive: 0.17, mean_negative: 0.52 },
                { date: "05-01", mean_sentiment: -0.22, headline_volume: 17, mean_positive: 0.23, mean_negative: 0.45 },
                { date: "05-02", mean_sentiment: -0.29, headline_volume: 22, mean_positive: 0.20, mean_negative: 0.49 },
            ],
        },
        history: [
            { date: "04-14", close: 198.4, volume: 112_000_000 }, { date: "04-15", close: 191.2, volume: 134_000_000 },
            { date: "04-16", close: 187.8, volume: 148_000_000 }, { date: "04-17", close: 183.1, volume: 162_000_000 },
            { date: "04-22", close: 179.6, volume: 121_000_000 }, { date: "04-23", close: 182.4, volume: 108_000_000 },
            { date: "04-24", close: 178.9, volume: 118_000_000 }, { date: "04-25", close: 174.3, volume: 131_000_000 },
            { date: "04-28", close: 171.8, volume: 124_000_000 }, { date: "04-29", close: 168.2, volume: 139_000_000 },
            { date: "04-30", close: 165.7, volume: 145_000_000 }, { date: "05-01", close: 169.1, volume: 127_000_000 },
            { date: "05-02", close: 163.4, volume: 152_000_000 },
        ],
        headlines: [
            { headline: "Tesla Q1 deliveries miss estimates for second consecutive quarter", sentiment: -0.81, label: "negative", time: "2h ago" },
            { headline: "Musk confirms Cybertruck recall expanded to 46,000 vehicles", sentiment: -0.73, label: "negative", time: "5h ago" },
            { headline: "Tesla FSD v13 shows improved urban performance in beta testing", sentiment: 0.41, label: "positive", time: "8h ago" },
            { headline: "Germany Gigafactory output falls 20% short of 2025 targets", sentiment: -0.62, label: "negative", time: "12h ago" },
            { headline: "New Model Y refresh gains traction in Chinese market", sentiment: 0.38, label: "positive", time: "1d ago" },
        ],
        stats: { accuracy: 0.638, precision: 0.652, recall: 0.621, f1: 0.636, total_trades: 149 },
    },
    "BTC-USD": {
        predict: {
            ticker: "BTC-USD", prediction: "Flat", predicted_class: 1,
            confidence: 0.511, feature_date: "2025-05-02",
            probabilities: { Down: 0.271, Flat: 0.511, Up: 0.218 },
            sentiment_score: 0.04,
            top_headline: "Bitcoin consolidates near $97,000 as ETF inflows slow",
            feature_contributions: [
                { feature: "sentiment_volatility", value: 0.29 }, { feature: "rsi_14", value: -0.22 },
                { feature: "mean_sentiment", value: 0.11 }, { feature: "bb_width", value: 0.18 },
                { feature: "volume_ratio", value: -0.14 }, { feature: "negative_spike_flag", value: -0.12 },
                { feature: "headline_volume", value: 0.09 }, { feature: "macd_signal", value: -0.08 },
                { feature: "return_5d", value: 0.06 }, { feature: "sma_ratio_20_50", value: -0.04 },
            ],
        },
        sentiment: {
            ticker: "BTC-USD", days: 7,
            trend: [
                { date: "04-26", mean_sentiment: 0.14, headline_volume: 31, mean_positive: 0.38, mean_negative: 0.24 },
                { date: "04-27", mean_sentiment: -0.09, headline_volume: 28, mean_positive: 0.29, mean_negative: 0.38 },
                { date: "04-28", mean_sentiment: 0.21, headline_volume: 42, mean_positive: 0.44, mean_negative: 0.23 },
                { date: "04-29", mean_sentiment: 0.08, headline_volume: 35, mean_positive: 0.33, mean_negative: 0.25 },
                { date: "04-30", mean_sentiment: -0.13, headline_volume: 39, mean_positive: 0.27, mean_negative: 0.40 },
                { date: "05-01", mean_sentiment: 0.06, headline_volume: 27, mean_positive: 0.32, mean_negative: 0.26 },
                { date: "05-02", mean_sentiment: 0.04, headline_volume: 33, mean_positive: 0.31, mean_negative: 0.27 },
            ],
        },
        history: [
            { date: "04-14", close: 84100, volume: 28_000_000_000 }, { date: "04-15", close: 86800, volume: 31_000_000_000 },
            { date: "04-16", close: 85400, volume: 34_000_000_000 }, { date: "04-17", close: 83900, volume: 38_000_000_000 },
            { date: "04-22", close: 87200, volume: 27_000_000_000 }, { date: "04-23", close: 89600, volume: 24_000_000_000 },
            { date: "04-24", close: 91300, volume: 29_000_000_000 }, { date: "04-25", close: 93800, volume: 33_000_000_000 },
            { date: "04-28", close: 95100, volume: 31_000_000_000 }, { date: "04-29", close: 96700, volume: 28_000_000_000 },
            { date: "04-30", close: 94200, volume: 35_000_000_000 }, { date: "05-01", close: 97400, volume: 30_000_000_000 },
            { date: "05-02", close: 96900, volume: 32_000_000_000 },
        ],
        headlines: [
            { headline: "Bitcoin consolidates near $97,000 as ETF inflows slow", sentiment: 0.12, label: "neutral", time: "1h ago" },
            { headline: "BlackRock IBIT sees first weekly outflow since January launch", sentiment: -0.48, label: "negative", time: "4h ago" },
            { headline: "El Salvador doubles Bitcoin reserves in surprise treasury move", sentiment: 0.59, label: "positive", time: "7h ago" },
            { headline: "Fed minutes suggest prolonged high rates, crypto reacts cautiously", sentiment: -0.31, label: "negative", time: "10h ago" },
            { headline: "Bitcoin Lightning Network capacity hits all-time high", sentiment: 0.44, label: "positive", time: "1d ago" },
        ],
        stats: { accuracy: 0.601, precision: 0.614, recall: 0.589, f1: 0.601, total_trades: 131 },
    },
};

// ─── Portfolio heatmap data ────────────────────────────────────────────────────
const PORTFOLIO_SUMMARY = [
    { ticker: "AAPL", signal: "BUY", conf: 0.812, sentiment: 0.34, change: +2.34, price: 186.2 },
    { ticker: "MSFT", signal: "BUY", conf: 0.741, sentiment: 0.28, change: +1.27, price: 444.8 },
    { ticker: "NVDA", signal: "BUY", conf: 0.889, sentiment: 0.61, change: +3.81, price: 988.2 },
    { ticker: "TSLA", signal: "SELL", conf: 0.627, sentiment: -0.29, change: -3.38, price: 163.4 },
    { ticker: "BTC-USD", signal: "HOLD", conf: 0.511, sentiment: 0.04, change: -0.51, price: 96900 },
];

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #0d0f12;
    --surface:   #13161b;
    --card:      #181c22;
    --border:    #22282f;
    --border-hi: #2d3440;
    --text:      #e4e8ef;
    --muted:     #5a6475;
    --dim:       #3a4150;
    --green:     #00d97e;
    --green-dim: rgba(0,217,126,0.10);
    --red:       #ff4757;
    --red-dim:   rgba(255,71,87,0.10);
    --amber:     #ffc107;
    --amber-dim: rgba(255,193,7,0.10);
    --blue:      #4d9fff;
    --blue-dim:  rgba(77,159,255,0.10);
    --accent:    #00d97e;
  }

  body { background: var(--bg); color: var(--text); font-family: 'Syne', sans-serif; }

  .mono { font-family: 'JetBrains Mono', monospace; }

  /* ── Layout ── */
  .shell { min-height: 100vh; display: flex; flex-direction: column; }

  .topbar {
    height: 52px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; background: var(--surface);
    position: sticky; top: 0; z-index: 100;
  }
  .topbar-brand { display: flex; align-items: center; gap: 10px; }
  .topbar-brand .dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--green);
    box-shadow: 0 0 8px var(--green); animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .topbar-brand h1 { font-size: 13px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text); }
  .topbar-right { display: flex; align-items: center; gap: 16px; }
  .tag { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500;
         padding: 3px 8px; border-radius: 3px; letter-spacing: 0.06em; text-transform: uppercase; }
  .tag-green { background: var(--green-dim); color: var(--green); border: 1px solid rgba(0,217,126,0.2); }
  .tag-amber { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(255,193,7,0.2); }
  .tag-red   { background: var(--red-dim);   color: var(--red);   border: 1px solid rgba(255,71,87,0.2);  }
  .tag-blue  { background: var(--blue-dim);  color: var(--blue);  border: 1px solid rgba(77,159,255,0.2); }
  .tag-dim   { background: rgba(90,100,117,0.15); color: var(--muted); border: 1px solid var(--border); }

  .main-grid {
    display: grid;
    grid-template-columns: 260px 1fr;
    grid-template-rows: auto;
    gap: 0;
    flex: 1;
  }

  /* ── Sidebar ── */
  .sidebar {
    border-right: 1px solid var(--border);
    background: var(--surface);
    display: flex; flex-direction: column;
  }
  .sidebar-section { padding: 16px; border-bottom: 1px solid var(--border); }
  .sidebar-label { font-size: 9px; font-weight: 700; letter-spacing: 0.14em;
                   text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }

  .ticker-btn {
    width: 100%; display: flex; align-items: center; justify-content: space-between;
    padding: 8px 10px; border-radius: 6px; cursor: pointer; border: none;
    background: transparent; color: var(--text); margin-bottom: 2px;
    transition: background 0.15s;
  }
  .ticker-btn:hover { background: var(--card); }
  .ticker-btn.active { background: var(--card); border: 1px solid var(--border-hi); }
  .ticker-btn-left { display: flex; align-items: center; gap: 8px; }
  .ticker-name { font-size: 12px; font-weight: 700; letter-spacing: 0.04em; }
  .ticker-price { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }

  .signal-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .signal-dot.buy  { background: var(--green); box-shadow: 0 0 5px var(--green); }
  .signal-dot.sell { background: var(--red);   box-shadow: 0 0 5px var(--red);   }
  .signal-dot.hold { background: var(--amber); box-shadow: 0 0 5px var(--amber); }

  /* ── Content ── */
  .content { padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }

  /* ── Cards ── */
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; overflow: hidden;
  }
  .card-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; border-bottom: 1px solid var(--border);
  }
  .card-title { font-size: 11px; font-weight: 700; letter-spacing: 0.10em; text-transform: uppercase; color: var(--muted); }
  .card-body { padding: 18px; }

  /* ── Top row grid ── */
  .top-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }

  /* ── Prediction Card ── */
  .pred-signal {
    font-size: 42px; font-weight: 800; letter-spacing: -0.02em; line-height: 1;
    font-family: 'Syne', sans-serif;
  }
  .pred-signal.up   { color: var(--green); }
  .pred-signal.down { color: var(--red); }
  .pred-signal.flat { color: var(--amber); }
  .pred-sub { font-size: 11px; color: var(--muted); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }

  .conf-bar-wrap { margin-top: 16px; }
  .conf-label { display: flex; justify-content: space-between; margin-bottom: 6px; }
  .conf-label span { font-size: 10px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
  .conf-label strong { font-size: 10px; font-family: 'JetBrains Mono', monospace; }
  .conf-track { height: 4px; background: var(--border); border-radius: 99px; overflow: hidden; }
  .conf-fill { height: 100%; border-radius: 99px; transition: width 0.6s cubic-bezier(.4,0,.2,1); }

  .prob-row { display: flex; gap: 8px; margin-top: 14px; }
  .prob-item { flex: 1; background: var(--surface); border: 1px solid var(--border);
               border-radius: 6px; padding: 8px; text-align: center; }
  .prob-item .lbl { font-size: 9px; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
  .prob-item .val { font-size: 13px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

  /* ── Sentiment meter ── */
  .sent-value {
    font-size: 36px; font-weight: 800; font-family: 'JetBrains Mono', monospace; line-height: 1;
  }
  .sent-gauge { margin-top: 14px; position: relative; height: 4px; background: linear-gradient(to right, var(--red) 0%, var(--border-hi) 50%, var(--green) 100%); border-radius: 99px; }
  .sent-needle {
    position: absolute; top: 50%; transform: translate(-50%, -50%);
    width: 12px; height: 12px; border-radius: 50%; background: white;
    border: 2px solid var(--bg); box-shadow: 0 0 6px rgba(255,255,255,0.4);
    transition: left 0.6s cubic-bezier(.4,0,.2,1);
  }
  .sent-axis { display: flex; justify-content: space-between; margin-top: 6px; }
  .sent-axis span { font-size: 9px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

  /* ── Stats card ── */
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-item { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 12px; }
  .stat-item .lbl { font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
  .stat-item .val { font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .stat-item .sub { font-size: 9px; color: var(--muted); margin-top: 2px; }

  /* ── Charts ── */
  .chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .chart-full { width: 100%; }

  /* ── Headlines ── */
  .headline-item {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 12px 0; border-bottom: 1px solid var(--border);
  }
  .headline-item:last-child { border-bottom: none; }
  .headline-text { flex: 1; font-size: 12px; line-height: 1.55; color: var(--text); }
  .headline-meta { font-size: 10px; color: var(--muted); margin-top: 3px; font-family: 'JetBrains Mono', monospace; }
  .sent-score { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; flex-shrink: 0; padding-top: 1px; }

  /* ── SHAP ── */
  .shap-row {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 0; border-bottom: 1px solid var(--border);
  }
  .shap-row:last-child { border-bottom: none; }
  .shap-feat { width: 160px; font-size: 11px; font-family: 'JetBrains Mono', monospace; color: var(--muted); flex-shrink: 0; }
  .shap-bar-wrap { flex: 1; height: 6px; background: var(--surface); border-radius: 99px; overflow: hidden; }
  .shap-bar { height: 100%; border-radius: 99px; transition: width 0.5s; }
  .shap-val { width: 52px; text-align: right; font-size: 10px; font-family: 'JetBrains Mono', monospace; font-weight: 600; flex-shrink: 0; }

  /* ── Portfolio heatmap ── */
  .heat-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
  .heat-cell {
    border-radius: 8px; padding: 14px; border: 1px solid var(--border);
    display: flex; flex-direction: column; gap: 6px;
  }
  .heat-ticker { font-size: 13px; font-weight: 800; letter-spacing: 0.03em; }
  .heat-price  { font-size: 11px; font-family: 'JetBrains Mono', monospace; color: var(--muted); }
  .heat-change { font-size: 12px; font-family: 'JetBrains Mono', monospace; font-weight: 600; }
  .heat-signal { margin-top: 4px; }

  /* ── Tooltip ── */
  .custom-tip { background: var(--card); border: 1px solid var(--border-hi); border-radius: 6px; padding: 10px 13px; }
  .custom-tip .ct-label { font-size: 10px; color: var(--muted); font-family: 'JetBrains Mono', monospace; margin-bottom: 4px; }
  .custom-tip .ct-val   { font-size: 12px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

  /* ── Tab bar ── */
  .tabs { display: flex; gap: 2px; padding: 16px 18px 0; }
  .tab-btn {
    padding: 6px 14px; font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; border-radius: 4px 4px 0 0; border: none; cursor: pointer;
    background: transparent; color: var(--muted); border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab-btn.active { color: var(--text); border-bottom-color: var(--accent); }
  .tab-btn:hover:not(.active) { color: var(--text); }

  /* ── Overlay chart ── */
  .overlay-note { font-size: 10px; color: var(--muted); font-family: 'JetBrains Mono', monospace;
                  padding: 6px 18px 14px; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 99px; }

  /* ── Loading shimmer ── */
  @keyframes shimmer { 0%{opacity:0.4} 50%{opacity:0.8} 100%{opacity:0.4} }
  .shimmer { animation: shimmer 1.6s infinite; background: var(--border); border-radius: 4px; }
`;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function signalLabel(pred) {
    if (pred === "Up") return "BUY";
    if (pred === "Down") return "SELL";
    return "HOLD";
}
function signalClass(pred) {
    if (pred === "Up") return "up";
    if (pred === "Down") return "down";
    return "flat";
}
function signalTagClass(pred) {
    if (pred === "Up") return "tag-green";
    if (pred === "Down") return "tag-red";
    return "tag-amber";
}
function sentColor(v) {
    if (v > 0.15) return "var(--green)";
    if (v < -0.15) return "var(--red)";
    return "var(--amber)";
}
function fmtPrice(ticker, price) {
    if (ticker === "BTC-USD") return `$${price.toLocaleString()}`;
    return `$${price.toFixed(2)}`;
}
function fmtVol(v) {
    if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
    return v.toLocaleString();
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
const ChartTip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="custom-tip">
            <div className="ct-label">{label}</div>
            {payload.map((p, i) => (
                <div key={i} className="ct-val" style={{ color: p.color }}>
                    {p.name}: {typeof p.value === "number" ? p.value.toFixed(4) : p.value}
                </div>
            ))}
        </div>
    );
};

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
    const [ticker, setTicker] = useState("NVDA");
    const [tab, setTab] = useState("overview"); // overview | shap | portfolio
    const [loading, setLoading] = useState(false);

    const data = MOCK[ticker];
    const pred = data.predict;
    const sent = data.sentiment.trend;
    const hist = data.history;
    const headlines = data.headlines;
    const stats = data.stats;

    // Merge price + sentiment for overlay chart
    const overlayData = hist.map((h, i) => ({
        ...h,
        sentiment: sent[Math.max(0, sent.length - hist.length + i)]?.mean_sentiment ?? 0,
    }));

    const confColor = pred.predicted_class === 2 ? "var(--green)" : pred.predicted_class === 0 ? "var(--red)" : "var(--amber)";
    const sentNeedleLeft = `${Math.round(((pred.sentiment_score + 1) / 2) * 100)}%`;

    const maxShap = Math.max(...pred.feature_contributions.map(f => Math.abs(f.value)));

    return (
        <>
            <style>{styles}</style>
            <div className="shell">

                {/* ── Topbar ── */}
                <div className="topbar">
                    <div className="topbar-brand">
                        <div className="dot" />
                        <h1>Stock Sentiment Analyzer</h1>
                        <span className="tag tag-dim mono" style={{ fontSize: 9 }}>Phase 5 — Dashboard</span>
                    </div>
                    <div className="topbar-right">
                        <span className="tag tag-green">Live</span>
                        <span className="tag tag-dim mono" style={{ fontSize: 9 }}>FinBERT · XGBoost</span>
                        <span className="mono" style={{ fontSize: 10, color: "var(--muted)" }}>
                            {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} EST
                        </span>
                    </div>
                </div>

                {/* ── Main grid ── */}
                <div className="main-grid">

                    {/* ── Sidebar ── */}
                    <div className="sidebar">
                        <div className="sidebar-section">
                            <div className="sidebar-label">Portfolio</div>
                            {PORTFOLIO_SUMMARY.map(t => (
                                <button
                                    key={t.ticker}
                                    className={`ticker-btn ${ticker === t.ticker ? "active" : ""}`}
                                    onClick={() => setTicker(t.ticker)}
                                >
                                    <div className="ticker-btn-left">
                                        <div className={`signal-dot ${t.signal.toLowerCase()}`} />
                                        <div>
                                            <div className="ticker-name">{t.ticker}</div>
                                            <div className="ticker-price">{fmtPrice(t.ticker, t.price)}</div>
                                        </div>
                                    </div>
                                    <div style={{ textAlign: "right" }}>
                                        <span className={`tag ${t.signal === "BUY" ? "tag-green" : t.signal === "SELL" ? "tag-red" : "tag-amber"}`} style={{ fontSize: 9 }}>
                                            {t.signal}
                                        </span>
                                        <div className="mono" style={{ fontSize: 10, marginTop: 3, color: t.change >= 0 ? "var(--green)" : "var(--red)" }}>
                                            {t.change >= 0 ? "+" : ""}{t.change.toFixed(2)}%
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>

                        <div className="sidebar-section">
                            <div className="sidebar-label">Model</div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                {[["Algorithm", "XGBoost"], ["Features", "NLP + OHLCV"], ["Validation", "Walk-forward"], ["Horizon", "1-day ahead"]].map(([k, v]) => (
                                    <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                                        <span style={{ fontSize: 10, color: "var(--muted)" }}>{k}</span>
                                        <span className="mono" style={{ fontSize: 10, color: "var(--text)" }}>{v}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="sidebar-section" style={{ flex: 1 }}>
                            <div className="sidebar-label">Navigation</div>
                            {[["overview", "Overview"], ["shap", "Explain Prediction"], ["portfolio", "Portfolio View"]].map(([id, label]) => (
                                <button
                                    key={id}
                                    className={`ticker-btn ${tab === id ? "active" : ""}`}
                                    style={{ justifyContent: "flex-start" }}
                                    onClick={() => setTab(id)}
                                >
                                    <span className="ticker-name" style={{ fontWeight: tab === id ? 700 : 500, fontSize: 11 }}>{label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* ── Content ── */}
                    <div className="content">

                        {/* Ticker header */}
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                <h2 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.01em" }}>{ticker}</h2>
                                <span className={`tag ${signalTagClass(pred.prediction)}`} style={{ fontSize: 11, padding: "4px 10px" }}>
                                    {signalLabel(pred.prediction)}
                                </span>
                                <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>
                                    as of {pred.feature_date}
                                </span>
                            </div>
                            <div style={{ display: "flex", gap: 8 }}>
                                {["overview", "shap", "portfolio"].map((id, i) => (
                                    <button
                                        key={id}
                                        onClick={() => setTab(id)}
                                        style={{
                                            padding: "5px 12px", fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
                                            textTransform: "uppercase", borderRadius: 5, cursor: "pointer",
                                            border: `1px solid ${tab === id ? "var(--border-hi)" : "var(--border)"}`,
                                            background: tab === id ? "var(--card)" : "transparent",
                                            color: tab === id ? "var(--text)" : "var(--muted)",
                                        }}
                                    >
                                        {["Overview", "Explain", "Portfolio"][i]}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* ══ OVERVIEW TAB ══ */}
                        {tab === "overview" && (
                            <>
                                {/* Top row: prediction | sentiment | stats */}
                                <div className="top-row">

                                    {/* Prediction card */}
                                    <div className="card">
                                        <div className="card-header">
                                            <span className="card-title">Prediction</span>
                                            <span className="tag tag-dim mono">{pred.confidence >= 0.75 ? "High" : pred.confidence >= 0.55 ? "Med" : "Low"} Confidence</span>
                                        </div>
                                        <div className="card-body">
                                            <div className={`pred-signal ${signalClass(pred.prediction)}`}>{signalLabel(pred.prediction)}</div>
                                            <div className="pred-sub">Direction: {pred.prediction} · 1d horizon</div>
                                            <div className="conf-bar-wrap">
                                                <div className="conf-label">
                                                    <span>Confidence</span>
                                                    <strong style={{ color: confColor }}>{(pred.confidence * 100).toFixed(1)}%</strong>
                                                </div>
                                                <div className="conf-track">
                                                    <div className="conf-fill" style={{ width: `${pred.confidence * 100}%`, background: confColor }} />
                                                </div>
                                            </div>
                                            <div className="prob-row">
                                                {Object.entries(pred.probabilities).map(([k, v]) => (
                                                    <div className="prob-item" key={k}>
                                                        <div className="lbl">{k}</div>
                                                        <div className="val" style={{ color: k === "Up" ? "var(--green)" : k === "Down" ? "var(--red)" : "var(--amber)" }}>
                                                            {(v * 100).toFixed(1)}%
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Sentiment card */}
                                    <div className="card">
                                        <div className="card-header">
                                            <span className="card-title">Sentiment Score</span>
                                            <span className="tag tag-dim mono">FinBERT · 7d avg</span>
                                        </div>
                                        <div className="card-body">
                                            <div className="sent-value" style={{ color: sentColor(pred.sentiment_score) }}>
                                                {pred.sentiment_score > 0 ? "+" : ""}{pred.sentiment_score.toFixed(3)}
                                            </div>
                                            <div className="pred-sub" style={{ marginTop: 4 }}>
                                                {pred.sentiment_score > 0.15 ? "Positive news flow" : pred.sentiment_score < -0.15 ? "Negative news flow" : "Neutral / mixed"}
                                            </div>
                                            <div className="sent-gauge" style={{ marginTop: 18 }}>
                                                <div className="sent-needle" style={{ left: sentNeedleLeft }} />
                                            </div>
                                            <div className="sent-axis">
                                                <span>−1.0</span><span>Bearish</span><span>0</span><span>Bullish</span><span>+1.0</span>
                                            </div>
                                            <div style={{ marginTop: 14, padding: "10px 12px", background: "var(--surface)", borderRadius: 6, border: "1px solid var(--border)" }}>
                                                <div style={{ fontSize: 9, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>Top Headline</div>
                                                <div style={{ fontSize: 11, lineHeight: 1.5, color: "var(--text)" }}>{pred.top_headline}</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Stats card */}
                                    <div className="card">
                                        <div className="card-header">
                                            <span className="card-title">Model Performance</span>
                                            <span className="tag tag-dim mono">Backtested</span>
                                        </div>
                                        <div className="card-body">
                                            <div className="stat-grid">
                                                {[
                                                    ["Accuracy", `${(stats.accuracy * 100).toFixed(1)}%`, "walk-forward CV"],
                                                    ["F1 Score", stats.f1.toFixed(3), "macro avg"],
                                                    ["Precision", `${(stats.precision * 100).toFixed(1)}%`, "class-weighted"],
                                                    ["Recall", `${(stats.recall * 100).toFixed(1)}%`, "class-weighted"],
                                                ].map(([lbl, val, sub]) => (
                                                    <div className="stat-item" key={lbl}>
                                                        <div className="lbl">{lbl}</div>
                                                        <div className="val" style={{ color: "var(--green)" }}>{val}</div>
                                                        <div className="sub">{sub}</div>
                                                    </div>
                                                ))}
                                            </div>
                                            <div style={{ marginTop: 12, padding: "8px 12px", background: "var(--surface)", borderRadius: 6, border: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                                <span style={{ fontSize: 10, color: "var(--muted)" }}>Total predictions</span>
                                                <span className="mono" style={{ fontSize: 13, fontWeight: 700 }}>{stats.total_trades}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Charts row */}
                                <div className="chart-row">

                                    {/* Sentiment trend chart */}
                                    <div className="card">
                                        <div className="card-header">
                                            <span className="card-title">Sentiment Trend · 7-day</span>
                                            <span className="tag tag-dim mono">{ticker}</span>
                                        </div>
                                        <div className="card-body" style={{ paddingTop: 8 }}>
                                            <ResponsiveContainer width="100%" height={180}>
                                                <AreaChart data={sent} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
                                                    <defs>
                                                        <linearGradient id="gPos" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="var(--green)" stopOpacity={0.25} />
                                                            <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
                                                        </linearGradient>
                                                        <linearGradient id="gNeg" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="var(--red)" stopOpacity={0.25} />
                                                            <stop offset="95%" stopColor="var(--red)" stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                    <YAxis tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} domain={[-1, 1]} tickCount={5} />
                                                    <Tooltip content={<ChartTip />} />
                                                    <ReferenceLine y={0} stroke="var(--border-hi)" strokeDasharray="4 4" />
                                                    <Area type="monotone" dataKey="mean_positive" name="positive" stroke="var(--green)" strokeWidth={1.5} fill="url(#gPos)" dot={false} />
                                                    <Area type="monotone" dataKey="mean_negative" name="negative" stroke="var(--red)" strokeWidth={1.5} fill="url(#gNeg)" dot={false} />
                                                    <Line type="monotone" dataKey="mean_sentiment" name="net" stroke="var(--amber)" strokeWidth={2} dot={false} />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>

                                    {/* Volume chart */}
                                    <div className="card">
                                        <div className="card-header">
                                            <span className="card-title">Headline Volume</span>
                                            <span className="tag tag-dim mono">articles / day</span>
                                        </div>
                                        <div className="card-body" style={{ paddingTop: 8 }}>
                                            <ResponsiveContainer width="100%" height={180}>
                                                <BarChart data={sent} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                    <YAxis tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                    <Tooltip content={<ChartTip />} />
                                                    <Bar dataKey="headline_volume" name="articles" radius={[3, 3, 0, 0]}>
                                                        {sent.map((_, i) => (
                                                            <Cell key={i} fill={_.mean_sentiment > 0 ? "rgba(0,217,126,0.5)" : "rgba(255,71,87,0.5)"} />
                                                        ))}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>

                                {/* Price + sentiment overlay */}
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Price × Sentiment Overlay</span>
                                        <div style={{ display: "flex", gap: 8 }}>
                                            <span className="tag" style={{ background: "rgba(77,159,255,0.1)", color: "var(--blue)", border: "1px solid rgba(77,159,255,0.2)", fontSize: 9 }}>▬ Price</span>
                                            <span className="tag" style={{ background: "var(--amber-dim)", color: "var(--amber)", border: "1px solid rgba(255,193,7,0.2)", fontSize: 9 }}>▬ Sentiment</span>
                                        </div>
                                    </div>
                                    <div className="overlay-note">Dual-axis: price (left) · net sentiment (right)</div>
                                    <div style={{ padding: "0 18px 18px" }}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <AreaChart data={overlayData} margin={{ top: 4, right: 40, left: -10, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="gPrice" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="var(--blue)" stopOpacity={0.2} />
                                                        <stop offset="95%" stopColor="var(--blue)" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                                <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                <YAxis yAxisId="price" orientation="left" tick={{ fontSize: 9, fill: "var(--blue)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                <YAxis yAxisId="sent" orientation="right" tick={{ fontSize: 9, fill: "var(--amber)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} domain={[-1, 1]} />
                                                <Tooltip content={<ChartTip />} />
                                                <ReferenceLine yAxisId="sent" y={0} stroke="var(--border-hi)" strokeDasharray="4 4" />
                                                <Area yAxisId="price" type="monotone" dataKey="close" name="price" stroke="var(--blue)" strokeWidth={2} fill="url(#gPrice)" dot={false} />
                                                <Line yAxisId="sent" type="monotone" dataKey="sentiment" name="sentiment" stroke="var(--amber)" strokeWidth={2} dot={false} strokeDasharray="5 3" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Headlines */}
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Recent Headlines</span>
                                        <span className="tag tag-dim mono">FinBERT scored</span>
                                    </div>
                                    <div className="card-body" style={{ paddingTop: 4, paddingBottom: 4 }}>
                                        {headlines.map((h, i) => (
                                            <div className="headline-item" key={i}>
                                                <div className="sent-score" style={{ color: sentColor(h.sentiment) }}>
                                                    {h.sentiment > 0 ? "+" : ""}{h.sentiment.toFixed(2)}
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <div className="headline-text">{h.headline}</div>
                                                    <div className="headline-meta">{h.time}</div>
                                                </div>
                                                <span className={`tag ${h.label === "positive" ? "tag-green" : h.label === "negative" ? "tag-red" : "tag-amber"}`} style={{ fontSize: 9, flexShrink: 0 }}>
                                                    {h.label}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ══ SHAP TAB ══ */}
                        {tab === "shap" && (
                            <>
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Explain This Prediction — SHAP Waterfall</span>
                                        <span className={`tag ${signalTagClass(pred.prediction)}`}>{ticker} → {signalLabel(pred.prediction)}</span>
                                    </div>
                                    <div className="card-body">
                                        <div style={{ marginBottom: 16, padding: "10px 14px", background: "var(--surface)", borderRadius: 6, border: "1px solid var(--border)", fontSize: 11, color: "var(--muted)", lineHeight: 1.6 }}>
                                            SHAP (SHapley Additive exPlanations) shows how each feature pushed the prediction toward <strong style={{ color: "var(--green)" }}>Up</strong> or <strong style={{ color: "var(--red)" }}>Down</strong>. Positive values (green) support the predicted class; negative values (red) oppose it.
                                        </div>
                                        {pred.feature_contributions.map((f, i) => {
                                            const pct = Math.abs(f.value) / maxShap * 100;
                                            const isPos = f.value > 0;
                                            return (
                                                <div className="shap-row" key={i}>
                                                    <div className="shap-feat">{f.feature}</div>
                                                    <div className="shap-bar-wrap">
                                                        <div className="shap-bar" style={{
                                                            width: `${pct}%`,
                                                            background: isPos ? "var(--green)" : "var(--red)",
                                                            opacity: 0.7 + 0.3 * (pct / 100),
                                                        }} />
                                                    </div>
                                                    <div className="shap-val" style={{ color: isPos ? "var(--green)" : "var(--red)" }}>
                                                        {isPos ? "+" : ""}{f.value.toFixed(3)}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Raw feature table */}
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Feature Contributions Summary</span>
                                        <span className="tag tag-dim mono">top 10</span>
                                    </div>
                                    <div className="card-body" style={{ paddingTop: 6 }}>
                                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                            <div>
                                                <div style={{ fontSize: 9, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>Bullish Drivers ↑</div>
                                                {pred.feature_contributions.filter(f => f.value > 0).map((f, i) => (
                                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
                                                        <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{f.feature}</span>
                                                        <span className="mono" style={{ fontSize: 11, color: "var(--green)", fontWeight: 600 }}>+{f.value.toFixed(3)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                            <div>
                                                <div style={{ fontSize: 9, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>Bearish Drivers ↓</div>
                                                {pred.feature_contributions.filter(f => f.value < 0).map((f, i) => (
                                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
                                                        <span className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{f.feature}</span>
                                                        <span className="mono" style={{ fontSize: 11, color: "var(--red)", fontWeight: 600 }}>{f.value.toFixed(3)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* ══ PORTFOLIO TAB ══ */}
                        {tab === "portfolio" && (
                            <>
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Portfolio Heatmap</span>
                                        <span className="tag tag-dim mono">All Tickers · Live Signals</span>
                                    </div>
                                    <div className="card-body">
                                        <div className="heat-grid">
                                            {PORTFOLIO_SUMMARY.map(t => {
                                                const isUp = t.change > 0;
                                                const isDown = t.change < 0;
                                                return (
                                                    <div
                                                        key={t.ticker}
                                                        className="heat-cell"
                                                        style={{
                                                            background: t.signal === "BUY" ? "rgba(0,217,126,0.06)" :
                                                                t.signal === "SELL" ? "rgba(255,71,87,0.06)" :
                                                                    "rgba(255,193,7,0.05)",
                                                            border: `1px solid ${t.signal === "BUY" ? "rgba(0,217,126,0.2)" :
                                                                    t.signal === "SELL" ? "rgba(255,71,87,0.2)" :
                                                                        "rgba(255,193,7,0.15)"
                                                                }`,
                                                            cursor: "pointer",
                                                        }}
                                                        onClick={() => { setTicker(t.ticker); setTab("overview"); }}
                                                    >
                                                        <div className="heat-ticker">{t.ticker}</div>
                                                        <div className="heat-price">{fmtPrice(t.ticker, t.price)}</div>
                                                        <div className="heat-change" style={{ color: isUp ? "var(--green)" : isDown ? "var(--red)" : "var(--muted)" }}>
                                                            {t.change >= 0 ? "+" : ""}{t.change.toFixed(2)}%
                                                        </div>
                                                        <div style={{ fontSize: 10, color: "var(--muted)", fontFamily: "JetBrains Mono" }}>
                                                            Sent: {t.sentiment > 0 ? "+" : ""}{t.sentiment.toFixed(2)}
                                                        </div>
                                                        <div className="heat-signal">
                                                            <span className={`tag ${t.signal === "BUY" ? "tag-green" : t.signal === "SELL" ? "tag-red" : "tag-amber"}`} style={{ fontSize: 9 }}>
                                                                {t.signal} · {(MOCK[t.ticker].predict.confidence * 100).toFixed(0)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>

                                {/* Cross-ticker accuracy comparison */}
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Model Accuracy by Ticker</span>
                                        <span className="tag tag-dim mono">Walk-forward backtest</span>
                                    </div>
                                    <div className="card-body" style={{ paddingTop: 8 }}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <BarChart
                                                data={PORTFOLIO_SUMMARY.map(t => ({ ticker: t.ticker, accuracy: MOCK[t.ticker].stats.accuracy, f1: MOCK[t.ticker].stats.f1 }))}
                                                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                                <XAxis dataKey="ticker" tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                <YAxis tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} domain={[0.5, 0.8]} />
                                                <Tooltip content={<ChartTip />} />
                                                <Bar dataKey="accuracy" name="accuracy" radius={[3, 3, 0, 0]} fill="rgba(0,217,126,0.6)" />
                                                <Bar dataKey="f1" name="f1" radius={[3, 3, 0, 0]} fill="rgba(77,159,255,0.5)" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                        <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                                            <span className="tag" style={{ background: "rgba(0,217,126,0.1)", color: "var(--green)", border: "1px solid rgba(0,217,126,0.2)", fontSize: 9 }}>▬ Accuracy</span>
                                            <span className="tag" style={{ background: "var(--blue-dim)", color: "var(--blue)", border: "1px solid rgba(77,159,255,0.2)", fontSize: 9 }}>▬ F1 Score</span>
                                        </div>
                                    </div>
                                </div>

                                {/* All tickers sentiment comparison */}
                                <div className="card">
                                    <div className="card-header">
                                        <span className="card-title">Cross-Ticker Sentiment Trend</span>
                                        <span className="tag tag-dim mono">7-day net sentiment</span>
                                    </div>
                                    <div className="card-body" style={{ paddingTop: 8 }}>
                                        <ResponsiveContainer width="100%" height={200}>
                                            <LineChart margin={{ top: 4, right: 4, left: -28, bottom: 0 }}
                                                data={MOCK["AAPL"].sentiment.trend.map((_, i) => ({
                                                    date: _.date,
                                                    AAPL: MOCK["AAPL"].sentiment.trend[i]?.mean_sentiment,
                                                    MSFT: MOCK["MSFT"].sentiment.trend[i]?.mean_sentiment,
                                                    NVDA: MOCK["NVDA"].sentiment.trend[i]?.mean_sentiment,
                                                    TSLA: MOCK["TSLA"].sentiment.trend[i]?.mean_sentiment,
                                                    BTC: MOCK["BTC-USD"].sentiment.trend[i]?.mean_sentiment,
                                                }))}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                                <XAxis dataKey="date" tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                                                <YAxis tick={{ fontSize: 9, fill: "var(--muted)", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} domain={[-1, 1]} />
                                                <Tooltip content={<ChartTip />} />
                                                <ReferenceLine y={0} stroke="var(--border-hi)" strokeDasharray="4 4" />
                                                {[["AAPL", "#a8b4ff"], ["MSFT", "#4d9fff"], ["NVDA", "#00d97e"], ["TSLA", "#ff4757"], ["BTC", "#ffc107"]].map(([k, c]) => (
                                                    <Line key={k} type="monotone" dataKey={k} stroke={c} strokeWidth={1.5} dot={false} />
                                                ))}
                                            </LineChart>
                                        </ResponsiveContainer>
                                        <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                                            {[["AAPL", "#a8b4ff"], ["MSFT", "#4d9fff"], ["NVDA", "#00d97e"], ["TSLA", "#ff4757"], ["BTC-USD", "#ffc107"]].map(([k, c]) => (
                                                <span key={k} style={{ fontSize: 9, fontFamily: "JetBrains Mono", color: c }}>▬ {k}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                    </div>
                </div>
            </div>
        </>
    );
}