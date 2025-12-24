import streamlit as st
import plotly.graph_objects as go
from data_loader import DataLoader
from scorers import ScoringEngine
from utils import get_rating

st.set_page_config(page_title="Thesis Prototype", layout="wide")
st.title("AI-Powered Stock Evaluation Model")
st.markdown("*Thesis Prototype: Integrated Signal Analysis*")

st.sidebar.header("Configuration")

with st.sidebar.form(key='eval_form'):
    user_api_key = st.text_input("Finnhub API Key (Optional)", type="password")
    ticker = st.text_input("Ticker Symbol", value="AAPL").upper()
    submit_button = st.form_submit_button(label='Evaluate Stock')

if submit_button:
    loader = DataLoader(user_api_key)
    engine = ScoringEngine()

    with st.spinner(f"Evaluating {ticker}..."):
        df_tech = loader.get_technical_data(ticker)
        data_social, social_source = loader.get_social_sentiment(ticker)
        data_deriv = loader.get_derivative_data(ticker)
        data_fund = loader.get_fundamental_data(ticker)

        score_tech, meta_tech = engine.calculate_technical(df_tech)
        score_social, meta_social = engine.calculate_social(data_social)
        score_deriv, meta_deriv = engine.calculate_derivative(data_deriv)
        score_fund, meta_fund = engine.calculate_fundamental(data_fund)

        weights = {'tech': 0.3, 'social': 0.2, 'deriv': 0.25, 'fund': 0.25}
        composite = (
            score_tech * weights['tech'] +
            score_social * weights['social'] +
            score_deriv * weights['deriv'] +
            score_fund * weights['fund']
        )
        
        rating_text, rating_color = get_rating(composite)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Composite Score", f"{composite:.1f}/100")
    
    with col2:
        st.markdown(f"### Rating: :{rating_color}[ {rating_text} ]")
        
    with col3:
        if not df_tech.empty:
            current_price = df_tech['Close'].iloc[-1]
            st.metric("Current Price", f"${current_price:.2f}")
        else:
            st.metric("Current Price", "N/A")

    st.markdown("---")
    
    c_left, c_right = st.columns([1, 2])
    
    with c_left:
        st.subheader("Signal Breakdown")
        
        st.write(f"📈 **Technical:** {score_tech:.0f}")
        
        if social_source == "Real API":
            st.success(f"💬 **Social:** {score_social:.0f} (Source: {social_source})")
        else:
            st.warning(f"💬 **Social:** {score_social:.0f} (Source: {social_source})")
        
        st.info(f"📉 **Derivative:** {score_deriv:.0f}\n\n*{meta_deriv}*")

        st.info(f"📊 **Fundamental:** {score_fund:.0f}\n\n*P/E Ratio: {meta_fund:.2f}*")

    with c_right:
        st.subheader(f"{ticker} Price Trend")
        if not df_tech.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'].rolling(50).mean(), name='SMA 50'))
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Show Raw Data Details"):
                st.json({
                    "Social Metadata": meta_social,
                    "Derivative Data": meta_deriv,
                    "Technical RSI": f"{meta_tech.get('RSI', 0):.2f}",
                    "Fundamental P/E": meta_fund
                })