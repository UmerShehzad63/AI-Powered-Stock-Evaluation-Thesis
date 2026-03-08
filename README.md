# AI-Powered Stock Evaluation Model
### Thesis Prototype — Integrated Signal Analysis

A multi-factor stock scoring system that combines fundamental analysis, AI-driven news sentiment, technical indicators, and derivatives data into a single composite score (0–100). Built with Python and Streamlit.

🔗 **Live Demo:** [Streamlit App](https://ai-powered-stock-evaluationthesis-um6.streamlit.app/)

---

## Overview

The model evaluates any US-listed stock or ETF by pulling real-time data across four analytical pillars and producing a composite signal score with a qualitative rating from **Strong Bearish** to **Strong Bullish**.

```
Composite Score = Fundamentals (40%) + Sentiment (25%) + Technical (20%) + Derivatives (15%)
```

Each pillar has its own scoring engine with transparent signal breakdowns visible in the UI.

---

## Scoring Architecture

### 🏢 Fundamentals (40% weight)
Five-factor model mirroring institutional equity research:

| Factor | Weight | Metrics |
|---|---|---|
| Profitability | 35% | ROE, Net Margin, ROA |
| Growth | 30% | Revenue Growth, EPS Growth |
| Valuation | 15% | Sector-relative P/E ratio |
| Financial Health | 10% | Debt-to-Equity |
| FCF Quality | 10% | Free Cashflow Yield |

- P/E is scored relative to **sector median** (e.g. Technology = 32x, Energy = 13x), not absolute thresholds
- Distressed companies (negative ROE or margins) are hard-capped at 35
- A **Piotroski F-Score** (9-signal accounting quality test) is displayed as a supplementary badge
- Scores ≥ 70 and ≤ 35 are amplified outward to increase spread

### 🤖 AI Sentiment (25% weight)
- Scrapes the 30 most recent headlines from FinViz
- Classifies each as Bullish / Bearish / Neutral using **LLaMA 3.3 70B** via Groq API
- Assigns an impact score (0–10) per headline
- Weighted signal ratio with neutral anchoring to prevent noise domination

### 📈 Technical Analysis (20% weight)
Eight binary signals with explicit weights:

| Signal | Weight |
|---|---|
| Price Above SMA 200 | 25% |
| Price Above SMA 50 | 20% |
| Golden Cross Active (SMA50 > SMA200) | 15% |
| MACD Bullish Cross | 15% |
| MACD Above Zero | 10% |
| RSI Not Overbought (< 75) | 8% |
| Price Above EMA 20 | 5% |
| Not At BB Upper Band | 2% |

Each signal passes (bullish weight) or fails (no contribution). Final score = sum of bullish weights / total weights × 100.

### 📉 Derivatives & Options (15% weight)
| Signal | Weight |
|---|---|
| Put/Call Open Interest Ratio | 30% |
| Short Float (trend-contextualised) | 20% |
| Days to Cover | 20% |
| Put/Call Volume Ratio | 15% |
| Implied Volatility | 15% |

Short interest signals are contextualised by the prevailing technical trend — high short float in a downtrend is bearish, in an uptrend it's a squeeze watch signal.

---

## Composite Score Ratings

| Score | Rating |
|---|---|
| 80 – 100 | Strong Bullish 🐂 |
| 60 – 79 | Bullish Bias 📈 |
| 40 – 59 | Neutral / Mixed 😐 |
| 20 – 39 | Bearish Bias 📉 |
| 0 – 19 | Strong Bearish 🐻 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Market Data | yfinance |
| Technical Indicators | ta (Technical Analysis library) |
| Charts | Plotly |
| News Scraping | BeautifulSoup + FinViz |
| AI Sentiment | Groq API (LLaMA 3.3 70B / LLaMA 3.1 8B fallback) |
| Ticker Resolution | Yahoo Finance Search API |

---

## Project Structure

```
├── main.py           # Streamlit UI and dashboard layout
├── scorers.py        # All scoring engines (Technical, Fundamental, Sentiment, Derivatives)
├── data_loader.py    # Data fetching (yfinance, FinViz scraper, Groq AI)
├── utils.py          # Score normalisation and rating helpers
├── requirements.txt  # Python dependencies
└── sentiment analyzer/  # Standalone sentiment analysis module
```

---

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/UmerShehzad63/AI-Powered-Stock-Evaluation-Thesis.git
cd AI-Powered-Stock-Evaluation-Thesis
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure API keys**

Create a `.env` file in the root directory:
```
GROQ_KEYS=your_groq_api_key_1,your_groq_api_key_2
```

Or if deploying to Streamlit Cloud, add to `.streamlit/secrets.toml`:
```toml
GROQ_KEYS = "your_groq_api_key_1,your_groq_api_key_2"
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

**4. Run the app**
```bash
streamlit run main.py
```

---

## Usage

Enter any US stock ticker (`AAPL`, `NVDA`) or company name (`Apple`, `Nvidia`) in the search bar. The model resolves company names to tickers automatically via Yahoo Finance search.

The dashboard displays:
- Composite score and signal rating
- Insider transaction activity with direct links to OpenInsider
- Four signal panels with individual scores and transparent breakdowns
- Interactive candlestick chart with SMA 50/200 and Bollinger Bands overlay

---

## Limitations & Disclaimer

- **Data source:** All market data is sourced from Yahoo Finance via `yfinance`. Data accuracy is subject to Yahoo Finance's availability and update frequency.
- **Sentiment:** News is scraped from FinViz which may occasionally block automated requests. The model falls back gracefully when headlines are unavailable.
- **Options data:** Uses the nearest 20–40 day expiry options chain. Stocks without listed options will show N/A for derivative signals.
- **Not financial advice:** This tool is an academic prototype. Scores are algorithmic signals, not investment recommendations. Always conduct your own research before making investment decisions.

---

## Academic Context

This project implements and extends several academically validated frameworks:

- **Piotroski F-Score** (Piotroski, 2000) — 9-signal accounting quality test with documented 13.4% annual alpha over 20 years
- **Multi-factor equity scoring** — architecture consistent with Seeking Alpha Quant ratings (Value, Growth, Profitability, Momentum)
- **Sentiment-augmented models** — integrates LLM-based news classification as a forward-looking signal layer alongside lagging fundamental and technical indicators

---

*Built as a thesis prototype for academic evaluation of AI-assisted stock screening methodologies.*
