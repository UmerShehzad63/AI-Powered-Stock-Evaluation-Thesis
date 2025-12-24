import yfinance as yf
import finnhub
import pandas as pd
import random

class DataLoader:
    def __init__(self, finnhub_key=None):
        self.finnhub_client = finnhub.Client(api_key=finnhub_key) if finnhub_key else None

    def get_technical_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            return df
        except:
            return pd.DataFrame()

    def get_fundamental_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            return stock.info
        except:
            return {}

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

            options_dates = stock.options
            if options_dates:
                chain = stock.option_chain(options_dates[0])
                calls_vol = chain.calls['volume'].sum()
                puts_vol = chain.puts['volume'].sum()
                pcr = puts_vol / calls_vol if calls_vol > 0 else 0
            else:
                pcr = 0

            return {
                "short_float": short_float,
                "pcr": pcr,
                "valid": True
            }
        except:
            return {"valid": False}

    def get_social_sentiment(self, ticker):
        data = None
        source = "Mock"

        if self.finnhub_client:
            try:
                data = self.finnhub_client.stock_social_sentiment(ticker)
                source = "Real API"
            except:
                data = None 

        if not data:
            random.seed(ticker)
            data = {
                'reddit': [{
                    'score': random.uniform(-0.15, 0.15), 
                    'mention': random.randint(50, 150)
                }],
                'twitter': [{
                    'score': random.uniform(-0.10, 0.10),
                    'mention': random.randint(100, 300)
                }]
            }
            source = "Mock (Demo)"

        return data, source