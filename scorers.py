from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

class ScoringEngine:
    
    def calculate_technical(self, df):
        if df.empty or len(df) < 50: return 50, {}
        window = min(50, len(df))
        rsi = RSIIndicator(df['Close']).rsi().iloc[-1]
        sma = SMAIndicator(df['Close'], window=window).sma_indicator().iloc[-1]
        price = df['Close'].iloc[-1]
        
        rsi_score = 50
        if rsi < 30: rsi_score = 80
        elif rsi > 70: rsi_score = 30
        
        trend_score = 75 if price > sma else 30
        final = (trend_score * 0.6) + (rsi_score * 0.4)
        return final, {"RSI": rsi, "SMA": sma}

    def calculate_social(self, social_data):
        headlines = social_data.get('headlines', [])
        if not headlines:
            return 50, {"summary": "No relevant news", "details": [], "counts": {"bull":0,"bear":0,"neut":0}}

        bull_pow = 0
        bear_pow = 0
        
        bull_cnt = 0
        bear_cnt = 0
        neut_cnt = 0

        for item in headlines:
            sentiment = item.get('sentiment', '').lower()
            score = item.get('score', 0)
            
            if "bullish" in sentiment:
                bull_pow += score
                bull_cnt += 1
            elif "bearish" in sentiment:
                bear_pow += score
                bear_cnt += 1
            else:
                neut_cnt += 1
        
        total_power = bull_pow + bear_pow
        if total_power == 0:
            final_score = 50
        else:
            final_score = (bull_pow / total_power) * 100

        if final_score > 60: summary = f"Bullish Bias driven by {bull_cnt} positive signals"
        elif final_score < 40: summary = f"Bearish Bias driven by {bear_cnt} negative signals"
        else: summary = "Mixed / Neutral Sentiment"

        return final_score, {
            "summary": summary, 
            "details": headlines,
            "counts": {"bull": bull_cnt, "bear": bear_cnt, "neut": neut_cnt}
        }

    def calculate_derivative(self, data):
        if not data.get('valid'): return 50, "No Data"
        pcr = data.get('pcr', 0)
        short = data.get('short_float', 0) * 100
        pcr_score = 80 if pcr < 0.7 else 40
        short_score = 70 if short < 5 else 30
        return (pcr_score * 0.6) + (short_score * 0.4), f"PCR: {pcr:.2f} | Short: {short:.1f}%"

    def calculate_fundamental(self, info):
        pe = info.get('trailingPE', 0)
        score = 85 if 0 < pe < 25 else 50
        return score, f"PE Ratio: {pe:.2f}"