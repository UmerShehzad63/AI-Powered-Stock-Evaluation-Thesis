import streamlit as st
import plotly.graph_objects as go
from data_loader import DataLoader, convert_name_to_ticker
from scorers import ScoringEngine
from utils import get_rating

st.set_page_config(page_title="Thesis Prototype", layout="wide", page_icon="📈")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-header { font-size: 2.5rem; font-weight: 800; text-align: center; background: -webkit-linear-gradient(45deg, #00CC96, #3783FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub-header { text-align: center; color: #888; margin-bottom: 30px; }
    
    /* Search Bar Styling */
    .stTextInput > div > div > input {
        background-color: #1F2329; color: white; border: 1px solid #373A40; border-radius: 12px; padding: 12px;
    }
    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #00CC96 0%, #3783FF 100%);
        color: white; font-weight: bold; border: none; border-radius: 12px; padding: 14px;
    }
    
    /* Metrics */
    .metric-card { background-color: #1e2127; border: 1px solid #2e3137; border-radius: 12px; padding: 20px; text-align: center; }
    .metric-value { font-size: 32px; font-weight: 700; color: white; margin-top: 5px; }
    .metric-title { font-size: 14px; color: #aaa; text-transform: uppercase; }
    
    /* Sentiment Boxes */
    .sent-box { background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }
    .sent-val { font-size: 20px; font-weight: bold; }
    .sent-label { font-size: 10px; color: #aaa; text-transform: uppercase; }

    /* Headline Cards */
    a { color: #3783FF !important; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .news-link { font-size: 0.85em; font-weight: 600; margin-top: 5px; display: block; }
    
    /* Data Grid */
    .data-label { color: #888; font-size: 0.8em; }
    .data-val { color: #eee; font-size: 1.1em; font-weight: 600; }
    .ext-link { font-size: 0.8em; margin-top: 10px; display: block; border-top: 1px solid #333; padding-top: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">AI Stock Evaluation Model</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Thesis Prototype: Integrated Signal Analysis</div>', unsafe_allow_html=True)

# --- SMART SEARCH BAR ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.form(key='search_form'):
        user_input = st.text_input("", placeholder="Enter Ticker or Company Name (e.g. Nvidia, AAPL)...")
        submit_button = st.form_submit_button(label='Analyze Stock 🚀')

if submit_button and user_input:
    # 1. Resolve Ticker
    ticker = convert_name_to_ticker(user_input)
    
    loader = DataLoader()
    engine = ScoringEngine()
    
    status = st.empty()
    status.info(f"🔄 Finding data for {ticker}...")

    # 2. Fetch Technical Data First (To validate ticker)
    df_tech = loader.get_technical_data(ticker)
    
    # 3. Validation Check
    if df_tech is None or df_tech.empty:
        status.empty()
        st.error(f"❌ Could not find data for '{user_input}' (Resolved: {ticker}). Please check the name or ticker.")
    else:
        status.info(f"🔄 Fetching Real-Time Analysis for {ticker}...")
        
        # Fetch remaining data
        data_social, social_source = loader.get_social_sentiment(ticker)
        data_deriv = loader.get_derivative_data(ticker)
        data_fund = loader.get_fundamental_data(ticker)

        # Score
        score_tech, meta_tech = engine.calculate_technical(df_tech)
        score_social, meta_social_data = engine.calculate_social(data_social)
        score_deriv, meta_deriv = engine.calculate_derivative(data_deriv)
        score_fund, meta_fund = engine.calculate_fundamental(data_fund)

        # Composite
        composite = (score_tech * 0.3) + (score_social * 0.3) + (score_deriv * 0.2) + (score_fund * 0.2)
        rating_text, rating_color = get_rating(composite)
        status.empty()

        # --- DASHBOARD ---
        st.markdown(f"<h3 style='text-align:center;'>Analysis for: {ticker}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="metric-card" style="border-top: 4px solid {rating_color};"><div class="metric-title">Composite Score</div><div class="metric-value" style="color: {rating_color};">{composite:.1f}/100</div></div>""", unsafe_allow_html=True)
        with m2:
            # CHANGED LABEL HERE
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Signal Strength</div><div class="metric-value" style="color: {rating_color};">{rating_text}</div></div>""", unsafe_allow_html=True)
        with m3:
            price = df_tech['Close'].iloc[-1]
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Current Price</div><div class="metric-value">${price:.2f}</div></div>""", unsafe_allow_html=True)

        st.markdown("### 📡 Signal Breakdown")
        c_left, c_right = st.columns([1, 1.5])

        with c_left:
            # --- TECHNICAL ---
            with st.container(border=True):
                st.markdown(f"**📈 Technical Analysis** (Score: {score_tech:.0f})")
                st.progress(int(score_tech))
                tc1, tc2 = st.columns(2)
                with tc1: st.markdown(f"<div class='data-label'>RSI (14)</div><div class='data-val'>{meta_tech.get('RSI', 0):.1f}</div>", unsafe_allow_html=True)
                with tc2: st.markdown(f"<div class='data-label'>Trend (SMA)</div><div class='data-val'>{'Bullish' if score_tech > 60 else 'Bearish'}</div>", unsafe_allow_html=True)
                st.markdown(f"""<div class="ext-link">👉 <a href="https://www.tradingview.com/chart/?symbol={ticker}" target="_blank">View Charts on TradingView</a></div>""", unsafe_allow_html=True)

            # --- AI SENTIMENT ---
            with st.container(border=True):
                st.markdown(f"**🤖 AI Sentiment** (Score: {score_social:.0f})")
                st.progress(int(score_social))
                st.caption(meta_social_data['summary'])

                counts = meta_social_data.get('counts', {'bull':0, 'bear':0, 'neut':0})
                b1, b2, b3 = st.columns(3)
                b1.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#00CC96">{counts['bull']}</div><div class="sent-label">Bullish</div></div>""", unsafe_allow_html=True)
                b2.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#888">{counts['neut']}</div><div class="sent-label">Neutral</div></div>""", unsafe_allow_html=True)
                b3.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#FF4B4B">{counts['bear']}</div><div class="sent-label">Bearish</div></div>""", unsafe_allow_html=True)

                with st.expander("🔎 View Analyzed Headlines & Sources"):
                    details = meta_social_data.get('details', [])
                    details.sort(key=lambda x: x.get('score', 0), reverse=True)
                    if not details: st.write("No headlines found.")
                    for item in details:
                        sentiment = item.get('sentiment', 'Neutral')
                        source = item.get('source', 'News')
                        if "bullish" in sentiment.lower(): icon = "🟢"; border_c = "#00CC96"
                        elif "bearish" in sentiment.lower(): icon = "🔴"; border_c = "#FF4B4B"
                        else: icon = "⚪"; border_c = "#888"
                        
                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.03); border-left: 3px solid {border_c}; padding: 10px; margin-bottom: 8px; border-radius: 4px;">
                            <div style="font-weight:600; font-size:0.95em;">{icon} {item['title']}</div>
                            <div style="font-size: 0.8em; color: #aaa; margin-top: 4px; display: flex; justify-content: space-between;">
                                <span><b>{source}</b> • {item['time']}</span>
                                <span>Impact: {item['score']}/10</span>
                            </div>
                            <div class="news-link">👉 <a href="{item['link']}" target="_blank">Read Article</a></div>
                        </div>""", unsafe_allow_html=True)

            # --- DERIVATIVES ---
            with st.container(border=True):
                st.markdown(f"**📉 Derivatives** (Score: {score_deriv:.0f})")
                st.progress(int(score_deriv))
                try:
                    pcr_val = meta_deriv.split("|")[0].split(":")[1].strip()
                    short_val = meta_deriv.split("|")[1].split(":")[1].strip()
                except: pcr_val = "N/A"; short_val = "N/A"
                dc1, dc2 = st.columns(2)
                with dc1: st.markdown(f"<div class='data-label'>Put/Call Ratio</div><div class='data-val'>{pcr_val}</div>", unsafe_allow_html=True)
                with dc2: st.markdown(f"<div class='data-label'>Short Float</div><div class='data-val'>{short_val}</div>", unsafe_allow_html=True)
                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/options" target="_blank">View Options Chain</a></div>""", unsafe_allow_html=True)

            # --- FUNDAMENTALS ---
            with st.container(border=True):
                st.markdown(f"**🏢 Fundamentals** (Score: {score_fund:.0f})")
                st.progress(int(score_fund))
                try: pe_val = meta_fund.split(":")[1].strip()
                except: pe_val = "N/A"
                fc1, fc2 = st.columns(2)
                with fc1: st.markdown(f"<div class='data-label'>P/E Ratio</div><div class='data-val'>{pe_val}</div>", unsafe_allow_html=True)
                with fc2: st.markdown(f"<div class='data-label'>Status</div><div class='data-val'>{'Undervalued' if score_fund > 80 else 'Fair/Over'}</div>", unsafe_allow_html=True)
                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/financials" target="_blank">View Financial Statements</a></div>""", unsafe_allow_html=True)

        with c_right:
            if not df_tech.empty:
                st.subheader("Price Action")
                fig = go.Figure(data=[go.Candlestick(x=df_tech.index, open=df_tech['Open'], high=df_tech['High'], low=df_tech['Low'], close=df_tech['Close'])])
                fig.update_layout(height=450, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)