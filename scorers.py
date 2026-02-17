from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD, EMAIndicator
from ta.volatility import BollingerBands

class ScoringEngine:
    def __init__(self):
        # Default trend state to anchor the derivative scorer later
        self.current_tech_trend = True 

    def calculate_technical(self, df):
        if df.empty or len(df) < 50: return 50, {}
        
        close = df['Close']
        price = close.iloc[-1]
        
        rsi = RSIIndicator(close).rsi().iloc[-1]
        sma_50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
        ema_20 = EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        
        window_200 = min(200, len(df))
        sma_200 = SMAIndicator(close, window=window_200).sma_indicator().iloc[-1]
        
        macd_calc = MACD(close)
        macd_line = macd_calc.macd().iloc[-1]
        macd_signal = macd_calc.macd_signal().iloc[-1]
        
        bb = BollingerBands(close)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        
        is_uptrend = price > sma_50
        self.current_tech_trend = is_uptrend # Save trend state for derivative scorer
        
        if price > ema_20 > sma_50 > sma_200: trend_score = 100 
        elif price > sma_50 > sma_200: trend_score = 85         
        elif price > sma_50: trend_score = 65                   
        elif price < ema_20 < sma_50 < sma_200: trend_score = 10
        elif price < sma_50: trend_score = 30                   
        else: trend_score = 50
        
        if macd_line > macd_signal and macd_line > 0: macd_score = 95
        elif macd_line > macd_signal and macd_line < 0: macd_score = 70 
        elif macd_line < macd_signal and macd_line > 0: macd_score = 30 
        elif macd_line < macd_signal and macd_line < 0: macd_score = 10 
        else: macd_score = 50

        if is_uptrend:
            if 50 <= rsi <= 75: rsi_score = 90  
            elif rsi > 75: rsi_score = 40       
            elif rsi < 40: rsi_score = 100      
            else: rsi_score = 60
        else:
            if 30 <= rsi <= 50: rsi_score = 20  
            elif rsi < 30: rsi_score = 60       
            elif rsi > 60: rsi_score = 10       
            else: rsi_score = 40

        if is_uptrend:
            if price >= bb_high: bb_score = 85  
            elif price <= bb_low: bb_score = 95 
            else: bb_score = 70                 
        else:
            if price <= bb_low: bb_score = 15   
            elif price >= bb_high: bb_score = 25
            else: bb_score = 30                 

        final_score = (trend_score * 0.40) + (macd_score * 0.30) + (rsi_score * 0.15) + (bb_score * 0.15)
        
        meta = {
            "RSI": rsi, "SMA50": sma_50, "SMA200": sma_200, "EMA20": ema_20,
            "MACD": macd_line, "MACD_Signal": macd_signal,
            "BB_High": bb_high, "BB_Low": bb_low, "Price": price, "Trend": is_uptrend
        }
        return final_score, meta

    def calculate_social(self, social_data):
        if "error" in social_data: return 50, {"summary": f"⚠️ ERROR: {social_data['error']}", "details": [], "counts": {"bull":0,"bear":0,"neut":0}}
        headlines = social_data.get('headlines', [])
        if not headlines: return 50, {"summary": "No relevant news found.", "details": [], "counts": {"bull":0,"bear":0,"neut":0}}

        bull_pow = bear_pow = bull_cnt = bear_cnt = neut_cnt = 0
        for item in headlines:
            sentiment = item.get('sentiment', '').lower()
            score = item.get('score', 0)
            if "bullish" in sentiment: bull_pow += score; bull_cnt += 1
            elif "bearish" in sentiment: bear_pow += score; bear_cnt += 1
            else: neut_cnt += 1
        
        total_power = bull_pow + bear_pow
        final_score = 50 if total_power == 0 else (bull_pow / total_power) * 100
        
        if final_score > 60: summary = f"Bullish Bias driven by {bull_cnt} positive signals"
        elif final_score < 40: summary = f"Bearish Bias driven by {bear_cnt} negative signals"
        else: summary = "Mixed / Neutral Sentiment"
        
        return final_score, {"summary": summary, "details": headlines, "counts": {"bull": bull_cnt, "bear": bear_cnt, "neut": neut_cnt}}

    def calculate_derivative(self, data):
        if not data.get('valid'): return 50, {}
        pcr_vol = data.get('pcr_vol', 0)
        pcr_oi = data.get('pcr_oi', 0)
        short_float = data.get('short_float', 0) * 100
        short_ratio = data.get('short_ratio', 0)
        avg_iv = data.get('avg_iv', 0) * 100
        
        # --- DERIVATIVE ANCHOR: Contextualizing Short Interest ---
        if not self.current_tech_trend:
            # If in a downtrend, high short float is a warning (Risk), not a squeeze opportunity
            float_score = 15 if short_float > 10 else 50
            ratio_score = 20 if short_ratio > 5 else 50
        else:
            # If in an uptrend, high short float is a "Squeeze Watch"
            float_score = 85 if short_float < 3 else 30 if short_float > 15 else 55
            ratio_score = 95 if short_ratio > 8 and short_float > 10 else 70 if short_ratio < 3 else 35

        if pcr_oi < 0.6: oi_score = 95
        elif pcr_oi < 0.9: oi_score = 75
        elif pcr_oi > 1.2: oi_score = 25
        else: oi_score = 50

        if pcr_vol < 0.7: vol_score = 85
        elif pcr_vol > 1.1: vol_score = 35
        else: vol_score = 50

        final_score = (oi_score * 0.40) + (vol_score * 0.20) + (float_score * 0.20) + (ratio_score * 0.20)
        return final_score, {"pcr_vol": pcr_vol, "pcr_oi": pcr_oi, "short_float": short_float, "short_ratio": short_ratio, "avg_iv": avg_iv}

    def calculate_fundamental(self, info):
        if not info: return 50, {}

        sector = info.get('sector', 'Unknown')
        pe = info.get('trailingPE')
        pb = info.get('priceToBook')
        roe = info.get('returnOnEquity')
        debt_eq = info.get('debtToEquity') 
        rev_growth = info.get('revenueGrowth')
        margins = info.get('profitMargins')
        
        insider_buys = info.get('insider_buys', 0)
        insider_sells = info.get('insider_sells', 0)

        # --- DISTRESS DETECTION LOGIC ---
        is_distressed = False
        if (roe is not None and roe < 0) or (margins is not None and margins < 0):
            is_distressed = True

        slack = 1.5 if sector in ['Technology', 'Communication Services', 'Healthcare'] else 0.8 if sector in ['Utilities', 'Financial Services'] else 1.0

        val_score = 50
        if pe is not None:
            adj_pe = pe / slack
            if adj_pe < 15: val_score = 100
            elif adj_pe < 25: val_score = 85
            elif adj_pe < 38: val_score = 70     
            elif adj_pe < 55: val_score = 45
            else: val_score = 25             
            
        if pb is not None:
            if is_distressed and pb < 1.0:
                val_score = 5  # VALUE TRAP PENALTY: Cheap P/B on a failing company is bad
            elif pb > 10: 
                val_score = max(5, val_score - 20)

        prof_score = 50
        if roe is not None:
            if roe > 0.50: prof_score = 100  
            elif roe > 0.25: prof_score = 85
            elif roe > 0: prof_score = 50
            else: prof_score = 20
            
        if margins is not None and margins > 0.25: 
            prof_score = min(100, prof_score + 15) 
            
        if is_distressed:
            prof_score = 10 # Massive penalty for structural unprofitability

        growth_score = 50
        if rev_growth is not None:
            if rev_growth >= 0.30: growth_score = 90  
            elif rev_growth >= 0.10: growth_score = 70  
            elif rev_growth < 0: growth_score = 10 # Penalty for shrinking business
            else: growth_score = 50                     

        health_score = 50
        if debt_eq is not None:
            if debt_eq < 40: health_score = 90
            elif debt_eq < 100: health_score = 75
            elif debt_eq > 200: health_score = 30
            else: health_score = 50

        final_score = (val_score * 0.10) + (prof_score * 0.35) + (growth_score * 0.40) + (health_score * 0.15)

        # Dynamic Booster
        booster = min(insider_buys * 1.5, 10)
        if is_distressed and insider_sells > 20:
            booster = 0 # Strip booster if the company is dying and insiders are dumping

        meta = {
            **info,
            "PE": pe, "PB": pb, "ROE": roe, 
            "DebtEq": debt_eq, "RevGrowth": rev_growth, "Margins": margins,
            "insider_buys": insider_buys, "insider_sells": insider_sells, 
            "insider_booster": booster, "is_distressed": is_distressed, "valuation_slack": slack
        }
        return final_score, meta