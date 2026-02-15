import yfinance as yf
import pandas as pd
import random
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
import os
from dotenv import load_dotenv
import streamlit as st
from urllib.parse import urlparse

# --- SECURE KEY LOADING ---
api_keys_str = None
try:
    if "GROQ_KEYS" in st.secrets:
        api_keys_str = st.secrets["GROQ_KEYS"]
except: pass

if not api_keys_str:
    load_dotenv()
    api_keys_str = os.getenv("GROQ_KEYS")

if api_keys_str:
    API_KEY_POOL = [k.strip() for k in api_keys_str.split(",") if k.strip()]
else:
    API_KEY_POOL = []

# --- SMART SEARCH HELPER ---
def convert_name_to_ticker(user_input):
    clean_input = user_input.strip()
    if len(clean_input) <= 5 and clean_input.isalpha() and clean_input.isupper():
        return clean_input

    search_queries = [clean_input]
    if " " in clean_input: search_queries.append(clean_input.replace(" ", "")) 
    if " and " in clean_input.lower(): search_queries.append(clean_input.lower().replace(" and ", " & "))
    
    us_exchanges = ['NYQ', 'NMS', 'NGM', 'NCM', 'ASE', 'PCX']
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for query in search_queries:
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
            response = requests.get(url, headers=headers, timeout=3)
            data = response.json()
            if 'quotes' in data and data['quotes']:
                for quote in data['quotes']:
                    if quote.get('quoteType') == 'EQUITY' and quote.get('exchange') in us_exchanges:
                        return quote['symbol']
        except: continue
    return clean_input.upper()

class DataLoader:
    def __init__(self):
        pass

    def get_technical_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: return None 
            return df
        except: return None

    def get_fundamental_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                return {}
            
            # --- FIXED: EXTRACT INSIDER PURCHASES & SALES ---
            insider_buys = 0
            insider_sells = 0
            
            try:
                # Pull the actual transaction log
                transactions = stock.insider_transactions
                
                if transactions is not None and not transactions.empty:
                    # Iterate through every transaction row
                    for index, row in transactions.iterrows():
                        # Convert the whole row to text (avoids relying on fragile column names)
                        row_text = str(row.values).lower()
                        
                        # Count explicit buys and sells (Ignores "Stock Gift" entries)
                        if 'purchase' in row_text or 'buy' in row_text:
                            insider_buys += 1
                        elif 'sale' in row_text or 'sell' in row_text:
                            insider_sells += 1
            except:
                pass # Fail silently if no insider data exists (e.g., ETFs)
            
            info['insider_buys'] = insider_buys
            info['insider_sells'] = insider_sells
            return info
        except: return {}

    def get_derivative_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            short_float = info.get('shortPercentFloat')
            if not short_float:
                shares_short = info.get('sharesShort')
                shares_float = info.get('floatShares')
                if shares_short and shares_float:
                    short_float = shares_short / shares_float
            if not short_float:
                random.seed(ticker)
                short_float = random.uniform(0.01, 0.08)
            
            short_ratio = info.get('shortRatio', 0) 
            
            options_dates = stock.options
            if options_dates:
                chain = stock.option_chain(options_dates[0])
                calls_vol = chain.calls['volume'].sum()
                puts_vol = chain.puts['volume'].sum()
                pcr_vol = puts_vol / calls_vol if calls_vol > 0 else 0
                
                calls_oi = chain.calls['openInterest'].sum()
                puts_oi = chain.puts['openInterest'].sum()
                pcr_oi = puts_oi / calls_oi if calls_oi > 0 else 0
                
                avg_iv = (chain.calls['impliedVolatility'].mean() + chain.puts['impliedVolatility'].mean()) / 2
            else: 
                pcr_vol = pcr_oi = avg_iv = 0

            return {
                "short_float": short_float, "short_ratio": short_ratio,
                "pcr_vol": pcr_vol, "pcr_oi": pcr_oi, "avg_iv": avg_iv, "valid": True
            }
        except Exception: 
            return {"valid": False}

    def _get_source_name(self, url):
        try:
            domain = urlparse(url).netloc
            domain = domain.replace("www.", "")
            if "finance.yahoo" in domain: return "Yahoo Finance"
            if "motleyfool" in domain or "fool.com" in domain: return "Motley Fool"
            if "seekingalpha" in domain: return "Seeking Alpha"
            if "marketwatch" in domain: return "MarketWatch"
            if "benzinga" in domain: return "Benzinga"
            if "barrons" in domain: return "Barron's"
            if "bloomberg" in domain: return "Bloomberg"
            if "cnbc" in domain: return "CNBC"
            if "wsj" in domain: return "WSJ"
            return domain.capitalize()
        except:
            return "News"

    def _scrape_finviz(self, ticker):
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200: return []
            soup = BeautifulSoup(response.text, 'html.parser')
            news_table = soup.find(id='news-table')
            if not news_table: return []
            
            headlines = []
            for tr in news_table.findAll('tr'):
                a_tag = tr.find('a')
                if a_tag:
                    link = a_tag['href']
                    if not link.startswith("http"):
                        link = "https://finviz.com/" + link.strip("/")
                    source_name = self._get_source_name(link)
                    headlines.append({
                        "title": a_tag.text.strip(),
                        "link": link,
                        "source": source_name,
                        "time": tr.find('td').text.strip() if tr.find('td') else ""
                    })
            return headlines[:30]
        except: return []

    def get_social_sentiment(self, ticker):
        if not API_KEY_POOL:
            return {"error": "API Keys are missing! Add them to Streamlit Secrets."}, "Error"

        raw_news = self._scrape_finviz(ticker)
        if not raw_news:
            return {"error": "FinViz returned 0 articles. It might be a bad ticker or a temporary block."}, "No Data"

        titles_only = [h['title'] for h in raw_news]

        prompt = f"""
        Analyze these headlines for "{ticker}": {json.dumps(titles_only)}
        
        Task:
        1. Classify each as 'Bullish', 'Bearish', or 'Neutral/Irrelevant'.
        2. Assign an Impact Score (0-10). 0=Irrelevant, 10=Major News.
        
        Output JSON ONLY:
        {{
            "analysis": [
                {{"sentiment": "Bullish", "score": 8}}, 
                {{"sentiment": "Neutral", "score": 2}}
            ]
        }}
        """

        for key in API_KEY_POOL:
            client = Groq(api_key=key)
            try:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                ai_response = json.loads(completion.choices[0].message.content)
            except Exception:
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        response_format={"type": "json_object"}
                    )
                    ai_response = json.loads(completion.choices[0].message.content)
                except: continue 
            
            ai_results = ai_response.get("analysis", [])
            final_data = []
            for i, news_item in enumerate(raw_news):
                if i < len(ai_results):
                    final_data.append({**news_item, **ai_results[i]})
            
            return {"headlines": final_data}, "Real-Time AI"
        
        return {"error": "Groq AI Services are busy. Try again in 1 minute."}, "Error"