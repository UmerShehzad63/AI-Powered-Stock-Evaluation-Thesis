from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

class ScoringEngine:
    
    def calculate_technical(self, df):
        if df.empty or len(df) < 200: return 50, {} 

        rsi = RSIIndicator(df['Close']).rsi().iloc[-1]
        sma_50 = SMAIndicator(df['Close'], window=50).sma_indicator().iloc[-1]
        sma_200 = SMAIndicator(df['Close'], window=200).sma_indicator().iloc[-1]
        price = df['Close'].iloc[-1]

        rsi_score = 80 if 30 <= rsi <= 70 else 40
        
        if price > sma_50 > sma_200: trend_score = 90
        elif price < sma_50: trend_score = 30
        else: trend_score = 60

        final_score = (trend_score * 0.6) + (rsi_score * 0.4)
        return final_score, {"RSI": rsi, "SMA50": sma_50, "Price": price}

    def calculate_social(self, social_data):
        if not social_data: return 50, "No Data"

        reddit = social_data.get('reddit', [])
        r_score = reddit[0]['score'] if reddit else 0
        r_mentions = reddit[0]['mention'] if reddit else 0

        twitter = social_data.get('twitter', [])
        t_score = twitter[0]['score'] if twitter else 0
        t_mentions = twitter[0]['mention'] if twitter else 0

        norm_reddit = (r_score + 1) * 50
        norm_twitter = (t_score + 1) * 50
        total_mentions = r_mentions + t_mentions
        
        if total_mentions >= 100:
            final_score = (norm_reddit * 0.4) + (norm_twitter * 0.6)
        elif total_mentions >= 20:
            final_score = (norm_reddit * 0.5) + (norm_twitter * 0.5)
        else:
            final_score = 50 

        return final_score, f"Mentions: {total_mentions}"

    def calculate_derivative(self, data):
        if not data.get('valid'): return 50, "No Data"
        
        pcr = data.get('pcr', 0)
        short_float = data.get('short_float', 0) * 100 
        
        if pcr < 0.7: pcr_score = 80
        elif pcr < 1.0: pcr_score = 60
        else: pcr_score = 40 
        
        if short_float < 5: si_score = 90
        elif short_float < 15: si_score = 60
        else: si_score = 30
        
        final_score = (pcr_score * 0.6) + (si_score * 0.4)
        meta = f"PCR: {pcr:.2f} | Short Float: {short_float:.2f}%"
        return final_score, meta

    def calculate_fundamental(self, info):
        pe = info.get('trailingPE', 0)
        
        if 15 <= pe <= 25: score = 90
        elif pe < 5 or pe > 40: score = 30
        else: score = 60
        return score, pe