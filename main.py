import streamlit as st
import plotly.graph_objects as go
from data_loader import DataLoader, convert_name_to_ticker
from scorers import ScoringEngine
from utils import get_rating
from ta.volatility import BollingerBands

st.set_page_config(page_title="Thesis Prototype", layout="wide", page_icon="📈")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-header { font-size: 2.5rem; font-weight: 800; text-align: center; background: -webkit-linear-gradient(45deg, #00CC96, #3783FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub-header { text-align: center; color: #888; margin-bottom: 30px; }
    
    .stTextInput > div > div > input { background-color: #1F2329; color: white; border: 1px solid #373A40; border-radius: 12px; padding: 12px; }
    div.stButton > button { width: 100%; background: linear-gradient(90deg, #00CC96 0%, #3783FF 100%); color: white; font-weight: bold; border: none; border-radius: 12px; padding: 14px; }
    
    .metric-card { background-color: #1e2127; border: 1px solid #2e3137; border-radius: 12px; padding: 20px; text-align: center; }
    .metric-value { font-size: 32px; font-weight: 700; color: white; margin-top: 5px; }
    .metric-title { font-size: 14px; color: #aaa; text-transform: uppercase; }
    
    .sent-box { background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }
    .sent-val { font-size: 20px; font-weight: bold; }
    .sent-label { font-size: 10px; color: #aaa; text-transform: uppercase; }

    a { color: #3783FF !important; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .news-link { font-size: 0.85em; font-weight: 600; margin-top: 5px; display: block; }
    
    .data-label { color: #888; font-size: 0.75em; text-transform: uppercase; }
    .data-val { color: #eee; font-size: 1.05em; font-weight: 600; margin-bottom: 12px; }
    .ext-link { font-size: 0.8em; margin-top: 10px; display: block; border-top: 1px solid #333; padding-top: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">AI Stock Evaluation Model</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Thesis Prototype: Integrated Signal Analysis</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.form(key='search_form'):
        user_input = st.text_input("", placeholder="Enter Ticker or Company Name (e.g. Nvidia, AAPL)...")
        submit_button = st.form_submit_button(label='Analyze Stock 🚀')

if submit_button and user_input:
    ticker = convert_name_to_ticker(user_input)
    loader = DataLoader()
    engine = ScoringEngine()
    
    status = st.empty()
    status.info(f"🔄 Finding data for {ticker}...")

    df_tech = loader.get_technical_data(ticker)
    
    if df_tech is None or df_tech.empty:
        status.empty()
        st.error(f"❌ Could not find data for '{user_input}' (Resolved: {ticker}). Please check the name or ticker.")
    else:
        status.info(f"🔄 Fetching Real-Time Analysis for {ticker}...")
        
        # --- TECHNICALS FIRST (Anchors Derivatives) ---
        score_tech, meta_tech = engine.calculate_technical(df_tech)
        
        data_social, social_source = loader.get_social_sentiment(ticker)
        data_deriv = loader.get_derivative_data(ticker)
        data_fund = loader.get_fundamental_data(ticker)

        score_social, meta_social_data = engine.calculate_social(data_social)
        score_deriv, meta_deriv = engine.calculate_derivative(data_deriv)
        score_fund, meta_fund = engine.calculate_fundamental(data_fund)

        # Base Composite
        weights = {'fund': 0.40, 'social': 0.30, 'tech': 0.15, 'deriv': 0.15}
        base_composite = (
            (score_fund * weights['fund']) + 
            (score_social * weights['social']) + 
            (score_tech * weights['tech']) + 
            (score_deriv * weights['deriv'])
        )
        
        # APPLY DYNAMIC INSIDER BOOSTER
        insider_buys = meta_fund.get('insider_buys', 0)
        insider_sells = meta_fund.get('insider_sells', 0)
        insider_booster = meta_fund.get('insider_booster', 0)
        
        composite = min(100, base_composite + insider_booster) # Cap at 100
        
        rating_text, rating_color = get_rating(composite)
        status.empty()

        # --- DASHBOARD ---
        st.markdown(f"<h3 style='text-align:center;'>Analysis for: {ticker}</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # 1. TOP METRICS
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"""<div class="metric-card" style="border-top: 4px solid {rating_color};"><div class="metric-title">Composite Score</div><div class="metric-value" style="color: {rating_color};">{composite:.1f}/100</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="metric-card"><div class="metric-title">Signal Strength</div><div class="metric-value" style="color: {rating_color};">{rating_text}</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="metric-card"><div class="metric-title">Current Price</div><div class="metric-value">${df_tech['Close'].iloc[-1]:.2f}</div></div>""", unsafe_allow_html=True)

        # 2. INSIDER UI BANNER
        if insider_buys > 10:  
            emoji = "🔥"
            title = f"Massive Insider Cluster Buying! (+{insider_booster:.1f} Points)"
            color = "#00CC96"
        elif insider_buys > 0: 
            emoji = "👀"
            title = f"Minor Insider Buying Detected (+{insider_booster:.1f} Points)"
            color = "#3783FF"
        else:
            emoji = "👔"
            title = "Corporate Insider Activity (+0 Points)"
            color = "#888888"

        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {color}33 0%, rgba(0,0,0,0) 100%); 
                    border-left: 4px solid {color}; padding: 15px; border-radius: 5px; margin-top: 20px; margin-bottom: 20px;">
            <h4 style="margin:0; color:{color};">{emoji} {title}</h4>
            <div style="color:#ddd; font-size: 0.95em; margin-top: 8px;">
                <b>Past 12-Month Transactions:</b> <span style="color:#00CC96; font-weight:bold;">{insider_buys} Buys</span> | <span style="color:#FF4B4B; font-weight:bold;">{insider_sells} Sells</span> <br>
                <span style="font-size: 0.9em; color: #aaa;"><i>Note: Insider selling is not penalized as it can occur for tax/personal reasons. Insiders only buy when they expect the price to rise.</i></span>
            </div>
            <div style="margin-top: 10px; font-size: 0.9em;">
                👉 <a href="http://openinsider.com/search?q={ticker}" target="_blank" style="color: #3783FF; text-decoration: none; font-weight: 600;">View Full Trading Log on OpenInsider</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                👉 <a href="https://finance.yahoo.com/quote/{ticker}/insider-transactions" target="_blank" style="color: #3783FF; text-decoration: none; font-weight: 600;">View on Yahoo Finance</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📡 Signal Breakdown")
        c_left, c_right = st.columns([1, 1.5])

        with c_left:
            # --- TECHNICAL ANALYSIS ---
            with st.container(border=True):
                st.markdown(f"**📈 Technical Analysis** (Score: {score_tech:.0f})")
                st.progress(int(score_tech))
                
                price = meta_tech.get('Price', 0)
                macd_status = "Bullish Cross" if meta_tech.get('MACD', 0) > meta_tech.get('MACD_Signal', 0) else "Bearish Cross"
                
                ema20 = meta_tech.get('EMA20', 0); sma50 = meta_tech.get('SMA50', 0); sma200 = meta_tech.get('SMA200', 0)
                if price > ema20 > sma50 > sma200: trend_status = "Strong Uptrend"
                elif price > sma50 > sma200: trend_status = "Uptrend"
                elif price < sma50 and price > sma200: trend_status = "Weakening / Pullback"
                elif price < sma200: trend_status = "Downtrend"
                else: trend_status = "Mixed/Consolidating"

                bb_high = meta_tech.get('BB_High', 0); bb_low = meta_tech.get('BB_Low', 0)
                if price > bb_high: bb_status = "Upper Band (Breakout)" if meta_tech.get('Trend') else "Overbought"
                elif price < bb_low: bb_status = "Lower Band (Support)" if meta_tech.get('Trend') else "Oversold"
                else: bb_status = "Mid-Channel"

                tc1, tc2 = st.columns(2)
                with tc1: 
                    st.markdown(f"<div class='data-label'>RSI (14)</div><div class='data-val'>{meta_tech.get('RSI', 0):.1f}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>MACD</div><div class='data-val'>{macd_status}</div>", unsafe_allow_html=True)
                with tc2: 
                    st.markdown(f"<div class='data-label'>Trend (vs 200 SMA)</div><div class='data-val'>{trend_status}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Volatility (BB)</div><div class='data-val'>{bb_status}</div>", unsafe_allow_html=True)
                
                st.markdown(f"""<div class="ext-link">👉 <a href="https://www.tradingview.com/chart/?symbol={ticker}" target="_blank">View Advanced Charts</a></div>""", unsafe_allow_html=True)

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
                st.markdown(f"**📉 Derivatives & Options** (Score: {score_deriv:.0f})")
                st.progress(int(score_deriv))
                
                def fmt_num(val): return f"{val:.2f}" if val is not None else "N/A"
                def fmt_pct(val): return f"{val:.1f}%" if val is not None else "N/A"

                pcr_v = meta_deriv.get('pcr_vol', 0)
                pcr_o = meta_deriv.get('pcr_oi', 0)
                s_float = meta_deriv.get('short_float', 0)
                s_ratio = meta_deriv.get('short_ratio', 0)
                iv = meta_deriv.get('avg_iv', 0)
                
                dc1, dc2 = st.columns(2)
                with dc1: 
                    st.markdown(f"<div class='data-label'>Volume P/C Ratio</div><div class='data-val'>{fmt_num(pcr_v)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Short Float</div><div class='data-val'>{fmt_pct(s_float)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Implied Volatility (IV)</div><div class='data-val'>{fmt_pct(iv)}</div>", unsafe_allow_html=True)
                with dc2: 
                    st.markdown(f"<div class='data-label'>Open Interest P/C Ratio</div><div class='data-val'>{fmt_num(pcr_o)}</div>", unsafe_allow_html=True)
                    squeeze_tag = "🔥 Squeeze Watch" if s_ratio > 8 and s_float > 10 and meta_tech.get('Trend') else ""
                    st.markdown(f"<div class='data-label'>Days to Cover</div><div class='data-val'>{fmt_num(s_ratio)} <span style='color:#FF4B4B; font-size:0.8em;'>{squeeze_tag}</span></div>", unsafe_allow_html=True)
                    iv_status = "High Volatility Expected" if iv > 50 else "Normal Volatility"
                    st.markdown(f"<div class='data-label'>Market Expectation</div><div class='data-val'>{iv_status}</div>", unsafe_allow_html=True)

                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/options" target="_blank">View Options Chain Data</a></div>""", unsafe_allow_html=True)

            # --- FUNDAMENTALS ---
            with st.container(border=True):
                if meta_fund.get('is_distressed'):
                    st.markdown(f"**🏢 Fundamentals** (Score: {score_fund:.0f}) ⚠️ **DISTRESSED ASSET**")
                else:
                    st.markdown(f"**🏢 Fundamentals** (Score: {score_fund:.0f})")
                st.progress(int(score_fund))
                
                def fmt_fpct(val): return f"{val*100:.1f}%" if val is not None else "N/A"
                def fmt_fnum(val): return f"{val:.2f}" if val is not None else "N/A"
                def fmt_de(val): return f"{val/100:.2f}" if val is not None else "N/A"

                fc1, fc2 = st.columns(2)
                with fc1:
                    st.markdown(f"<div class='data-label'>P/E Ratio</div><div class='data-val'>{fmt_fnum(meta_fund.get('PE'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Return on Equity</div><div class='data-val'>{fmt_fpct(meta_fund.get('ROE'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Revenue Growth</div><div class='data-val'>{fmt_fpct(meta_fund.get('RevGrowth'))}</div>", unsafe_allow_html=True)
                with fc2:
                    st.markdown(f"<div class='data-label'>P/B Ratio</div><div class='data-val'>{fmt_fnum(meta_fund.get('PB'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Net Margin</div><div class='data-val'>{fmt_fpct(meta_fund.get('Margins'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Debt-to-Equity</div><div class='data-val'>{fmt_de(meta_fund.get('DebtEq'))}</div>", unsafe_allow_html=True)

                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/financials" target="_blank">View Financial Statements</a></div>""", unsafe_allow_html=True)

        with c_right:
            if not df_tech.empty:
                st.subheader("Price Action & Indicators")
                
                bb = BollingerBands(df_tech['Close'])
                df_tech['bb_high'] = bb.bollinger_hband()
                df_tech['bb_low'] = bb.bollinger_lband()
                df_tech['sma_50'] = df_tech['Close'].rolling(50).mean()
                df_tech['sma_200'] = df_tech['Close'].rolling(min(200, len(df_tech))).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['bb_low'], line=dict(color='rgba(255, 255, 255, 0.1)', width=1), name='Lower BB'))
                fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['bb_high'], line=dict(color='rgba(255, 255, 255, 0.1)', width=1), name='Upper BB', fill='tonexty', fillcolor='rgba(255, 255, 255, 0.05)'))
                fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['sma_50'], line=dict(color='#3783FF', width=1.5), name='SMA 50'))
                fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['sma_200'], line=dict(color='#FF4B4B', width=1.5, dash='dash'), name='SMA 200'))
                fig.add_trace(go.Candlestick(x=df_tech.index, open=df_tech['Open'], high=df_tech['High'], low=df_tech['Low'], close=df_tech['Close'], name='Price'))
                
                fig.update_layout(height=500, margin=dict(t=0, b=0, l=0, r=0), xaxis_rangeslider_visible=False, template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)