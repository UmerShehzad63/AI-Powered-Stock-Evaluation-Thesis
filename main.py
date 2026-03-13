import streamlit as st
from data_loader import DataLoader, convert_name_to_ticker
from scorers import ScoringEngine
from utils import get_rating

st.set_page_config(page_title="Thesis Prototype", layout="wide", page_icon="📈")

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

    .fsig-pass { display:inline-block; background:#00CC9622; border:1px solid #00CC96; color:#00CC96; border-radius:4px; padding:2px 8px; font-size:0.78em; margin:2px; }
    .fsig-fail { display:inline-block; background:#FF4B4B22; border:1px solid #FF4B4B; color:#FF4B4B; border-radius:4px; padding:2px 8px; font-size:0.78em; margin:2px; }

    .pillar-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #1e2127; }
    .pillar-name { font-size:0.82em; color:#aaa; text-transform:uppercase; letter-spacing:0.04em; }
    .pillar-bar-bg { flex:1; margin:0 12px; height:6px; background:#1e2127; border-radius:3px; }
    .pillar-bar-fill { height:6px; border-radius:3px; }
    .pillar-val { font-size:0.9em; font-weight:700; min-width:32px; text-align:right; }
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

        score_tech, meta_tech   = engine.calculate_technical(df_tech)
        data_social, social_src = loader.get_social_sentiment(ticker)
        data_deriv              = loader.get_derivative_data(ticker)
        data_fund               = loader.get_fundamental_data(ticker)

        score_social, meta_social = engine.calculate_social(data_social)
        score_deriv,  meta_deriv  = engine.calculate_derivative(data_deriv)
        score_fund,   meta_fund   = engine.calculate_fundamental(data_fund)

        # Weights: Fundamentals 40% | Sentiment 25% | Technical 20% | Derivatives 15%
        base_composite = (
            score_fund   * 0.40 +
            score_social * 0.25 +
            score_tech   * 0.20 +
            score_deriv  * 0.15
        )

        insider_buys    = meta_fund.get('insider_buys', 0)
        insider_sells   = meta_fund.get('insider_sells', 0)
        insider_booster = meta_fund.get('insider_booster', 0)
        composite       = min(100, base_composite + insider_booster)

        rating_text, rating_color = get_rating(composite)
        status.empty()

        company_name = meta_fund.get('longName') or meta_fund.get('shortName') or ticker
        sector       = meta_fund.get('sector', '')
        industry     = meta_fund.get('industry', '')

        st.markdown(f"<h3 style='text-align:center;'>{ticker} &nbsp;<span style='color:#aaa;font-weight:400;font-size:0.75em;'>({company_name})</span></h3>", unsafe_allow_html=True)
        if sector or industry:
            st.markdown(f"<p style='text-align:center;color:#666;font-size:0.82em;margin-top:-10px;'>{sector}{' · ' + industry if industry else ''}</p>", unsafe_allow_html=True)

        # ── Competitors strip ──
        competitors = loader.get_competitors(ticker, company_name, sector, industry)
        if competitors:
            chips_html = ''.join([
                f'<a href="?ticker={c["ticker"]}" style="display:inline-block;background:#1a1d24;border:1px solid #2e3240;'
                f'border-radius:20px;padding:4px 12px;margin:3px;font-size:0.78em;color:#aaa;text-decoration:none;'
                f'cursor:pointer;" title="{c.get("name","")}">'
                f'<span style="color:#3783FF;font-weight:600;">{c["ticker"]}</span>'
                f'&nbsp;<span style="color:#666;">{c.get("name","")}</span></a>'
                for c in competitors
            ])
            st.markdown(
                f'<div style="text-align:center;margin:4px 0 12px 0;">'
                f'<span style="font-size:0.72em;color:#555;text-transform:uppercase;letter-spacing:0.06em;margin-right:8px;">Competitors</span>'
                f'{chips_html}</div>',
                unsafe_allow_html=True
            )
        st.markdown("---")

        # ── Top metrics ──
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="metric-card" style="border-top:4px solid {rating_color};">
                <div class="metric-title">Composite Score</div>
                <div class="metric-value" style="color:{rating_color};">{composite:.1f}/100</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-title">Signal Strength</div>
                <div class="metric-value" style="color:{rating_color};">{rating_text}</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-title">Current Price</div>
                <div class="metric-value">${df_tech['Close'].iloc[-1]:.2f}</div>
            </div>""", unsafe_allow_html=True)

        # ── Insider banner ──
        if insider_buys > 10:
            emoji, title, color = "🔥", f"Massive Insider Cluster Buying! (+{insider_booster:.1f} Points)", "#00CC96"
        elif insider_buys > 0:
            emoji, title, color = "👀", f"Minor Insider Buying Detected (+{insider_booster:.1f} Points)", "#3783FF"
        else:
            emoji, title, color = "👔", "Corporate Insider Activity (+0 Points)", "#888888"

        st.markdown(f"""
        <div style="background:linear-gradient(90deg,{color}33 0%,rgba(0,0,0,0) 100%);
                    border-left:4px solid {color};padding:15px;border-radius:5px;margin:20px 0;">
            <h4 style="margin:0;color:{color};">{emoji} {title}</h4>
            <div style="color:#ddd;font-size:0.95em;margin-top:8px;">
                <b>Past 12-Month Transactions:</b>
                <span style="color:#00CC96;font-weight:bold;">{insider_buys} Buys</span> |
                <span style="color:#FF4B4B;font-weight:bold;">{insider_sells} Sells</span><br>
                <span style="font-size:0.9em;color:#aaa;"><i>Insiders only buy when they expect the price to rise.</i></span>
            </div>
            <div style="margin-top:10px;font-size:0.9em;">
                👉 <a href="http://openinsider.com/search?q={ticker}" target="_blank" style="color:#3783FF;font-weight:600;">OpenInsider Log</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                👉 <a href="https://finance.yahoo.com/quote/{ticker}/insider-transactions" target="_blank" style="color:#3783FF;font-weight:600;">Yahoo Finance</a>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### 📡 Signal Breakdown")
        c_left, c_right = st.columns([1, 1.5])

        with c_left:
            # ── Fundamentals ──
            with st.container(border=True):
                dist_tag = " ⚠️ **DISTRESSED ASSET**" if meta_fund.get('is_distressed') else ""
                p_raw    = meta_fund.get('piotroski_raw', 0)
                p_max    = meta_fund.get('piotroski_max', 0)
                f_badge  = f" · Piotroski {p_raw}/{p_max}" if p_max > 0 else ""
                st.markdown(f"**🏢 Fundamentals** (Score: {score_fund:.0f}{f_badge}){dist_tag}")
                st.progress(int(score_fund))

                # 5-pillar mini breakdown
                pillar_scores = meta_fund.get('pillar_scores', {})
                pillar_colors = {
                    'Profitability': '#00CC96',
                    'Growth':        '#3783FF',
                    'Valuation':     '#FFD700',
                    'Health':        '#FF9500',
                    'FCF Quality':   '#CC55FF',
                }
                if pillar_scores:
                    rows_html = ""
                    for pname, pval in pillar_scores.items():
                        if pval is None:
                            continue
                        pcolor = pillar_colors.get(pname, '#888')
                        bar_width = max(2, pval)
                        rows_html += (
                            f'<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1e2127;">'
                            f'<span style="font-size:0.82em;color:#aaa;text-transform:uppercase;letter-spacing:0.04em;min-width:90px;">{pname}</span>'
                            f'<div style="flex:1;margin:0 12px;height:6px;background:#1e2127;border-radius:3px;">'
                            f'<div style="width:{bar_width}%;height:6px;border-radius:3px;background:{pcolor};"></div>'
                            f'</div>'
                            f'<span style="font-size:0.9em;font-weight:700;color:{pcolor};min-width:32px;text-align:right;">{pval}</span>'
                            f'</div>'
                        )
                    st.markdown(f'<div style="background:#12151a;border-radius:8px;padding:12px 16px;margin:8px 0;"><div style="font-size:0.72em;color:#666;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Factor Breakdown</div>{rows_html}</div>', unsafe_allow_html=True)

                def fmt_fp(v):  return f"{v*100:.1f}%" if v is not None else "N/A"
                def fmt_fn(v):  return f"{v:.2f}"      if v is not None else "N/A"
                def fmt_de(v):  return f"{v/100:.2f}"  if v is not None else "N/A"

                pe_med = meta_fund.get('sector_pe_median')

                fc1, fc2 = st.columns(2)
                with fc1:
                    pe_label = f"P/E Ratio (vs ~{pe_med}x sector)" if pe_med else "P/E Ratio"
                    st.markdown(f"<div class='data-label'>{pe_label}</div><div class='data-val'>{fmt_fn(meta_fund.get('PE'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Return on Equity</div><div class='data-val'>{fmt_fp(meta_fund.get('ROE'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Revenue Growth</div><div class='data-val'>{fmt_fp(meta_fund.get('RevGrowth'))}</div>", unsafe_allow_html=True)
                with fc2:
                    st.markdown(f"<div class='data-label'>P/B Ratio</div><div class='data-val'>{fmt_fn(meta_fund.get('PB'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Net Margin</div><div class='data-val'>{fmt_fp(meta_fund.get('Margins'))}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Debt-to-Equity</div><div class='data-val'>{fmt_de(meta_fund.get('DebtEq'))}</div>", unsafe_allow_html=True)

                # Piotroski signal pills (secondary detail)
                p_sigs = meta_fund.get('piotroski_signals', {})
                if p_sigs:
                    with st.expander("🔬 Piotroski F-Score Signals"):
                        pills = ""
                        for lbl, val in p_sigs.items():
                            css  = "fsig-pass" if val == 1 else "fsig-fail"
                            icon = "✓" if val == 1 else "✗"
                            pills += f'<span class="{css}">{icon} {lbl}</span>'
                        st.markdown(f"<div style='margin-top:4px;'>{pills}</div>", unsafe_allow_html=True)

                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/financials" target="_blank">View Financial Statements</a></div>""", unsafe_allow_html=True)

            # ── Sentiment ──
            with st.container(border=True):
                st.markdown(f"**🤖 AI Sentiment** (Score: {score_social:.0f})")
                st.progress(int(score_social))
                st.caption(meta_social['summary'])

                counts = meta_social.get('counts', {'bull': 0, 'bear': 0, 'neut': 0})
                b1, b2, b3 = st.columns(3)
                b1.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#00CC96">{counts['bull']}</div><div class="sent-label">Bullish</div></div>""", unsafe_allow_html=True)
                b2.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#888">{counts['neut']}</div><div class="sent-label">Neutral</div></div>""", unsafe_allow_html=True)
                b3.markdown(f"""<div class="sent-box"><div class="sent-val" style="color:#FF4B4B">{counts['bear']}</div><div class="sent-label">Bearish</div></div>""", unsafe_allow_html=True)

                with st.expander("🔎 View Analyzed Headlines & Sources"):
                    details = sorted(meta_social.get('details', []), key=lambda x: x.get('score', 0), reverse=True)
                    if not details:
                        st.write("No headlines found.")
                    for item in details:
                        sent = item.get('sentiment', 'Neutral')
                        src  = item.get('source', 'News')
                        if "bullish" in sent.lower(): icon2, bc = "🟢", "#00CC96"
                        elif "bearish" in sent.lower(): icon2, bc = "🔴", "#FF4B4B"
                        else: icon2, bc = "⚪", "#888"
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.03);border-left:3px solid {bc};padding:10px;margin-bottom:8px;border-radius:4px;">
                            <div style="font-weight:600;font-size:0.95em;">{icon2} {item['title']}</div>
                            <div style="font-size:0.8em;color:#aaa;margin-top:4px;display:flex;justify-content:space-between;">
                                <span><b>{src}</b> • {item['time']}</span>
                                <span>Impact: {item['score']}/10</span>
                            </div>
                            <div class="news-link">👉 <a href="{item['link']}" target="_blank">Read Article</a></div>
                        </div>""", unsafe_allow_html=True)

            # ── Technical ──
            with st.container(border=True):
                st.markdown(f"**📈 Technical Analysis** (Score: {score_tech:.0f})")
                st.progress(int(score_tech))

                price  = meta_tech.get('Price', 0)
                macd_s = "Bullish Cross" if meta_tech.get('MACD', 0) > meta_tech.get('MACD_Signal', 0) else "Bearish Cross"

                ema20  = meta_tech.get('EMA20', 0)
                sma50  = meta_tech.get('SMA50', 0)
                sma200 = meta_tech.get('SMA200', 0)
                if price > ema20 > sma50 > sma200:    trend_s = "Strong Uptrend"
                elif price > sma50 > sma200:           trend_s = "Uptrend"
                elif price < sma50 and price > sma200: trend_s = "Weakening / Pullback"
                elif price < sma200:                   trend_s = "Downtrend"
                else:                                  trend_s = "Mixed/Consolidating"

                bb_hi = meta_tech.get('BB_High', 0)
                bb_lo = meta_tech.get('BB_Low', 0)
                if price > bb_hi:   bb_s = "Upper Band (Breakout)" if meta_tech.get('Trend') else "Overbought"
                elif price < bb_lo: bb_s = "Lower Band (Support)"  if meta_tech.get('Trend') else "Oversold"
                else:               bb_s = "Mid-Channel"

                tc1, tc2 = st.columns(2)
                with tc1:
                    st.markdown(f"<div class='data-label'>RSI (14)</div><div class='data-val'>{meta_tech.get('RSI',0):.1f}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>MACD</div><div class='data-val'>{macd_s}</div>", unsafe_allow_html=True)
                with tc2:
                    st.markdown(f"<div class='data-label'>Trend (vs 200 SMA)</div><div class='data-val'>{trend_s}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Volatility (BB)</div><div class='data-val'>{bb_s}</div>", unsafe_allow_html=True)

                sig_html = ""
                for lbl, s in meta_tech.get('signal_details', []):
                    css  = "fsig-pass" if s == 1 else "fsig-fail"
                    icon = "✓" if s == 1 else "✗"
                    sig_html += f'<span class="{css}">{icon} {lbl}</span>'
                if sig_html:
                    st.markdown(f"<div style='margin-top:10px;'>{sig_html}</div>", unsafe_allow_html=True)

            # ── Derivatives ──
            with st.container(border=True):
                st.markdown(f"**📉 Derivatives & Options** (Score: {score_deriv:.0f})")
                st.progress(int(score_deriv))

                def fmt_num(v): return f"{v:.2f}" if v is not None else "N/A"
                def fmt_pct(v): return f"{v:.1f}%" if v is not None else "N/A"

                pcr_v   = meta_deriv.get('pcr_vol')
                pcr_o   = meta_deriv.get('pcr_oi')
                s_float = meta_deriv.get('short_float')
                s_ratio = meta_deriv.get('short_ratio')
                iv      = meta_deriv.get('avg_iv')

                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown(f"<div class='data-label'>Volume P/C Ratio</div><div class='data-val'>{fmt_num(pcr_v)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Short Float</div><div class='data-val'>{fmt_pct(s_float)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='data-label'>Implied Volatility (IV)</div><div class='data-val'>{fmt_pct(iv)}</div>", unsafe_allow_html=True)
                with dc2:
                    st.markdown(f"<div class='data-label'>Open Interest P/C Ratio</div><div class='data-val'>{fmt_num(pcr_o)}</div>", unsafe_allow_html=True)
                    squeeze = "🔥 Squeeze Watch" if (s_ratio and s_float and s_ratio > 8 and s_float > 10 and meta_tech.get('Trend')) else ""
                    st.markdown(f"<div class='data-label'>Days to Cover</div><div class='data-val'>{fmt_num(s_ratio)} <span style='color:#FF4B4B;font-size:0.8em;'>{squeeze}</span></div>", unsafe_allow_html=True)
                    iv_s = "High Volatility Expected" if iv and iv > 50 else ("Normal Volatility" if iv else "N/A")
                    st.markdown(f"<div class='data-label'>Market Expectation</div><div class='data-val'>{iv_s}</div>", unsafe_allow_html=True)

                st.markdown(f"""<div class="ext-link">👉 <a href="https://finance.yahoo.com/quote/{ticker}/options" target="_blank">View Options Chain Data</a></div>""", unsafe_allow_html=True)

        # ── Chart ──
        with c_right:
            if not df_tech.empty:
                st.subheader("Price Action & Indicators")

                from ta.volatility import BollingerBands as BB
                import streamlit.components.v1 as components
                import json

                bb_ind   = BB(df_tech['Close'])
                df_tech['bb_high'] = bb_ind.bollinger_hband()
                df_tech['bb_low']  = bb_ind.bollinger_lband()
                df_tech['sma_50']  = df_tech['Close'].rolling(50).mean()
                df_tech['sma_200'] = df_tech['Close'].rolling(min(200, len(df_tech))).mean()

                # Build data arrays for Lightweight Charts
                def to_ts(idx):
                    return int(idx.timestamp())

                candles = [
                    {"time": to_ts(row.Index), "open": round(float(row.Open), 4),
                     "high": round(float(row.High), 4), "low": round(float(row.Low), 4),
                     "close": round(float(row.Close), 4)}
                    for row in df_tech.itertuples() if not (
                        hasattr(row, 'Open') and str(row.Open) == 'nan'
                    )
                ]

                def line_data(col):
                    return [
                        {"time": to_ts(idx), "value": round(float(v), 4)}
                        for idx, v in df_tech[col].items()
                        if str(v) != 'nan'
                    ]

                sma50_data  = line_data('sma_50')
                sma200_data = line_data('sma_200')
                bb_hi_data  = line_data('bb_high')
                bb_lo_data  = line_data('bb_low')

                candles_json  = json.dumps(candles)
                sma50_json    = json.dumps(sma50_data)
                sma200_json   = json.dumps(sma200_data)
                bb_hi_json    = json.dumps(bb_hi_data)
                bb_lo_json    = json.dumps(bb_lo_data)

                chart_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0e1117; }}
  #chart {{ width:100%; height:500px; }}
  #legend {{
    position:absolute; top:8px; left:8px; z-index:10;
    display:flex; gap:14px; flex-wrap:wrap;
    font-family:sans-serif; font-size:12px; color:#aaa;
    background:rgba(14,17,23,0.7); padding:4px 10px; border-radius:6px;
  }}
  .leg {{ display:flex; align-items:center; gap:5px; }}
  .dot {{ width:14px; height:3px; border-radius:2px; }}
</style>
</head>
<body>
<div style="position:relative;">
  <div id="legend">
    <div class="leg"><div class="dot" style="background:#26a69a;"></div>Price</div>
    <div class="leg"><div class="dot" style="background:#3783FF;"></div>SMA 50</div>
    <div class="leg"><div class="dot" style="background:#FF4B4B; border-top:2px dashed #FF4B4B; height:0;"></div>SMA 200</div>
    <div class="leg"><div class="dot" style="background:rgba(255,255,255,0.25);"></div>BB Band</div>
  </div>
  <div id="chart"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
<script>
  const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
    width:  document.getElementById('chart').clientWidth,
    height: 500,
    layout: {{ background: {{ color: '#0e1117' }}, textColor: '#aaa' }},
    grid:   {{ vertLines: {{ color: 'rgba(255,255,255,0.04)' }}, horzLines: {{ color: 'rgba(255,255,255,0.04)' }} }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
    rightPriceScale: {{ borderColor: 'rgba(255,255,255,0.1)' }},
    timeScale: {{ borderColor: 'rgba(255,255,255,0.1)', timeVisible: true, secondsVisible: false }},
    handleScroll:  {{ mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true }},
    handleScale:   {{ mouseWheel: true, pinch: true, axisPressedMouseMove: true }},
  }});

  // Candlesticks
  const cSeries = chart.addCandlestickSeries({{
    upColor: '#26a69a', downColor: '#ef5350',
    borderUpColor: '#26a69a', borderDownColor: '#ef5350',
    wickUpColor: '#26a69a', wickDownColor: '#ef5350',
  }});
  cSeries.setData({candles_json});

  // BB upper
  const bbHi = chart.addLineSeries({{ color: 'rgba(255,255,255,0.18)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false }});
  bbHi.setData({bb_hi_json});

  // BB lower (filled)
  const bbLo = chart.addLineSeries({{ color: 'rgba(255,255,255,0.18)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false }});
  bbLo.setData({bb_lo_json});

  // SMA 50
  const sma50 = chart.addLineSeries({{ color: '#3783FF', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false }});
  sma50.setData({sma50_json});

  // SMA 200
  const sma200 = chart.addLineSeries({{ color: '#FF4B4B', lineWidth: 1.5, lineStyle: LightweightCharts.LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false }});
  sma200.setData({sma200_json});

  chart.timeScale().fitContent();

  window.addEventListener('resize', () => {{
    chart.applyOptions({{ width: document.getElementById('chart').clientWidth }});
  }});
</script>
</body>
</html>
"""
                components.html(chart_html, height=510, scrolling=False)

                st.markdown(f"""
                <div style="text-align:right; margin-top:6px;">
                    👉 <a href="https://www.tradingview.com/chart/?symbol={ticker}" target="_blank" style="color:#3783FF; font-weight:600; font-size:0.9em;">View Advanced Charts on TradingView ↗</a>
                </div>""", unsafe_allow_html=True)